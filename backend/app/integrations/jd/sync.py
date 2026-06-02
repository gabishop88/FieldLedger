# from sqlmodel import select
# from app.core.enums import SyncStatus
# from app.db.connection import SessionLocal
# from app.db.models import JDConnection, JDRecordLink
import logging
from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import Engine
from sqlmodel import Session, text

from app.db import crud
from app.db.models import JDConnection

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# NOTE: Is the clientKey even helpful here? is it unique to a webhook? How do I know what clientKey to use?
# NOTE: Register webhook: https://developer.deere.com/dev-docs/webhook#/eventSubscriptions/post:~:text=3.-,SUBSCRIBE%20TO%20AN%20EVENT,-3.1%20Use


@contextmanager
def user_session(engine: Engine, user_id: UUID) -> Generator[Session]:
    with Session(engine) as db:
        try:
            db.exec(text(f"SET SESSION \"app.current_user\"= '{user_id}'"))  # type: ignore
            yield db
            db.commit()
        except:
            db.rollback()
            raise


def maintain_connection() -> None:
    # TODO: Check Authorization header
    # TODO: Verify connection is active
    pass


# TODO: Validate the existance of a JDConnection record, and then make RecordLinks align
#   with current subscriptions using GET /eventSubscriptions
async def initial_sync(ctx, user_id: UUID, org_id: UUID) -> None:
    log.info(f"Initial Sync for {user_id=} {org_id=}")
    with user_session(ctx["engine"], user_id) as db:
        conn = db.get(JDConnection, org_id)
        if not conn:
            crud.jd_connection.create(db, JDConnection(user_id=user_id, org_id=org_id))

        # TODO: Get the farms and fields from JD APIs
        # TODO: Check to see if there are already record links to those farms/fields
        # TODO: If there are not, then check for or create matching records and create links
        # NOTE: It is much harder to match to fieldOperations, but I can do the same for boundaries
        # NOTE: record in my db should be persistent if there is any data that relies on it in my db that is not from sync
        # 
    # TODO: Build sync tree
    # TODO: Create all JDRecordLink records
    # TODO: connect existing records where possible


# NOTE: event has clientKey, eventTypeId, targetResource, token (if given), metadata, links
async def handle_webhook_event(ctx, user_id: UUID, event: dict) -> None:
    with user_session(ctx["engine"], user_id) as db:
        event_type = event.get("eventTypeId")
        target_resource = event.get("targetResource")
        match event_type:
            case "heartbeat":
                log.info("[Webhook Event] Ba-dum <3")
            case "subscriptionVerification":
                log.info(f"[Webhook Event] Subscription Verified, {target_resource=}")
            case "fieldOperation":
                log.info("[Webhook Event] Update to Field Operations")
            case "farm":
                log.info("[Webhook Event] Update to Farm")
            case "field":
                log.info("[Webhook Event] Update to Field")
            case "boundary":
                log.info("[Webhook Event] Update to Field Boundary")
            case _:
                log.info(f"[Webhook Event] Cannot Handle {event_type=}")
