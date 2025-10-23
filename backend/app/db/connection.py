import logging

from pydantic import PostgresDsn
from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings

MAX_TRIES = 60 * 5
WAIT_SECONDS = 1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine(uri: PostgresDsn = settings.API_DATABASE_URI) -> Engine:
    return create_engine(str(uri))


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
