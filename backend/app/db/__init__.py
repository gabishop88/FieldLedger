import logging

import alembic.config
from pydantic import PostgresDsn
from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.db import crud
from app.db.models import AppUser, UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5
wait_seconds = 1


def get_engine(uri: PostgresDsn = settings.API_DATABASE_URI):
    return create_engine(str(uri))


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def test_connection(eng: Engine) -> None:
    try:
        with Session(eng) as session:
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


def initial_data(db: Session) -> None:
    user = db.exec(
        select(AppUser).where(AppUser.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        first_user_data = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        crud.user.create(db, first_user_data)


if __name__ == "__main__":
    engine = get_engine()
    test_connection(engine)
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    with Session(engine) as db:
        initial_data(db)
