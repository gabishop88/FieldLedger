from fastapi.testclient import TestClient
from pydantic import EmailStr
from sqlmodel import Session

from app.api.models import UserCreate
from app.core.config import settings
from app.db import crud
from tests.utils.rng import generate_email, generate_str


def get_auth_headers(client: TestClient, email: EmailStr, pwd: str) -> dict[str, str]:
    data = {"username": email, "password": pwd}
    res = client.post(f"{settings.API_PREFIX}/account/login/access-token", data=data)
    assert res.status_code == 200
    token = res.json()
    assert "access_token" in token
    return {"Authorization": f"{token['token_type']} {token['access_token']}"}


def random_user_headers(
    client: TestClient, db: Session, seed: int, is_superuser: bool = False
) -> dict[str, str]:
    """Generate a random user, insert with `db` and then return the auth headers.
    User info not provided, but can be recreated with `generate_email`/`generate_str`
    from `tests.utils.rng`.

    Email is `generate_email(seed)`, password and full_name are `generate_str(seed)`
    (which is also the same as the first section of the email, before '@').
    """
    email = generate_email(seed)
    pwd = generate_str(seed)
    if crud.user.get_by_email(db, email) is None:
        user_data = UserCreate(
            email=email, password=pwd, full_name=pwd, is_superuser=is_superuser
        )
        crud.user.create(db, user_data)
    return get_auth_headers(client, email, pwd)
