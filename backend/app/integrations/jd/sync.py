import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import Engine
from sqlmodel import Session, select, text

from app.core.enums import SYNC_ACTIVE, FieldType, OrgFarmType, SyncStatus
from app.db import crud
from app.db.models import (
    Farm,
    FarmCreate,
    Field,
    JDLinkUpdate,
    JDRecordLink,
    Org,
    OrgCreate,
    OrgFarm,
    SyncLinkUpdate,
)
from app.integrations.jd.models import (
    JDBoundary,
    JDFarm,
    JDField,
    JDFieldOp,
    JDMulti,
    JDOrg,
)
from app.integrations.jd.requests import JDClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


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


async def discover_orgs(ctx, user_id: UUID, member_only=True) -> None:
    log.info(f"Discovering orgs for {user_id=}")
    with user_session(ctx["engine"], user_id) as db:
        client = JDClient.from_user(db, user_id)
        for org in await client.orgs(member_only):
            org_links = crud.jd_link.get_paginated(
                db, 0, None, JDRecordLink.uri == org.uri
            )
            existing = next((v for v in org_links.data if v.user_id == user_id), None)
            others = [v for v in org_links.data if v.user_id != user_id]
            if existing:  # NOTE: if a link exists, just leave it be.
                continue

            # Starting status
            if others and any(v.status in SYNC_ACTIVE for v in others):
                status = SyncStatus.CONFLICT
            elif org.has_conn_link:
                status = SyncStatus.NORG
            else:
                status = SyncStatus.NOSYNC

            crud.jd_link.create(
                db,
                JDRecordLink(
                    uri=org.uri,
                    data=org.model_dump(exclude_unset=True),
                    status=status,
                    local_persistent=False,
                    table_name="org",
                    table_key=None,
                    parent_id=None,
                    user_id=user_id,
                ),
            )


def remove_linked(db: Session, link: JDRecordLink) -> None:
    """### Deletes link and referenced local data.
    Does NOT check if it *should*, only if it *can*."""
    if not hasattr(crud, link.table_name):
        raise ValueError(f"Desync unsupported for {link.table_name=}")

    table_crud = getattr(crud, link.table_name)
    record = table_crud.get_or_raise(db, link.table_key)
    table_crud.delete(db, record)

    if link.table_name == "field_op":
        pass  # TODO: delete the rest of the stuff created by a field op sync.

    crud.jd_link.delete(db, link)


async def unsync_link(db: Session, link: JDRecordLink) -> bool:
    """
    Guarantees:
    - non-persistent local resources are deleted
    - children are unsynced and links are deleted, if applicable.

    Returns: whether the local resource and link was deleted (True) or disabled (False)

    DOES NOT MODIFY link.status!
    """
    children_removed = all([await unsync_link(db, child) for child in link.children])
    # TODO: modify webhook
    is_removable = children_removed and not link.local_persistent
    if is_removable:
        remove_linked(db, link)
    elif not link.local_persistent:  # If children exist, link becomes persistent.
        link = crud.jd_link.update(db, link, JDLinkUpdate(local_persistent=True))

    return is_removable


# TODO: should I add a get_first function to CRUDBase?
async def sync_link(db: Session, link: JDRecordLink) -> None:
    """
    Guarantees:
    - Resource(s) exist locally
    - local matches JD
    - children are discovered (if applicable).
    DOES NOT MODIFY link.status!
    """
    client = JDClient(db, link.connection)

    # NOTE: mention in docstring, but prob fine to update link.status w everything else
    # What fields would LinkUpdate need? local_persistent, data, table_key, parent_id

    changes = {}
    match link.table_name:
        case "org":
            # NOTE: Update the link
            jd_org = JDOrg.model_validate(await client.get(link.uri))
            fl_org = db.get(Org, link.table_key) if link.table_key else None
            if fl_org is None:
                fl_org = crud.org.get_first(db, Org.name == jd_org.name)
            if fl_org is None:
                fl_org = crud.org.create(db, OrgCreate(name=jd_org.name))
            elif not link.local_persistent:
                changes["local_persistent"] = True
            changes["data"] = jd_org.model_dump(exclude_unset=True)
            changes["table_key"] = {"id": fl_org.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # NOTE: Discover Children
            farm_links = {c.uri for c in link.children}
            jd_farms = await client.get(jd_org.linked("farms"), JDMulti[JDFarm])
            for jd_farm in jd_farms.values:
                if jd_farm.uri not in farm_links:
                    crud.jd_link.create(
                        db,
                        JDRecordLink(
                            uri=jd_farm.uri,
                            data=jd_farm.model_dump(exclude_unset=True),
                            status=SyncStatus.NOSYNC,
                            local_persistent=False,
                            table_name="farm",
                            table_key=None,
                            parent_id=link.id,
                            user_id=link.user_id,
                        ),
                    )
            # TODO: update webhook

        case "farm":
            assert (  # TODO: replace assert? maybe for an issue, unsync and start over?
                link.parent
                and link.parent.table_name == "org"
                and link.parent.table_key
            ), link.parent
            org_id = link.parent.table_key["id"]

            # NOTE: Update the link
            jd_farm = JDFarm.model_validate(await client.get(link.uri))
            fl_farm = db.get(Farm, link.table_key) if link.table_key else None
            if fl_farm is None:
                org_fil = [OrgFarm.org_id == org_id, OrgFarm.farm_id == Farm.id]
                filter = [select(1).where(*org_fil).exists(), Farm.name == jd_farm.name]
                fl_farm = crud.farm.get_first(db, *filter)
            if fl_farm is None:
                fl_farm = crud.farm.create(db, FarmCreate(name=jd_farm.name))
                own = OrgFarm(type=OrgFarmType.Own, org_id=org_id, farm_id=fl_farm.id)
                crud.org_farm.create(db, own)
            elif not link.local_persistent:
                changes["local_persistent"] = True
            changes["data"] = jd_farm.model_dump(exclude_unset=True)
            changes["table_key"] = {"id": fl_farm.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # NOTE: Discover Children
            field_links = {c.uri for c in link.children}
            jd_fields = await client.get(jd_farm.linked("fields"), JDMulti[JDField])
            for jd_field in jd_fields.values:
                if jd_field.uri not in field_links:
                    crud.jd_link.create(
                        db,
                        JDRecordLink(
                            uri=jd_field.uri,
                            data=jd_field.model_dump(exclude_unset=True),
                            status=SyncStatus.NOSYNC,
                            local_persistent=False,
                            table_name="field",
                            table_key=None,
                            parent_id=link.id,
                            user_id=link.user_id,
                        ),
                    )
            # TODO: update webhook

        case "field":
            assert (
                link.parent
                and link.parent.table_name == "farm"
                and link.parent.table_key
            ), link.parent
            farm_id = link.parent.table_key["id"]

            # NOTE: Update the link
            jd_field = JDField.model_validate(await client.get(link.uri))
            fl_field = db.get(Field, link.table_key) if link.table_key else None
            if fl_field is None:
                fl_field = crud.field.get_first(
                    db, Field.farm_id == farm_id, Field.name == jd_field.name
                )
            if fl_field is None:
                data = Field(  # TODO: always use type=FieldCrops?
                    name=jd_field.name, type=FieldType.FieldCrops, farm_id=farm_id
                )
                fl_field = crud.field.create(db, data)
            elif not link.local_persistent:
                changes["local_persistent"] = True
            changes["data"] = jd_field.model_dump(exclude_unset=True)
            changes["table_key"] = {"id": fl_field.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            child_links = {c.uri for c in link.children}
            jd_bounds = await client.get(
                jd_field.linked("boundaries"), JDMulti[JDBoundary]
            )
            jd_ops = await client.get(
                jd_field.linked("fieldOperation"),
                JDMulti[JDFieldOp],
                embed="measurementTypes",
            )
            for jd_field_child in jd_bounds.values + jd_ops.values:
                if jd_field_child.uri not in child_links:
                    pass  # TODO: build JDRecordLink
            # TODO: discover boundaries and operations
            # TODO: update webhook

        case "field_op":
            # TODO: client.get uri -> JDOperation
            # TODO: create operation (no columns to match existing ops that I can see)
            # TODO: deal with potentially making i/o/e records and bringing in boundary
            # TODO: Discover boundary
            # TODO: update webhooks
            pass
        case "boundary":
            # TODO: client.get uri -> JDBoundary
            # TODO: find or create boundary
            # TODO: update webhook
            pass

        case _:
            raise ValueError(f"Sync unsupported for {link.table_name=}")


async def update_status(db: Session, link: JDRecordLink, to_status: SyncStatus) -> None:
    """### Change JDRecordLink.status. All state changes should be done here.
    This function calls `sync_link` or `unsync_link` for applicable transitions.
    > Do NOT call `change_status` from `sync_link`, `unsync_link` or a function called
    by them unless you know with certainty it will not cause infinite recusion.
    """
    if link.status == to_status:
        return
    client = JDClient(db, link.connection)

    def exec_update(new_status: SyncStatus, target=link) -> JDRecordLink:
        return crud.jd_link.update(db, target, JDLinkUpdate(status=new_status))

    # TODO: This could run (and make request) multiple times per job. cache/precompute?
    async def still_norg(target=link) -> bool:
        """### Returns True if user has not allowed org connection in JD (NORG).
        Makes GET request to ensure fully up-to-date answer.
        """
        org = await client.get_org(target.uri)
        return org is None or org.has_conn_link

    async def resolve_conflicts(target=link) -> None:
        if target.table_name != "org":  # Conflicts are only for orgs.
            if target.status in (SyncStatus.NORG, SyncStatus.CONFLICT):  # Very unlikely
                exec_update(SyncStatus.NOSYNC, target)  # Clear invalid status
            return

        uri, user_id = target.uri, target.user_id
        filters = [JDRecordLink.uri == uri, JDRecordLink.user_id != user_id]
        other = crud.jd_link.get_paginated(db, 0, None, *filters)
        other_active = any(ln.status in SYNC_ACTIVE for ln in other.data)
        if target.status in SYNC_ACTIVE and other_active:  # resolve conflict
            log.error(f"Sync Conflict Detected. {target=}\n{other=}")
            active = [lnk for lnk in [target, *other.data] if lnk.status in SYNC_ACTIVE]
            active.sort(key=lambda x: cast(datetime, x.connection.first_established))
            active.pop(0)  # Let the oldest connection keep the active state.
            for lnk in active:
                await unsync_link(db, lnk)
                exec_update(SyncStatus.CONFLICT, lnk)
        else:
            no_conflict = target.status not in SYNC_ACTIVE and not other_active
            for lnk in [target, *other.data]:
                if no_conflict:
                    to = SyncStatus.NORG if await still_norg(lnk) else SyncStatus.NOSYNC
                    if lnk.status != to:
                        exec_update(to, lnk)
                elif not no_conflict and lnk.status == SyncStatus.NOSYNC:
                    exec_update(SyncStatus.CONFLICT, lnk)

    match (link.status, to_status):  # NOTE: choose action based on transition
        case (_, SyncStatus.NORG | SyncStatus.CONFLICT):  # Invalid for manual update
            return

        case (SyncStatus.NORG, _):  # try to clear status
            if not await still_norg():  # NORG constraint has cleared
                link = exec_update(SyncStatus.NOSYNC)
                await update_status(db, link, to_status)

        case (SyncStatus.CONFLICT, _):  # try to clear status
            await resolve_conflicts()
            if link.status not in (SyncStatus.CONFLICT, SyncStatus.NORG):
                await update_status(db, link, to_status)

        case (active, SyncStatus.NOSYNC) if active in SYNC_ACTIVE:  # desync
            await unsync_link(db, link)
            exec_update(to_status)
            await resolve_conflicts()  # Updates status to CONFLICT if applicable

        case (SyncStatus.SYNC | SyncStatus.DIRTY, SyncStatus.PAUSE):  # pause
            exec_update(to_status)

        case (_, active) if active in SYNC_ACTIVE:  # sync
            await resolve_conflicts()
            if link.status in (SyncStatus.CONFLICT, SyncStatus.NORG):
                return

            end_status = to_status if to_status != SyncStatus.DIRTY else SyncStatus.SYNC
            # NOTE: # DIRTY is from sync error. _job_id caps 1 job per resuorce_path.
            if link.status != SyncStatus.DIRTY:
                link = exec_update(SyncStatus.DIRTY)
                db.commit()  # NOTE: Commit status so queries during sync show DIRTY.
            await sync_link(db, link)
            exec_update(end_status)


async def modify_sync(ctx, user_id: UUID, uri: str, update: JDLinkUpdate) -> None:
    with user_session(ctx["engine"], user_id) as db:
        link = crud.jd_link.get_by_user_and_uri(db, user_id, uri)
        if not link:  # NOTE: should not happen due to check in endpoint.
            raise ValueError(f"Cannot modify unknown resource: {uri=}")

        # TODO: empty `update` likely a desire for manual sync (does nothing rn).
        if update.status:  # Decides if a sync is needed based on context.
            await update_status(db, link, update.status)
        crud.jd_link.update(db, link, update)  # Update other columns directly.


# NOTE: event: clientKey, eventTypeId, targetResource, token (when provided), metadata, links
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
