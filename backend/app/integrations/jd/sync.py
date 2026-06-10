import logging
from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import Engine
from sqlmodel import Session, text

from app.core.enums import SYNC_ACTIVE, SyncStatus
from app.db import crud
from app.db.models import JDLinkUpdate, JDRecordLink
from app.integrations.jd.models import JDOrg
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


# def validate_sync_tree(client: JDClient) -> None:
#     """Go through the existing sync tree and make sure everything is up-to-date."""
#     assert client.has_token()
#     db, user_id = client.db, client.conn.user_id
#     for org_link in crud.jd_link.get_trees_paginated(db, user_id, 0, None).data:
#         if org_link.table_name != "org":
#             org_link.status = SyncStatus.ERROR
#             continue

#         # TODO: For each of these, check data and status are both correct

#         # TODO: Get org info to verify the data is up-to-date and matches org in db
#         for org_child in org_link.children:
#             if org_child.table_name == "farm":
#                 # TODO: Get farm info to verify the data in link and db
#                 for field_link in org_child.children:
#                     if field_link.table_name != "field":
#                         field_link.status = SyncStatus.ERROR
#                         continue
#                     # TODO: Get field info to verify data in link and db
#                     for field_child in field_link.children:
#                         if field_child.table_name == "field_boundary":
#                             # TODO: Validate boundary
#                             pass
#                         elif field_child.table_name == "field_op":
#                             # TODO: Validate Operation
#                             pass
#                         else:
#                             field_child.status = SyncStatus.ERROR
#                             continue
#             elif org_child.table_name == "equipment":
#                 # TODO: Validate equipment
#                 pass
#             elif org_child.table_name == "product":
#                 # TODO: Validate Product
#                 pass
#             else:
#                 org_child.status = SyncStatus.ERROR
#                 continue


async def discover_orgs(ctx, user_id: UUID, member_only=True) -> None:
    log.info(f"Discovering orgs for {user_id=}")
    with user_session(ctx["engine"], user_id) as db:
        client = JDClient.from_user(db, user_id)
        for org in await client.orgs(member_only):
            filters = [
                JDRecordLink.user_id == user_id,
                JDRecordLink.link == org.self_link.uri,
            ]
            existing = crud.jd_link.get_paginated(db, 0, None, *filters)
            if existing.count:  # NOTE: if a link exists, just leave it be.
                continue

            crud.jd_link.create(db, JDRecordLink(
                link=org.self_link.uri,
                data=org.model_dump(exclude_unset=True),
                status=SyncStatus.NORG if org.conn_link else SyncStatus.NOSYNC,
                persistent=False,
                table_name="org",
                table_key=None,
                parent_id=None,
                user_id=user_id,
            ))


# TODO: Should I have a function that lets you refresh? Maybe update with empty data?
# at the least it should double check orgs for CONFLICT, and check NORG for conn_link
# If the status is dirty for some reason, run the update

# TODO: make sure update does not wipe FLAG status

async def unsync_link(db: Session, link: JDRecordLink): ...

async def sync_link(db: Session, link: JDRecordLink): ...

async def pause_link(db: Session, link: JDRecordLink): ...

# TODO: List the valid/invalid transition options (manual changes)
#   SYNC -> DIRTY: Valid, make DIRTY, dispatch refresh (which marks SYNC)
#   SYNC -> PAUSE: Valid, intended, just set PAUSE
#   SYNC -> FLAG: Valid, just set FLAG, will proceed as if SYNC
#   SYNC -> NOSYNC: Valid, intended
#   DIRTY -> SYNC: ?? I think I should just run the update and allow it
#   DIRTY -> PAUSE: fine, same as SYNC -> PAUSE

#   DIRTY -> FLAG: ?? Not sure what to do here, probably run update then set to FLAG
#   DIRTY -> NOSYNC: Fine, same as SYNC -> NOSYNC
#   PAUSE -> SYNC: Intended, update and set to SYNC (same as DIRTY)
#   PAUSE -> DIRTY: same as -> SYNC, mark dirty, dispatch update which should set SYNC
#   PAUSE -> FLAG: ?? this one is hard because I don't know if I should resume updates, probably
#   PAUSE -> NOSYNC: Fine, same as SYNC -> NOSYNC
#   FLAG -> SYNC: intended, set to sync no other changes
#   FLAG -> DIRTY: set to dirty, dispatch update
#   FLAG -> PAUSE: fine, same as SYNC -> PAUSE
#   FLAG -> NOSYNC: fine, same as SYNC -> NOSYNC
#   NOSYNC -> SYNC: fine, dispatch update
#   NOSYNC -> DIRTY: set DIRTY, dispatch update
#   NOSYNC -> PAUSE: hmmm, maybe dispatch update then pause?
#   NOSYNC -> FLAG: dispatch update then set FLAG
#   NORG -> Anything: check conn_link, do nothing or treat like NOSYNC
#   CONFLICT -> Anything: check conflict, do notthing or treat like NOSYNC

# Rules 1. cannot update from anything to NORG or CONFLICT
#       2. NORG | CONFLICT to Anything, check condition then skip or treat like NOSYNC
#       3. SYNC_ACTIVE to NOSYNC acts the same
#       4. anything to DIRTY, set DIRTY then dispatch update
#       5. NOSYNC or DIRTY to active update then set status to whatever was requested.
async def change_status(db: Session, link: JDRecordLink, to_status: SyncStatus) -> None:
    client = JDClient(db, link.connection)
    from_status = link.status
    if from_status == to_status:
        return

    match (from_status, to_status):
        case (_, SyncStatus.NORG | SyncStatus.CONFLICT):
            return  # Invalid change # TODO: enforce this in endpoint, too.

        case (SyncStatus.NORG, _):
            new_data = JDOrg.model_validate(await client.get(link.link))
            if not new_data.conn_link:  # Org is now allowed
                to_confict = JDLinkUpdate(status=SyncStatus.CONFLICT)
                link = crud.jd_link.update(db, link, to_confict)
                await change_status(db, link, to_status)  # Repeat as CONFLICT in case

        case (SyncStatus.CONFLICT, _):
            # TODO: check for conflict. leave or run change_status again as NOSYNC
            pass

        case (active, SyncStatus.NOSYNC) if active in SYNC_ACTIVE:  # Remove sync
            await unsync_link(db, link)

        case (_, SyncStatus.DIRTY):
            to_dirty = JDLinkUpdate(status=SyncStatus.DIRTY)
            link = crud.jd_link.update(db, link, to_dirty)
            await sync_link(db, link)

        case (SyncStatus.NOSYNC | SyncStatus.DIRTY | SyncStatus.SYNC, active) if active in SYNC_ACTIVE:
            # TODO: better hadle DIRTY -> FLAG or PAUSE -> FLAG by calling sync_link first
            if from_status == SyncStatus.NOSYNC or to_status not in (SyncStatus.PAUSE, SyncStatus.FLAG):
                await sync_link(db, link)
            update = JDLinkUpdate(status=to_status)
            link = crud.jd_link.update(db, link, update)

        # TODO: handle DIRTY -> FLAG
        # TODO: handle PAUSE -> FLAG
        # TODO: handle FLAG -> SYNC (remove flag) by just changing status
        # TODO: handle FLAG -> PAUSE by just setting pause
        # TODO: add pause and Flag to case above?


async def modify_sync(ctx, user_id: UUID, link: str, updates: dict) -> None:
    with user_session(ctx["engine"], user_id) as db:
        # TODO: Strip base from url when creating ResourceLink?
        db_link = crud.jd_link.get_by_link(db, user_id, link)
        if not db_link:  # NOTE: should not happen due to check in endpoint.
            raise ValueError(f"Cannot modify unknown resource: {link=}")

        link_updates = JDLinkUpdate.model_validate(updates)
        if link_updates.status is not None:
            await change_status(db, db_link, link_updates.status)

        crud.jd_link.update(db, db_link, link_updates)


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
