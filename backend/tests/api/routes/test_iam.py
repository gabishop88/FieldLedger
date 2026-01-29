import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.messages import ExeMsg
from app.core import security
from app.core.config import settings
from app.db import crud
from app.db.models import AppUser, UserCreate, UserUpdate
from tests.utils.auth import get_auth_headers
from tests.utils.rng import generate_email, generate_str

# TODO: test an expired token? How?
PFIX = settings.API_PREFIX

# --------------------------------- User / Login Tests ---------------------------------
# Many use `seed + x` to update values, if you want different values, add an offset.
# NOTE: Remember that using the user_headers fixture will create user with the seed.


def test_superuser_login(cli: TestClient, db: Session) -> None:
    form = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    res = cli.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 200
    assert "access_token" in res.json()

    suser = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert suser
    assert security.decode_token(res.json()["access_token"]) == str(suser.id)


def test_fail_superuser_login(cli: TestClient) -> None:
    form = {"username": "not@an.email", "password": "Incorrect"}
    res = cli.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF.format("Email", "not@an.email")

    form["username"] = settings.FIRST_SUPERUSER
    res = cli.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_PWD


def test_register_user(cli: TestClient, db: Session, seed) -> None:
    user_in = UserCreate(email=generate_email(seed), password=generate_str(seed))
    res = cli.post(f"{PFIX}/account", json=user_in.model_dump())
    assert res.status_code == 200

    user_res = res.json()
    assert "id" in user_res
    assert user_res["email"] == user_in.email
    assert user_res["full_name"] == user_in.full_name
    assert user_res["is_superuser"] is False

    user_db = db.get(AppUser, user_res["id"])
    assert user_db
    assert user_db.email == user_in.email
    assert user_db.full_name == user_in.full_name
    assert security.verify_password(user_in.password, user_db.hashed_password)


def test_fail_register_duplicate_user(cli: TestClient, db: Session, seed) -> None:
    user_in = UserCreate(email=generate_email(seed), password=generate_str(seed))
    crud.user.create(db, user_in)

    res = cli.post(f"{PFIX}/account", json=user_in.model_dump())
    assert res.status_code == 409
    assert res.json()["detail"] == ExeMsg.KEY_EXISTS.format("email", user_in.email)


def test_user_login(cli: TestClient, db: Session, seed) -> None:
    user_in = UserCreate(email=generate_email(seed), password=generate_str(seed))
    login_data = {"username": user_in.email, "password": user_in.password}
    user = crud.user.create(db, user_in)

    res = cli.post(f"{PFIX}/account/login/access-token", data=login_data)
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert security.decode_token(res.json()["access_token"]) == str(user.id)


def test_user_update(cli: TestClient, db: Session, seed, user_head) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    edits = UserUpdate(
        email=generate_email(seed + 1),
        password=generate_str(seed + 1),
        full_name=generate_str(seed + 1),
    )
    assert edits.password and user

    res = cli.patch(f"{PFIX}/account", json=edits.model_dump(), headers=user_head)
    assert res.status_code == 200
    new_info = res.json()
    assert new_info["email"] == edits.email
    assert new_info["full_name"] == edits.full_name
    assert new_info["id"] == str(user.id)

    db.refresh(user)
    assert security.verify_password(edits.password, user.hashed_password)


def test_fail_user_elevate_self(cli: TestClient, db: Session, seed, user_head) -> None:
    """### Make sure a user can't bypass the superuser check and elevate themself."""
    user = crud.user.get_by_email(db, generate_email(seed))
    edits = UserUpdate(is_superuser=True).model_dump(exclude_unset=True)
    assert user

    res = cli.patch(f"{PFIX}/account", json=edits, headers=user_head)
    assert res.status_code == 200  # This doesn't fail, it just ignores is_superuser.
    assert res.json()["is_superuser"] is False

    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_email(cli: TestClient, user_head) -> None:
    edits = UserUpdate(email=settings.FIRST_SUPERUSER).model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/account", json=edits, headers=user_head)
    assert res.status_code == 409
    assert res.json()["detail"] == ExeMsg.KEY_EXISTS.format("email", edits["email"])


def test_get_user(cli: TestClient, db: Session, seed, user_head) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    assert user

    res = cli.get(f"{PFIX}/account", headers=user_head)
    user_info = res.json()
    assert user_info["email"] == user.email
    assert user_info["full_name"] == user.full_name
    assert user_info["id"] == str(user.id)
    assert user_info["is_superuser"] == user.is_superuser


def test_superuser_update_other(cli: TestClient, db: Session, seed, su_head) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    edits = UserUpdate(
        email=generate_email(seed + 2),
        password=generate_str(seed + 2),
        full_name=generate_str(seed + 2),
        is_superuser=True,
    ).model_dump()
    assert user

    res = cli.patch(f"{PFIX}/account/{user.id}", json=edits, headers=su_head)
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["email"] == edits["email"]
    assert user_info["is_superuser"] is True
    assert user_info["full_name"] == user.full_name
    assert user_info["id"] == str(user.id)

    db.refresh(user)
    assert user.is_superuser is True
    assert security.verify_password(edits["password"], user.hashed_password)

    # Reset is_superuser to revoke priveleges for the future.
    edits = UserUpdate(is_superuser=False).model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/account/{user.id}", json=edits, headers=su_head)
    assert res.status_code == 200
    assert res.json()["is_superuser"] is False
    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_nonexistant(cli: TestClient, su_head) -> None:
    edits = UserUpdate(full_name="NOTANAME").model_dump(exclude_unset=True)
    id = uuid.uuid4()
    res = cli.patch(f"{PFIX}/account/{id}", json=edits, headers=su_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF.format("AppUser", id)


def test_fail_user_update_other(cli: TestClient, db: Session, seed, user_head) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user and crud.user.get_by_email(db, generate_email(seed))

    edits = UserUpdate(full_name=generate_str(seed + 1)).model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/account/{user.id}", json=edits, headers=user_head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_PRIV


def test_search_users(cli: TestClient, db: Session, seed, user_head) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    assert user

    query: dict[str, str] = {}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_EMPTY_SEARCH

    # Search for id
    query = {"id": str(user.id)}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for email
    query = {"email": generate_email(seed)}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name
    query = {"name": generate_str(seed)}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name, but have an almost match (remove last three characters)
    query = {"name": generate_str(seed)[:-3]}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for an email that doesn't exist
    assert crud.user.get_by_email(db, generate_email(seed + 1)) is None
    query = {"email": generate_email(seed + 1)}
    res = cli.get(f"{PFIX}/account/search", params=query, headers=user_head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 0
    assert res.json()["data"] == []


def test_fail_user_delete_su(cli: TestClient, db: Session, seed, user_head) -> None:
    su = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert su and crud.user.get_by_email(db, generate_email(seed)) is not None

    res = cli.delete(f"{PFIX}/account/{su.id}", headers=user_head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_PRIV


def test_user_delete_self(cli: TestClient, db: Session, seed, user_head) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    assert user is not None, "Test user should exist."

    res = cli.delete(f"{PFIX}/account", headers=user_head)
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["id"] == str(user.id)

    assert crud.user.get_by_email(db, generate_email(seed)) is None


def test_fail_first_superuser_delete_self(cli: TestClient, db: Session) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user
    head = get_auth_headers(cli, user.email, settings.FIRST_SUPERUSER_PASSWORD)

    res = cli.delete(f"{PFIX}/account/{user.id}", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_REM_1SU

    res = cli.delete(f"{PFIX}/account", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_DEL_1SU

    # TODO: Test other superuser deletes another, fails to delete FIRST, deletes self.


def test_superuser_delete_user(cli: TestClient, db: Session, seed, su_head) -> None:
    user_in = UserCreate(email=generate_email(seed + 3), password=generate_str(seed))
    user = crud.user.create(db, user_in)

    res = cli.delete(f"{PFIX}/account/{user.id}", headers=su_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(user.id)

    assert crud.user.get_by_email(db, generate_email(seed + 3)) is None


def test_fail_superuser_delete_nonexist(cli: TestClient, su_head) -> None:
    id = uuid.uuid4()
    res = cli.delete(f"{PFIX}/account/{id}", headers=su_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF.format("AppUser", id)
