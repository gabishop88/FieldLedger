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
from app.db.connection import get_engine
from app.db.models import AppUser
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    """Get a database session. DO NOT call `db.commit()`."""
    with Session(get_engine()) as session:
        try:
            yield session
        finally:
            session.rollback()


@pytest.fixture(scope="module")
def client(db: Session) -> Generator[TestClient, None, None]:
    # FIXME: Without dep overrides, the client uses actual dep sessions (test data is saved and changes made directly by the db in the test function are not available to the client)
    # However, with these dep overrides, I am getting stale data error. One possibility is the session.close in CurrentUser (deps.py) might be closing the session since I override both with the same generator. Possible solution is to make a second geneator fixture for that purpose? or override the CurrentUser dep?
    def test_session_override():
        yield db

    def current_user_override(db: ReadSession, token: AccessToken) -> AppUser:
        key = security.decode_token(token)
        if key is None:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Could not validate credentials"
            )
        user = db.get(AppUser, key)
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
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
