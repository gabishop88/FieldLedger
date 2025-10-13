from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import get_engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    """ Get a database session. DO NOT call `db.commit()`."""
    with Session(get_engine()) as session:
        yield session
        session.rollback()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as cli:
        yield cli
