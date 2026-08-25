import logging
import re
from typing import cast

from pydantic import PostgresDsn
from sqlalchemy import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlmodel import Session, create_engine, inspect, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings

MAX_TRIES = 60 * 5
WAIT_SECONDS = 1
PASCALIZER = re.compile(r"(^|_)([a-z])")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine(uri: PostgresDsn = settings.API_DATABASE_URI) -> Engine:
    return create_engine(str(uri))


def snake_to_pascal(s: str) -> str:
    """Transform a string to PascalCase. Designed to work with snake_case inputs."""
    return PASCALIZER.sub(lambda m: m.group(2).upper(), s)


def list_tables(*schemas: str, all: bool = False, pascal: bool = False) -> list[str]:
    """### Provide schema names and get a list of the table names across them.
    `all=True` gets all tablenames across all schemas (ignores `schemas`)
    `pascal=True` returns them in PascalCase rather than snake_case (default)
    """
    with Session(get_engine(settings.READONLY_DATABASE_URI)) as db:
        insp = cast(Inspector, inspect(db.bind))
        schema_list = insp.get_schema_names() if all else schemas
        tables = [t for sch in schema_list for t in insp.get_table_names(sch)]
    return list(map(snake_to_pascal, tables)) if pascal else tables


@retry(
    stop=stop_after_attempt(MAX_TRIES),
    wait=wait_fixed(WAIT_SECONDS),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN)
)
def test_connection(eng: Engine) -> None:
    try:
        with Session(eng) as session:
            session.exec(select(1))
    except Exception as e:
        logging.error(e)
        raise e
