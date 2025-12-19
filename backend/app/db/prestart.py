import logging
import os
import subprocess
from pathlib import Path

import alembic.config
from sqlmodel import Session, select

# NOTE: Avoided `from app.db import crud` because crud.ref relies on db being set up.
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.backup import get_revision
from app.db.connection import get_engine, test_connection
from app.db.models import AppUser, UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.db.prestart")


def restore_backup(backup_fp: Path) -> None:
    db_uri = str(settings.ADMIN_DATABASE_URI).replace("+psycopg", "")
    cmd = ["pg_restore", "-va", "-d", db_uri, "-N", "public", backup_fp]
    logger.info(f"Applying backup file: {backup_fp}")

    env = os.environ.copy()
    env["PGOPTIONS"] = "-c audit.skip_changelog=on"
    subprocess.check_call(cmd, env=env)


def find_backup() -> Path | None:
    if settings.POSTGRES_BACKUP_DIR is None:
        logger.warning("Cannot restore backup data: No backup dir in .env")
        return None

    backup_dir = Path(settings.POSTGRES_BACKUP_DIR)
    if not backup_dir.exists():
        logger.warning(f"Cannot restore backup data: Backup dir missing: {backup_dir}")
        return None

    backups = sorted(backup_dir.glob(f"{get_revision()}_*.dump"), reverse=True)
    if not backups:
        logger.warning("Cannot restore backup data: No compatible backups found.")
        return None
    return backups[0]


def ensure_superuser_exists(db: Session) -> None:
    user = db.exec(select(AppUser).where(AppUser.email == settings.FIRST_SUPERUSER)).first()
    if not user:
        first_user_data = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        record = AppUser.model_validate(
            first_user_data,
            update={"hashed_password": get_password_hash(first_user_data.password)},
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    user = db.exec(select(AppUser).where(AppUser.email == settings.FIRST_SUPERUSER)).first()
    assert user, "First superuser could not be created."


if __name__ == "__main__":
    # When app.db.prestart is run as a module:

    # Test the database connection
    engine = get_engine(settings.ADMIN_DATABASE_URI)
    test_connection(engine)
    logger.info("Database Connection Established.")

    # Run alembic migration
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    logger.info("Alembic Migration Complete.")

    with Session(engine) as db:
        if db.exec(select(AppUser).where(AppUser.email == settings.FIRST_SUPERUSER)).first() is None:
            # Restore compatible backup if exists
            backup = find_backup()
            if backup:
                restore_backup(backup)
                logger.info("Data Restoration Complete.")

            # Make sure the first superuser exists even if backup failed.
            ensure_superuser_exists(db)
            logger.info("First Superuser Exists.")
