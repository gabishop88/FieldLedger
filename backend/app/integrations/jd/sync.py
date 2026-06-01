# from sqlmodel import select
# from app.core.enums import SyncStatus
# from app.db.connection import SessionLocal
# from app.db.models import JDConnection, JDRecordLink
import logging
from uuid import UUID

from sqlmodel import Session

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def initial_sync(db: Session, org_id: UUID) -> None:
    log.info(f"Initial Sync for {org_id=}")
    # TODO: create JDConnection record
    # TODO: Build sync tree
    # TODO: Create all JDRecordLink records
    # TODO: connect existing records where possible



async def handle_webhook_event(payload: dict) -> None:
    event_type = payload.get("eventType")
    log.info(f"[Unimplemented] Handle {payload}")
    match event_type:
        case _:  # TODO: Log and handle webhook callback event
            return
