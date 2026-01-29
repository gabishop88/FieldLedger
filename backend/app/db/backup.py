"""### Tools to create a backup of the database
You can call `make_backup(backup_dir)` to make a backup, or run one of the following:

```sh
docker compose exec backend uv run python -m app.db.backup
```
OR
```sh
uv run python -m app.db.backup
```
"""
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import settings


def get_revision() -> str:
    result = subprocess.run(["alembic", "current"], capture_output=True, text=True)
    return result.stdout.split(" ")[0].strip()


def get_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S").strip()


def make_backup(dir: Path) -> None:
    fp = dir.joinpath(f"{get_revision()}_{get_timestamp()}_{settings.POSTGRES_DB}.dump")
    db_url = str(settings.ADMIN_DATABASE_URI).replace("+psycopg", "")
    cmd = ["pg_dump", "-Fc", "--data-only", db_url, "-f", fp]
    subprocess.check_call(cmd)


if __name__ == "__main__":
    if settings.POSTGRES_BACKUP_DIR is not None:
        make_backup(Path(settings.POSTGRES_BACKUP_DIR))
