import random
from collections.abc import Generator

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.deps import (
    AccessToken,
    ReadSession,
    get_current_user,
    read_session,
    write_session,
)
from app.core import security
from app.core.enums import ErrMsg
from app.db.connection import get_engine
from app.db.models import AppUser
from app.main import app
from tests.utils.auth import random_user_headers


@pytest.fixture(scope="function", autouse=True)
def db() -> Generator[Session, None, None]:
    """Get a database session. DO NOT call `db.commit()`."""
    with Session(get_engine()) as session:
        try:
            # TODO: Set "app.current_user" for tests? What would I even set it to?
            yield session
        finally:
            session.rollback()


@pytest.fixture(scope="function")
def cli(db: Session) -> Generator[TestClient, None, None]:
    def test_session_override():
        yield db

    def current_user_override(db: ReadSession, token: AccessToken) -> AppUser:
        key = security.decode_token(token)
        if key is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, ErrMsg.FBDN_CRED)
        user = db.get(AppUser, key)
        if not user:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("AppUser", key)
            )
        return user

    app.dependency_overrides[read_session] = test_session_override
    app.dependency_overrides[write_session] = test_session_override
    app.dependency_overrides[get_current_user] = current_user_override

    with TestClient(app) as cli:
        yield cli

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def seed() -> int:
    """Gives the same random number across all tests in the model."""
    return random.randint(0, 2**16 - 1)  # 2**16: random enough, has room in int range


@pytest.fixture(scope="function")
def user_head(cli: TestClient, db: Session, seed: int) -> dict[str, str]:
    return random_user_headers(cli, db, seed)


@pytest.fixture(scope="function")
def su_head(cli: TestClient, db: Session, seed: int) -> dict[str, str]:
    return random_user_headers(cli, db, seed, is_superuser=True)
