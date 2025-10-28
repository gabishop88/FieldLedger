import logging
import subprocess
from pathlib import Path

import alembic.config
from sqlmodel import Session

from app.core.config import settings
from app.db import crud
from app.db.backup import get_revision
from app.db.connection import get_engine, test_connection
from app.db.models import UserCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.db.prestart")


def restore_backup(backup_fp: Path) -> None:
    pg_url = str(settings.ADMIN_DATABASE_URI).replace("+psycopg", "")
    cmd = ["pg_restore", "-c", "-d", pg_url, backup_fp]
    logger.info(f"Applying backup file: {backup_fp}")
    subprocess.check_call(cmd)


def find_backup() -> Path | None:
    if settings.POSTGRES_BACKUP_DIR is None:
        logger.info("Cannot restore backup data: No backup dir in .env")
        return None

    backup_dir = Path(settings.POSTGRES_BACKUP_DIR)
    if not backup_dir.exists():
        logger.info(f"Cannot restore backup data: Backup dir missing: {backup_dir}")
        return None

    backups = sorted(backup_dir.glob(f"{get_revision()}_*.dump"), reverse=True)
    if not backups:
        logger.info("Cannot restore backup data: No compatible backups found.")
        return None
    return backups[0]


def ensure_superuser_exists(db: Session) -> None:
    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    if not user:
        first_user_data = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        crud.user.create(db, first_user_data)
        db.commit()

    user = crud.user.get_by_email(db, settings.FIRST_SUPERUSER)
    assert user, "First superuser could not be created."


if __name__ == "__main__":
    # Test the database connection
    engine = get_engine(settings.ADMIN_DATABASE_URI)
    test_connection(engine)
    logger.info("✅ Database Connection Established.")

    # Run alembic migration
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])
    logger.info("✅ Alembic Migration Complete.")

    with Session(engine) as db:
        if crud.user.get_by_email(db, settings.FIRST_SUPERUSER) is None:
            # Restore compatible backup if exists
            backup = find_backup()
            if backup:
                restore_backup(backup)
                logger.info("✅ Data Restoration Complete.")

            # Make sure the first superuser exists even if backup failed.
            ensure_superuser_exists(db)
            logger.info("✅ First Superuser Exists.")
