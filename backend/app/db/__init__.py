import logging

from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5
wait_seconds = 1

engine = create_engine(str(settings.API_DATABASE_URI))
ro_engine = create_engine(str(settings.READONLY_DATABASE_URI))


# TODO: Add any inital data steps

@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN)
)
def init(eng: Engine) -> None:
    try:
        with Session(eng) as session:
            session.exec(select(1))
    except Exception as e:
        logger.error(e)
        raise e


if __name__ == "__main__":
    init(engine)
