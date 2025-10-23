import pytest
from sqlmodel import Session, select

from app.core.config import settings
from app.db.connection import get_engine


@pytest.mark.parametrize(
    "uri",
    [
        settings.ADMIN_DATABASE_URI,
        settings.API_DATABASE_URI,
        settings.READONLY_DATABASE_URI,
    ],
)
def test_engine_connections(uri) -> None:
    with Session(get_engine(uri)) as session:
        session.exec(select(1))
