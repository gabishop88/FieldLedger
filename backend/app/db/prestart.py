import logging

import alembic.config
from sqlmodel import Session, select

from app.core.config import settings
from app.db import crud
from app.db.connection import get_engine, test_connection
from app.db.models import AppUser, UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.db.prestart")


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
        db.commit()

    user = db.exec(
        select(AppUser).where(AppUser.email == settings.FIRST_SUPERUSER)
    ).first()
    assert user, "First superuser could not be created."


if __name__ == "__main__":
    # Test the database connection
    engine = get_engine(settings.ADMIN_DATABASE_URI)
    test_connection(engine)
    logger.info("✅ Database connection established.")

    # Run alembic migration
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    logger.info("✅ Alembic migration complete.")

    # Make sure the first superuser exists
    with Session(engine) as db:
        initial_data(db)
    logger.info("✅ First superuser exists.")
