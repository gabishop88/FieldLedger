import random
import string
import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.db import crud
from app.db.models import AppUser, UserCreate

# TODO: test an expired token? How?

# ---------------------------------- Helper Functions ----------------------------------


def generate_str(seed: int | None = None, k: int = 16) -> str:
    rng = random.Random(seed)
    return "".join(rng.choices(string.ascii_lowercase, k=k))


def generate_email(seed: int | None = None) -> str:
    return f"{generate_str(seed)}@{generate_str(seed)}.edu"


def get_auth_headers(client: TestClient, email: str, pwd: str) -> dict[str, str]:
    data = {"username": email, "password": pwd}
    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=data)
    assert res.status_code == 200, "Test did not provide valid email/pwd."
    assert "access_token" in res.json()
    token = res.json()
    return {"Authorization": f"{token['token_type']} {token['access_token']}"}


# --------------------------------- User / Login Tests ---------------------------------
# Many of these must be run in order (rely on objects changed by previous tests)

# Use these to get random but deterministic test values by giving them the seed:
# e.g. `email_1(seed)` gives a random email, but it is the same random email everywhere it is called.
# Originally, I just called generate_x(seed + offset) to get them, but got confused. I am sure there is a better way to do this.
email_1 = lambda seed: generate_email(seed + 0)  # noqa: E731
pass_1 = lambda seed: generate_str(seed + 1)  # noqa: E731
email_2 = lambda seed: generate_email(seed + 2)  # noqa: E731
pass_2 = lambda seed: generate_str(seed + 3)  # noqa: E731
name_1 = lambda seed: generate_str(seed + 4)  # noqa: E731
email_3 = lambda seed: generate_email(seed + 5)  # noqa: E731
pass_3 = lambda seed: generate_str(seed + 6)  # noqa: E731
email_4 = lambda seed: generate_email(seed + 7)  # noqa: E731
pass_4 = lambda seed: generate_str(seed + 8)  # noqa: E731


def test_superuser_login(client: TestClient, db: Session) -> None:
    form = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=form)
    assert res.status_code == 200
    assert "access_token" in res.json()

    suser = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert suser
    assert security.decode_token(res.json()["access_token"]) == str(suser.id)


def test_fail_superuser_login(client: TestClient) -> None:
    form = {"username": "not@an.email", "password": "Incorrect"}
    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=form)
    assert res.status_code == 404
    assert "detail" in res.json()
    assert res.json()["detail"] == "Email(username) not found."

    form["username"] = settings.FIRST_SUPERUSER
    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=form)
    assert res.status_code == 400
    assert "detail" in res.json()
    assert res.json()["detail"] == "Incorrect Password."


def test_register_user(client: TestClient, db: Session, seed) -> None:
    data = {"email": email_1(seed), "password": pass_1(seed), "full_name": None}
    # TODO: Figure out why I can't use `data=data` (it formats it like params=)?
    res = client.put(f"{settings.API_PREFIX}/account", json=data)
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
    data = {"email": email_1(seed), "password": pass_1(seed)}
    assert crud.user.get_by_email(db, data["email"]) is not None, "User should exist."

    res = client.put(f"{settings.API_PREFIX}/account", json=data)
    assert res.status_code == 400
    assert res.json()["detail"] == "Email is already registered."


def test_user_login(client: TestClient, db: Session, seed) -> None:
    data = {"username": email_1(seed), "password": pass_1(seed)}
    user = crud.user.get_by_email(db, data["username"])
    assert user is not None, "Test user should exist."

    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=data)
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert security.decode_token(res.json()["access_token"]) == str(user.id)


def test_user_update(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_1(seed))
    assert user is not None, "Test user should exist."
    assert security.verify_password(pass_1(seed), user.hashed_password)
    edits = {
        "full_name": name_1(seed),
        "email": email_2(seed),
        "password": pass_2(seed),
    }

    head = get_auth_headers(client, user.email, pass_1(seed))
    res = client.patch(f"{settings.API_PREFIX}/account", json=edits, headers=head)
    assert res.status_code == 200
    new_info = res.json()
    assert new_info["email"] == edits["email"]
    assert new_info["full_name"] == edits["full_name"]
    assert new_info["id"] == str(user.id)

    db.refresh(user)
    assert security.verify_password(edits["password"], user.hashed_password)


def test_fail_user_elevate_self(client: TestClient, db: Session, seed) -> None:
    """##Make sure a user can't bypass the type checker and elevate themself.
    Normally, I wouldn't even check, but this seems like the one place it is good to be certain
    """
    user = crud.user.get_by_email(db, email_2(seed))
    assert user is not None, "Test user should exist."
    edits = {"is_superuser": "True"}

    head = get_auth_headers(client, user.email, pass_2(seed))
    res = client.patch(f"{settings.API_PREFIX}/account", json=edits, headers=head)
    assert res.status_code == 200  # TODO: Should this have a validation error?
    assert res.json()["is_superuser"] is False

    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_email_exists(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_2(seed))
    assert user is not None, "Test user should exist."
    edits = {"email": settings.FIRST_SUPERUSER}

    head = get_auth_headers(client, user.email, pass_2(seed))
    res = client.patch(f"{settings.API_PREFIX}/account", json=edits, headers=head)
    assert res.status_code == 409
    assert res.json()["detail"] == "That email is already in use."

    db.refresh(user)
    assert user.email == email_2(seed)


def test_get_user(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_2(seed))
    assert user is not None, "Test user should exist."

    head = get_auth_headers(client, user.email, pass_2(seed))
    res = client.get(f"{settings.API_PREFIX}/account", headers=head)
    user_info = res.json()
    assert user_info["email"] == user.email
    assert user_info["full_name"] == user.full_name
    assert user_info["id"] == str(user.id)
    assert user_info["is_superuser"] == user.is_superuser


def test_superuser_update_other(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_2(seed))
    assert user is not None, "Test user should exist."

    edits = {"email": email_3(seed), "password": pass_3(seed), "is_superuser": "True"}
    head = get_auth_headers(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    res = client.patch(
        f"{settings.API_PREFIX}/account/{user.id}", json=edits, headers=head
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
    edits = {"is_superuser": "False"}
    res = client.patch(
        f"{settings.API_PREFIX}/account/{user.id}", json=edits, headers=head
    )
    assert res.status_code == 200
    assert res.json()["is_superuser"] is False
    db.refresh(user)
    assert user.is_superuser is False


def test_fail_update_nonexistant(client: TestClient) -> None:
    edits = {"full_name": "NOTANAME"}
    head = get_auth_headers(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    res = client.patch(
        f"{settings.API_PREFIX}/account/{uuid.uuid4()}", json=edits, headers=head
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Could not find target user."


def test_fail_user_update_other(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None
    assert crud.user.get_by_email(db, email_3(seed)) is not None, "User should exist."

    edits = {"full_name": name_1(seed)}
    head = get_auth_headers(client, email_3(seed), pass_3(seed))
    res = client.patch(
        f"{settings.API_PREFIX}/account/{user.id}", json=edits, headers=head
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "User does not have priveleges."


def test_search_users(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_3(seed))
    assert user is not None, "Test user should exist."
    head = get_auth_headers(client, email_3(seed), pass_3(seed))

    query: dict[str, str] = {}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 400
    assert res.json()["detail"] == "Provide a search option."

    # Search for id
    query = {"id": str(user.id)}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for email
    query = {"email": email_3(seed)}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name
    query = {"name": name_1(seed)}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for name, but have an almost match (remove last three characters)
    query = {"name": name_1(seed)[:-3]}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(user.id)

    # Search for an email that doesn't exist
    assert not crud.user.get_by_email(db, email_2(seed)), "This user shouldn't exist."
    query = {"email": email_2(seed)}
    res = client.get(f"{settings.API_PREFIX}/account/search", params=query, headers=head)
    assert res.status_code == 200
    assert "count" in res.json()
    assert res.json()["count"] == 0
    assert res.json()["data"] == []


def test_fail_user_delete_superuser(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None, "Superuser should exist."
    assert crud.user.get_by_email(db, email_3(seed)) is not None, "User should exist."

    head = get_auth_headers(client, email_3(seed), pass_3(seed))
    res = client.delete(f"{settings.API_PREFIX}/account/{user.id}", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == "User does not have priveleges."


def test_user_delete_self(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_3(seed))
    assert user is not None, "Test user should exist."

    head = get_auth_headers(client, user.email, pass_3(seed))
    res = client.delete(f"{settings.API_PREFIX}/account", headers=head)
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["id"] == str(user.id)

    assert crud.user.get_by_email(db, email_3(seed)) is None, "User was not deleted."


def test_fail_first_superuser_delete_self(client: TestClient, db: Session) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user is not None, "Superuser should exist."

    head = get_auth_headers(client, user.email, settings.FIRST_SUPERUSER_PASSWORD)

    res = client.delete(f"{settings.API_PREFIX}/account/{user.id}", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == "Can't remove First Superuser."

    res = client.delete(f"{settings.API_PREFIX}/account", headers=head)
    assert res.status_code == 403
    assert res.json()["detail"] == "YOU ARE NEEDED, ADMINISTRATOR."

    # Related, but not tested: Suser deletes another, Other Suser (fails) to del FIRST


def test_superuser_delete_user(client: TestClient, db: Session, seed) -> None:
    user = crud.user.get_by_email(db, email_4(seed))
    assert user is None
    user = crud.user.create(db, UserCreate(email=email_4(seed), password=pass_4(seed)))

    head = get_auth_headers(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    res = client.delete(f"{settings.API_PREFIX}/account/{user.id}", headers=head)
    assert res.status_code == 200
    assert res.json()["id"] == str(user.id)

    assert crud.user.get_by_email(db, email_4(seed)) is None


def test_fail_superuser_delete_nonexist(client: TestClient) -> None:
    head = get_auth_headers(
        client, settings.FIRST_SUPERUSER, settings.FIRST_SUPERUSER_PASSWORD
    )
    res = client.delete(f"{settings.API_PREFIX}/account/{uuid.uuid4()}", headers=head)
    assert res.status_code == 404
    assert res.json()["detail"] == "Could not find target user."
