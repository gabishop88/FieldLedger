import logging
from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import Engine
from sqlmodel import Session, select, text

from app.core.enums import SyncStatus
from app.db import crud
from app.db.models import JDConnection, JDRecordLink
from app.integrations.jd.requests import JDClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# TODO: functions to add to worker list: modify_sync, handle_webhook_event
# TODO: add validate_sync_tree to worker functions?

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


def validate_sync_tree(client: JDClient) -> None:
    """Go through the existing sync tree and make sure everything is up-to-date."""
    assert client.refresh_check_auth()
    for org_link in client.get_org_trees(0, None):
        if org_link.table_name != "org":
            org_link.status = SyncStatus.ERROR
            continue

        # TODO: For each of these, check data and status are both correct

        # TODO: Get org info to verify the data is up-to-date and matches org in db
        for org_child in org_link.children:
            if org_child.table_name == "farm":
                # TODO: Get farm info to verify the data in link and db
                for field_link in org_child.children:
                    if field_link.table_name != "field":
                        field_link.status = SyncStatus.ERROR
                        continue
                    # TODO: Get field info to verify data in link and db
                    for field_child in field_link.children:
                        if field_child.table_name == "field_boundary":
                            # TODO: Validate boundary
                            pass
                        elif field_child.table_name == "field_op":
                            # TODO: Validate Operation
                            pass
                        else:
                            field_child.status = SyncStatus.ERROR
                            continue
            elif org_child.table_name == "equipment":
                # TODO: Validate equipment
                pass
            elif org_child.table_name == "product":
                # TODO: Validate Product
                pass
            else:
                org_child.status = SyncStatus.ERROR
                continue


async def modify_sync(ctx, user_id: UUID, resource_path: str, updates: dict) -> None:
    with user_session(ctx["engine"], user_id) as db:
        client = JDClient.from_user(db, user_id)
        assert client.refresh_check_auth()
        # TODO: Get the RecordLink at the resource_path, which should be unique
        # TODO: process the updates and ensure they are valid
        # TODO: cascade changes, e.g. add children for first sync, delete them in unsync




# # TODO: Validate the existance of a JDConnection record, and then make RecordLinks align
# #   with current subscriptions using GET /eventSubscriptions
# async def initial_sync(ctx, user_id: UUID, org_id: UUID) -> None:
#     log.info(f"Initial Sync for {user_id=} {org_id=}")
#     with user_session(ctx["engine"], user_id) as db:
#         conn_model = JDConnection(user_id=user_id)
#         conn = db.get(JDConnection, org_id) or crud.jd_connection.create(db, conn_model)
#         jd = JDClient(db, conn)

#         # TODO: Get the farms and fields from JD APIs
#         # TODO: Check to see if there are already record links to those farms/fields
#         # TODO: If there are not, then check for or create matching records and create links
#         # NOTE: It is much harder to match to fieldOperations, but I can do the same for boundaries
#         # NOTE: record in my db should be persistent if there is any data that relies on it in my db that is not from sync
#         #
#     # TODO: Build sync tree
#     # TODO: Create all JDRecordLink records
#     # TODO: connect existing records where possible


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
