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
# Many of these must be run in order (rely on objects changed by previous tests)

# Many use `seed + x` to update values, so following tests must use the seed+offset of the last update.
# I tried to keep them consistent so they aren't too hard to follow.


def test_superuser_login(client: TestClient, db: Session) -> None:
    form = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    res = client.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 200
    assert "access_token" in res.json()

    suser = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert suser
    assert security.decode_token(res.json()["access_token"]) == str(suser.id)


def test_fail_superuser_login(client: TestClient) -> None:
    form = {"username": "not@an.email", "password": "Incorrect"}
    res = client.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_EMAIL.format("not@an.email")

    form["username"] = settings.FIRST_SUPERUSER
    res = client.post(f"{PFIX}/account/login/access-token", data=form)
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_PWD


def test_register_user(client: TestClient, db: Session, seed) -> None:
    data = UserCreate(
        email=generate_email(seed), password=generate_str(seed)
    ).model_dump()
    res = client.put(f"{PFIX}/account", json=data)
    assert res.status_code == 200

    user_res = res.json()
    assert "id" in user_res
    assert user_res["email"] == data["email"]
    assert user_res["full_name"] == data["full_name"]
    assert user_res["is_superuser"] is False

    user_db = db.get(AppUser, user_res["id"])
    assert user_db
    assert user_db.email == data["email"]
    assert user_db.full_name == data["full_name"]
    assert security.verify_password(data["password"], user_db.hashed_password)


def test_fail_register_duplicate_user(client: TestClient, db: Session, seed) -> None:
    data = UserCreate(
        email=generate_email(seed), password=generate_str(seed)
    ).model_dump()
    assert crud.user.get_by_email(db, data["email"]) is not None, "User should exist."

    res = client.put(f"{PFIX}/account", json=data)
    assert res.status_code == 409
    assert res.json()["detail"] == ExeMsg.CONFLICT_EMAIL.format(data["email"])


def test_user_login(client: TestClient, db: Session, seed) -> None:
    data = {"username": generate_email(seed), "password": generate_str(seed)}
    user = crud.user.get_by_email(db, data["username"])
    assert user is not None, "Test user should exist."

    res = client.post(f"{PFIX}/account/login/access-token", data=data)
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert security.decode_token(res.json()["access_token"]) == str(user.id)


def test_user_update(client: TestClient, db: Session, seed, user_headers) -> None:
    user = crud.user.get_by_email(db, generate_email(seed))
    assert user is not None, "Test user should exist."
    assert security.verify_password(generate_str(seed), user.hashed_password)
    edits = UserUpdate(
        email=generate_email(seed + 1),
        password=generate_str(seed + 1),
        full_name=generate_str(seed + 1),
    ).model_dump()

    res = client.patch(f"{PFIX}/account", json=edits, headers=user_headers)
    assert res.status_code == 200
    new_info = res.json()
    assert new_info["email"] == edits["email"]
    assert new_info["full_name"] == edits["full_name"]
    assert new_info["id"] == str(user.id)

    db.refresh(user)
    assert security.verify_password(edits["password"], user.hashed_password)


def test_fail_user_elevate_self(
    client: TestClient, db: Session, seed, user_headers
) -> None:
    """##Make sure a user can't bypass the type checker and elevate themself.
    Normally, I wouldn't even check, but this seems like the one place it is good to be certain
    """
    user = crud.user.get_by_email(db, generate_email(seed + 1))
    assert user is not None, "Test user should exist."
    edits = UserUpdate(is_superuser=True).model_dump(exclude_unset=True)

    res = client.patch(f"{PFIX}/account", json=edits, headers=user_headers)
    assert res.status_code == 200  # TODO: Should this have a validation error?
    assert res.json()["is_superuser"] is False

    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_email_exists(
    client: TestClient, db: Session, seed, user_headers
) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 1))
    assert user is not None, "Test user should exist."
    edits = UserUpdate(email=settings.FIRST_SUPERUSER).model_dump(exclude_unset=True)

    res = client.patch(f"{PFIX}/account", json=edits, headers=user_headers)
    assert res.status_code == 409
    assert res.json()["detail"] == ExeMsg.CONFLICT_EMAIL.format(edits["email"])

    db.refresh(user)
    assert user.email == generate_email(seed + 1)


def test_get_user(client: TestClient, db: Session, seed, user_headers) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 1))
    assert user is not None, "Test user should exist."

    res = client.get(f"{PFIX}/account", headers=user_headers)
    user_info = res.json()
    assert user_info["email"] == user.email
    assert user_info["full_name"] == user.full_name
    assert user_info["id"] == str(user.id)
    assert user_info["is_superuser"] == user.is_superuser


def test_superuser_update_other(
    client: TestClient, db: Session, seed, superuser_headers
) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 1))
    assert user is not None, "Test user should exist."

    edits = UserUpdate(
        email=generate_email(seed + 2),
        password=generate_str(seed + 2),
        full_name=generate_str(seed + 2),
        is_superuser=True,
    ).model_dump()
    res = client.patch(
        f"{PFIX}/account/{user.id}", json=edits, headers=superuser_headers
    )
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
    res = client.patch(
        f"{PFIX}/account/{user.id}", json=edits, headers=superuser_headers
    )
    assert res.status_code == 200
    assert res.json()["is_superuser"] is False
    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_nonexistant(client: TestClient, superuser_headers) -> None:
    edits = UserUpdate(full_name="NOTANAME").model_dump(exclude_unset=True)
    id = uuid.uuid4()
    res = client.patch(f"{PFIX}/account/{id}", json=edits, headers=superuser_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_USER.format(id)


def test_fail_user_update_other(
    client: TestClient, db: Session, seed, user_headers
) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None
    assert crud.user.get_by_email(db, generate_email(seed + 2)), "User should exist."

    edits = UserUpdate(full_name=generate_str(seed)).model_dump(exclude_unset=True)
    res = client.patch(f"{PFIX}/account/{user.id}", json=edits, headers=user_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_PRIV


def test_search_users(client: TestClient, db: Session, seed, user_headers) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 2))
    assert user is not None, "Test user should exist."

    query: dict[str, str] = {}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_EMPTY_SEARCH

    # Search for id
    query = {"id": str(user.id)}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for email
    query = {"email": generate_email(seed + 2)}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name
    query = {"name": generate_str(seed + 2)}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name, but have an almost match (remove last three characters)
    query = {"name": generate_str(seed + 2)[:-3]}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for an email that doesn't exist
    assert not crud.user.get_by_email(db, generate_email(seed + 1)), (
        "This user shouldn't exist."
    )
    query = {"email": generate_email(seed + 1)}
    res = client.get(f"{PFIX}/account/search", params=query, headers=user_headers)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 0
    assert res.json()["data"] == []


def test_fail_user_delete_superuser(
    client: TestClient, db: Session, seed, user_headers
) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None, "Superuser should exist."
    assert crud.user.get_by_email(db, generate_email(seed + 2)) is not None, (
        "User should exist."
    )

    res = client.delete(f"{PFIX}/account/{user.id}", headers=user_headers)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_PRIV


def test_user_delete_self(client: TestClient, db: Session, seed, user_headers) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 2))
    assert user is not None, "Test user should exist."

    res = client.delete(f"{PFIX}/account", headers=user_headers)
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["id"] == str(user.id)

    assert crud.user.get_by_email(db, generate_email(seed + 2)) is None, (
        "User was not deleted."
    )


def test_fail_first_superuser_delete_self(client: TestClient, db: Session) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None, "Superuser should exist."

    head = get_auth_headers(client, user.email, settings.FIRST_SUPERUSER_PASSWORD)

    res = client.delete(f"{PFIX}/account/{user.id}", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_REM_1SU

    res = client.delete(f"{PFIX}/account", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == ExeMsg.FBDN_DEL_1SU

    # TODO: Test other superuser deletes another, fails to delete FIRST, deletes self.


def test_superuser_delete_user(
    client: TestClient, db: Session, seed, superuser_headers
) -> None:
    user = crud.user.get_by_email(db, generate_email(seed + 3))
    assert user is None
    user = crud.user.create(
        db, UserCreate(email=generate_email(seed + 3), password=generate_str(seed + 3))
    )

    res = client.delete(f"{PFIX}/account/{user.id}", headers=superuser_headers)
    assert res.status_code == 200
    assert res.json()["id"] == str(user.id)

    assert crud.user.get_by_email(db, generate_email(seed + 3)) is None


def test_fail_superuser_delete_nonexist(client: TestClient, superuser_headers) -> None:
    id = uuid.uuid4()
    res = client.delete(f"{PFIX}/account/{id}", headers=superuser_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_USER.format(id)
