import logging
from asyncio import gather
from collections.abc import Generator
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from typing import cast
from uuid import UUID

from fastapi import HTTPException
from geoalchemy2.functions import (
    ST_Area,
    ST_Intersection,
    ST_Intersects,
    ST_Union,
)
from geoalchemy2.shape import from_shape
from rich.logging import RichHandler
from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, String, col, select, text
from sqlmodel import cast as sqlcast

from app.api.models import FarmCreate, JDLinkUpdate, OrgCreate, SyncLinkUpdate
from app.core.enums import (
    SYNC_ACTIVE,
    SYNC_ORG_ERR,
    BoundaryType,
    FieldType,
    OpType,
    OrgFarmType,
    SyncStatus,
)
from app.db import crud
from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    Farm,
    Field,
    FieldBoundary,
    FieldOp,
    JDRecordLink,
    JDShapefile,
    Org,
    OrgFarm,
)
from app.integrations.jd.models import (
    JDBoundary,
    JDComponent,
    JDFarm,
    JDField,
    JDFieldOp,
    JDLink,
    JDModel,
    JDMulti,
    JDOrg,
    JDProduct,
)
from app.integrations.jd.requests import JDClient

log_handler = RichHandler(show_time=False)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[log_handler])
log = logging.getLogger(__name__)

# region ------------------------------ General Helpers -------------------------------


@contextmanager
def user_session(engine: Engine, user_id: UUID) -> Generator[Session]:
    with Session(engine) as db:
        try:
            db.exec(text(f"SET SESSION \"app.current_user\"= '{user_id}'"))  # type: ignore
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


# endregion
# region ------------------------------- Unsync Helpers -------------------------------


def get_local_record(db: Session, _lnk: JDRecordLink) -> SQLModel | None:
    if _lnk.table_key is None:
        return None

    relevant_crud: CRUDBase | None = getattr(crud, _lnk.table_name, None)
    if relevant_crud is None or relevant_crud.model is None:
        return None

    return db.get(relevant_crud.model, _lnk.table_key)


def delete_local_data(db: Session, _lnk: JDRecordLink) -> None:
    """### Deletes the local data referenced by the link.
    Does NOT check if it *should*, only if it *can*.

    Does not remove the actual link, just the data it points to.
    """
    record = get_local_record(db, _lnk)
    if record is None:
        return

    crud_cls = getattr(crud, _lnk.table_name)
    log.info(f"Deleting {crud_cls.model=} {record=}")
    crud_cls.delete(db, record)

    if _lnk.table_name == "field_op":
        pass  # TODO: delete the rest of the stuff created by a field op sync?


async def try_unsync(db: Session, _lnk: JDRecordLink) -> None:
    """
    Attempts to unsync all children by calling `change_status` on them.

    Deletes all child links that are not connected to persistent data.

    Deletes the data referred to by _lnk if `_lnk.local_persistent` is False.

    If the local data does not exist even though local_persistent is True,
    local_perssistent will become false.

    If the link has children that are persistent, but it is not, then local_persistent
    will become True.
    """
    remove_children = []
    for child in _lnk.children:
        await change_status(db, child, SyncStatus.Unsynced)
        if not child.local_persistent:
            remove_children.append(child)

    children_remain = len(remove_children) < len(_lnk.children)
    if remove_children:
        log.info(f"Deleting Links: {[c.uri for c in remove_children]}")
        crud.jd_link.delete_multiple(db, remove_children)

    # TODO: Modify webhook.

    should_persist = _lnk.local_persistent and get_local_record(db, _lnk) is not None
    should_persist |= children_remain
    # TODO: check for local data that relies on linked data but is not in children?
    if _lnk.local_persistent != should_persist:
        log.info(f"Persistence Mismatch {_lnk.local_persistent=} -> {should_persist=}")
        log.info(f"{bool(get_local_record(db, _lnk))=} {children_remain=}")
        crud.jd_link.update(db, _lnk, JDLinkUpdate(local_persistent=should_persist))

    if not _lnk.local_persistent:
        delete_local_data(db, _lnk)


# endregion
# region -------------------------------- Sync Helpers --------------------------------


def child_link(link: JDRecordLink, table: str, child: JDModel) -> JDRecordLink | None:
    if child.uri in link.child_uris:
        return None

    return JDRecordLink(
        uri=child.uri,
        data=child.model_dump(),
        status=SyncStatus.Unsynced,
        local_persistent=False,
        table_name=table,
        table_key=None,
        parent_id=link.id,
        user_id=link.user_id,
    )


def child_links[T: JDModel](
    link: JDRecordLink, table: str, children: JDMulti[T]
) -> list[JDRecordLink]:
    return [child for x in children.values if (child := child_link(link, table, x))]


async def get_or_attach_shapefile(
    client: JDClient, link: JDRecordLink, op: JDFieldOp | None = None
) -> JDShapefile:
    """### Request the shapefile for the given operation and attach it to the `link`.
    `op` may be provided, but if not it will be generated from `link.data` (expensive).
    """
    if link.table_name != "field_op":
        raise RuntimeError("Cannot attach a shapefile to a link that isn't a FieldOp.")

    shp = link.shapefile
    if shp:
        return shp

    if op is None:
        op = JDFieldOp.model_validate(link.data)

    zip_data = await client.get_shp_zip(op.get_link("shapeFileAsync").uri)
    return crud.jd_shp.create(
        client.db, JDShapefile(zip_data=zip_data, link_id=link.id)
    )


async def links_from_op(
    client: JDClient, link: JDRecordLink, op: JDFieldOp | None = None
) -> tuple[list[JDRecordLink], list[JDRecordLink]] | None:
    """### Generate the `JDRecordLink`s that are based on the given field_op link.
    This will create a list of links that are children of the parent org
    (product and equipment links) and a list of links that are children of the field_op
    link (op_input, op_output, op_equipment, boundary links).

    `op` may be provided, but if not it will be generated from `link.data` (expensive).
    """
    if link.table_name != "field_op":
        return None

    if op is None:
        op = JDFieldOp.model_validate(link.data)

    log.info(
        f"Generating Children for {op.cropSeason} {op.fieldOperationType.capitalize()}"
    )

    # NOTE: Walk up tree to org; inefficient.
    org_link = link
    while org_link.parent:
        org_link = org_link.parent

    org_children: list[JDRecordLink] = []
    op_children: list[JDRecordLink] = []
    try:
        boundary = await client.get(op.generate_boundary_uri, JDBoundary)
        boundary.links.append(JDLink(rel="self", uri=op.generate_boundary_uri))
        boundary_link = child_link(link, "boundary", boundary)
        if boundary_link:
            op_children.append(boundary_link)
            log.info("Adding Boundary to op.")
        else:
            log.info("Boundary not added to children.")
    except HTTPException as e:
        log.warning(f"Refused to generate boundary: {e}")

    # shp = await get_or_attach_shapefile(client, link, op)
    # log.info(f"shp metadata: {json.dumps(shp.shp_meta, indent=2)}")
    # shp_meta = JDShpMeta.model_validate(shp.shp_meta)
    # log.info(f"Shapefile attached {shp.gdf.shape}: Columns={list(shp.gdf.columns)}")

    # TODO: Use measurements from products (rate) or something to get better units?
    # Where can I get information on Products used? Equipment?
    # Products: op.measurements.inputs
    #   do I need to compare it from both productTotals and products?
    #   Maybe from the shp metadata?
    log.info("Products:")
    # log.info(f"{shp_meta.Product=}")
    # log.info(f"{shp_meta.CropToken=}")

    # TODO: Should make product/equipment links as children of the org link
    # TODO: two maps {productID: Product Information} and {productId: Measurements}
    # TODO: op.measurements.inputs gives the latter. Where to get the former?
    # I think that op.products is probably best?
    items: list[JDProduct | JDComponent] = []
    for p in op.products or []:
        items.extend(([p.carrier] if p.carrier else []) + (p.components or []) or [p])

    # TODO: If the productType doesn't exist or is something like "OTHER", I should find
    # another way to get product info? What about if I request it and get nothing back?
    for i in items:
        if i.productType is None:
            log.warning(f"Found product with no type: {i}")

    org_uri = op.get_link("organization").uri
    reqs = gather(
        *(client.get_parent_product(org_uri, i.productType, i.guid) for i in items)
    )
    prods = dict(zip((i.guid for i in items), await reqs, strict=False))
    org_children.extend(
        filter(None, [child_link(org_link, "product", p) for p in prods.values() if p])
    )
    log.info(f"Adding {len(org_children)} Product(s) to org.")

    # TODO: Get org link
    # TODO: add product children
    # TODO: add equipment children

    # TODO: Add input/output/equipment measurements as children
    # TODO: Add a way to restrict the syncing of one of these unless the product/
    # equipment at the org level is synced.
    # NOTE: Using same uri as product it's attached to. Good idea? We'll see.
    for table, measurements in (
        ("op_input", op.measurements.inputs),
        ("op_output", op.measurements.outputs),
    ):
        for m in measurements:
            # TODO: THIS WON"T WORK because products will exclude synced/missing prods
            #   I need another way to connect them to product info.
            product_info = prods.get(m.guid)
            if product_info is None or product_info.uri in link.child_uris:
                log.info(f"Skipping adding op child {m=} {product_info=}")
                continue

            log.info("Adding Measurement to Op")
            op_children.append(
                JDRecordLink(
                    uri=product_info.uri,
                    data=m.model_dump(),
                    status=SyncStatus.Unsynced,
                    local_persistent=False,
                    table_name=table,
                    table_key=None,
                    parent_id=link.id,
                    user_id=link.user_id,
                )
            )

    # TODO: Getting the op_equipment record is going to be a bear. How do I connect ids?

    return org_children, op_children


async def try_sync(db: Session, link: JDRecordLink) -> bool:
    """
    Guarantees:
    - Resource(s) exist locally
    - local matches JD
    - children are discovered (if applicable).

    Returns whether the sync was successful. False indicates something went very wrong
    or link is not valid as a sync target for some reason.
    > DOES NOT MODIFY link.status!
    """
    changes = {}
    client = JDClient(db, link.connection)
    match link.table_name:
        case "org":
            if link.parent is not None:
                log.error(f"Sync Error, Org has parent.\n{link=}\n{link.parent=}")
                return False

            # NOTE: Update the link
            jd_org = await client.get(link.uri, JDOrg)
            fl_org = db.get(Org, link.table_key) if link.table_key else None

            if fl_org is None:
                link_taken = (
                    select(1)
                    .where(
                        JDRecordLink.table_name == link.table_name,
                        JDRecordLink.user_id == link.user_id,
                        sqlcast(Org.id, String)
                        == col(JDRecordLink.table_key)["id"].astext,
                    )
                    .exists()
                )
                fl_org = crud.org.get_first(db, Org.name == jd_org.name, ~link_taken)
                if fl_org and not link.local_persistent:
                    changes["local_persistent"] = True

            if fl_org is None:
                fl_org = crud.org.create(db, OrgCreate(name=jd_org.name))

            changes["data"] = jd_org.model_dump()
            changes["table_key"] = {"id": fl_org.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # NOTE: Discover children
            farms = await client.get(jd_org.get_link("farms").uri, JDMulti[JDFarm])
            crud.jd_link.create_multiple(db, child_links(link, "farm", farms))

            # TODO: update webhook

        case "farm":
            if (
                link.parent is None
                or link.parent.table_name != "org"
                or link.parent.table_key is None
            ):
                log.error(f"Sync Error, Invalid Parent.{link=}\n{link.parent=}")
                return False
            org_id = link.parent.table_key["id"]

            # NOTE: Update the link
            jd_farm = await client.get(link.uri, JDFarm)
            fl_farm = db.get(Farm, link.table_key) if link.table_key else None

            if fl_farm is None:
                in_org = (
                    select(1)
                    .where(OrgFarm.org_id == org_id, OrgFarm.farm_id == Farm.id)
                    .exists()
                )
                link_taken = (
                    select(1)
                    .where(
                        JDRecordLink.table_name == link.table_name,
                        JDRecordLink.user_id == link.user_id,
                        sqlcast(Farm.id, String)
                        == col(JDRecordLink.table_key)["id"].astext,
                    )
                    .exists()
                )
                fl_farm = crud.farm.get_first(
                    db, Farm.name == jd_farm.name, in_org, ~link_taken
                )
                if fl_farm and not link.local_persistent:
                    changes["local_persistent"] = True

            if fl_farm is None:
                # TODO: Do I need to put similar checks anywhere else?
                if jd_farm.name is None:
                    raise ValueError("Cannot create a farm without a valid name.")
                fl_farm = crud.farm.create(db, FarmCreate(name=jd_farm.name))
                own = OrgFarm(type=OrgFarmType.Own, org_id=org_id, farm_id=fl_farm.id)
                crud.org_farm.create(db, own)

            changes["data"] = jd_farm.model_dump()
            changes["table_key"] = {"id": fl_farm.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # NOTE: Discover Children
            fields = await client.get(jd_farm.get_link("fields").uri, JDMulti[JDField])
            crud.jd_link.create_multiple(db, child_links(link, "field", fields))

            # TODO: update webhook

        case "field":
            if (
                link.parent is None
                or link.parent.table_name != "farm"
                or link.parent.table_key is None
            ):
                log.error(f"Sync Error, Invalid Parent.{link=}\n{link.parent=}")
                return False
            farm_id = link.parent.table_key["id"]

            # NOTE: Update the link
            jd_field = await client.get(link.uri, JDField)
            fl_field = db.get(Field, link.table_key) if link.table_key else None

            if fl_field is None:
                link_taken = (
                    select(1)
                    .where(
                        JDRecordLink.table_name == link.table_name,
                        JDRecordLink.user_id == link.user_id,
                        sqlcast(Field.id, String)
                        == col(JDRecordLink.table_key)["id"].astext,
                    )
                    .exists()
                )
                filters = [
                    Field.farm_id == farm_id,
                    Field.name == jd_field.name,
                    ~link_taken,
                ]
                fl_field = crud.field.get_first(db, *filters)
                if fl_field and not link.local_persistent:
                    changes["local_persistent"] = True

            if fl_field is None:
                data = Field(
                    name=jd_field.name, type=FieldType.FieldCrops, farm_id=farm_id
                )
                fl_field = crud.field.create(db, data)
            changes["data"] = jd_field.model_dump()
            changes["table_key"] = {"id": fl_field.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # NOTE: Discover Children
            bds = await client.get(
                jd_field.get_link("boundaries").uri, JDMulti[JDBoundary]
            )
            # TODO: This could be a good place to use a gather() to start requesting shp
            # TODO: Max itemLimit for fieldOps is 100. More data takes multiple requests
            ops = await client.get(
                jd_field.get_link("fieldOperation").uri,
                JDMulti[JDFieldOp],
                params={"embed": "measurementTypes"},
            )
            crud.jd_link.create_multiple(db, child_links(link, "boundary", bds))
            crud.jd_link.create_multiple(db, child_links(link, "field_op", ops))

            # TODO: update webhook

        case "boundary":
            if (
                link.parent is None
                or link.parent.table_name not in ("field", "field_op")
                or link.parent.table_key is None
            ):
                log.error(f"Sync Error, Invalid Parent.{link=}\n{link.parent=}")
                return False
            # NOTE: get parent field or parent op's parent field.
            fl_op = None
            field_id = link.parent.table_key["id"]
            if link.parent.table_name == "field_op":
                fl_op = db.get(FieldOp, link.parent.table_key)
                if fl_op is None:
                    return False
                field_id = fl_op.field_id

            # NOTE: Update the link
            jd_bound = await client.get(link.uri, JDBoundary)
            fl_bound = db.get(FieldBoundary, link.table_key) if link.table_key else None

            if fl_bound is None:
                link_taken = (
                    select(1)
                    .where(
                        JDRecordLink.table_name == link.table_name,
                        JDRecordLink.user_id == link.user_id,
                        sqlcast(FieldBoundary.id, String)
                        == col(JDRecordLink.table_key)["id"].astext,
                    )
                    .exists()
                )

                geom = from_shape(jd_bound.as_shapely(), srid=4326)
                iou = ST_Area(ST_Intersection(FieldBoundary.geom, geom)) / ST_Area(
                    ST_Union(FieldBoundary.geom, geom)
                )
                # TODO: move magic number somewhere?
                filters = [
                    FieldBoundary.field_id == field_id,
                    ST_Intersects(FieldBoundary.geom, geom),
                    iou > 0.995,  # Boundaries have high overlap (Jaccard Index)
                    ~link_taken,
                ]
                fl_bound = crud.boundary.get_first(db, *filters, order_by=iou.desc())

            if fl_bound is None:
                data = FieldBoundary(
                    type=BoundaryType.Subfield if fl_op else BoundaryType.Primary,
                    active=jd_bound.active,
                    description=jd_bound.name,
                    geom=jd_bound.wkt,
                    field_id=field_id,
                )
                fl_bound = crud.boundary.create(db, data)
            changes["data"] = jd_bound.model_dump()
            changes["table_key"] = {"id": fl_bound.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # TODO: update webhook

        case "field_op":
            if (
                link.parent is None
                or link.parent.table_name != "field"
                or link.parent.table_key is None
            ):
                log.error(f"Sync Error, Invalid Parent.\n{link=}\n{link.parent=}")
                return False
            field_id = link.parent.table_key["id"]

            # NOTE: Update the link
            jd_op = await client.get(link.uri, JDFieldOp)
            log.info(f"Syncing {jd_op.cropSeason} {jd_op.fieldOperationType}")
            fl_op = db.get(FieldOp, link.table_key) if link.table_key else None
            # TODO: Is there a way to see if the operation already exists?
            if fl_op is None:
                crop = crud.crop.get_first_similar_name(db, jd_op.cropName)
                meas = jd_op.measurements

                # TODO: determine Till vs. NoTill ops?
                data = FieldOp(
                    type=OpType(jd_op.fieldOperationType.capitalize()),
                    season=jd_op.cropSeason,
                    start=jd_op.startDate,
                    end=jd_op.endDate,
                    crop_id=crop.id if crop else None,
                    area=meas.area.value if meas.area else None,
                    area_unit=meas.area.unit if meas.area else None,
                    boundary_id=None,  # TODO: make this now or sync it separately?
                    field_id=field_id,
                )
                fl_op = crud.field_op.create(db, data)
            changes["data"] = jd_op.model_dump()
            changes["table_key"] = {"id": fl_op.id}
            crud.jd_link.update(db, link, SyncLinkUpdate(**changes))

            # When you click sync on a field operation, it will sync op exists
            # It will

            # TODO: Discover children, possibilities are:
            #   - list of products that were used. Syncing product adds i/o records
            #   - list of equipment that were used. Syncing eq adds eq use records
            #   - one boundary for the operation that can be added as a Subfield
            #   - not sure what to use shpfile for; exract data for op_equipment record?

            """
            From the data in jd_op, I have the measurements, I have the boundary, and
            the shapefile. I need to turn all of that information into basically
            everything that I need to sync. That would be a list of products, a list of
            equipment, the boundary, and some way of including the op_input/output/eq
            records.
            """
            new_links = await links_from_op(client, link, jd_op)
            new_op_children, new_org_children = new_links if new_links else ([], [])
            log.info(f"Creating {len(new_op_children)=} and {len(new_org_children)=}")
            crud.jd_link.create_multiple(db, new_op_children + new_org_children)

            # TODO: update webhooks
            pass

        case _:
            log.error(f"Sync unsupported for {link.table_name=}")
            return False
    return True


# endregion
# region ------------------------------- Status Helpers -------------------------------


async def accessible(db: Session, link: JDRecordLink) -> bool:
    if link.table_name != "org":
        return True  # If not an org link, assume conn was allowed to make current link

    if link.data and not JDOrg.model_validate(link.data).has_conn_link:
        return True  # has data, which doesn't have connection link, good to go

    org = await JDClient(db, link.connection).get(link.uri, JDOrg)
    return org and not org.has_conn_link  # update data and check again for conn link.


async def resolve_org_conflicts(db: Session, link: JDRecordLink) -> None:
    """Ensures at most one link to the org referred to by `link` is active across users.
    * If more than one is active, will unsync all but oldest.
    * If exactly one is active, will make sure the rest are set to conflict status.
    * If none are active, will clear all conflict statuses.
    """
    if link.table_name != "org":
        return

    others = crud.jd_link.get_paginated(
        db, 0, None, JDRecordLink.uri == link.uri, JDRecordLink.user_id != link.user_id
    ).data
    another_active = any(x.status in SYNC_ACTIVE for x in others)
    if link.status in SYNC_ACTIVE and another_active:
        log.error(f"Sync Conflict Detected. {link=}\n{others=}")
        active = [x for x in [link, *others] if x.status in SYNC_ACTIVE]
        active.sort(key=lambda x: cast(datetime, x.connection.first_established))
        active.pop(0)  # Oldest connection keeps the active state.
        for bad_link in active:
            await try_unsync(db, bad_link)
            crud.jd_link.update(db, bad_link, JDLinkUpdate(status=SyncStatus.Conflict))
    else:
        no_conflict = link.status not in SYNC_ACTIVE and not another_active
        for x in [link, *others]:
            if no_conflict:
                is_accessible = await accessible(db, x)
                to = SyncStatus.Unsynced if is_accessible else SyncStatus.Inaccessible
                if x.status != to:
                    crud.jd_link.update(db, x, JDLinkUpdate(status=to))
            elif not no_conflict and x.status == SyncStatus.Unsynced:
                crud.jd_link.update(db, x, JDLinkUpdate(status=SyncStatus.Conflict))


async def change_status(db: Session, link: JDRecordLink, to_stat: SyncStatus):
    """### Change JDRecordLink.status.
    Behavior differs depending on requirements to go from current status to `to_status`.
    Primarily, that is calling `sync_link` or `unsync_link` for applicable transitions.

    This and helpers are the ONLY functions that should directly modify link.status.

    Note about recursion here: Each recursive call is basically: check if a
    restriction has cleared and start over. They are designed to recurse at most once.
    """

    def set_status(new_status: SyncStatus, _lnk=link) -> JDRecordLink:
        if _lnk.status != new_status:
            return crud.jd_link.update(db, _lnk, JDLinkUpdate(status=new_status))
        return _lnk

    if link.table_name != "org" and link.status in SYNC_ORG_ERR:
        set_status(SyncStatus.Unsynced)  # Unlikely; clear org-only status from non-org
    if link.status == to_stat:
        return

    match (link.status, to_stat):  # NOTE: choose action based on transition
        case (_, err) if err in SYNC_ORG_ERR:  # Invalid for manual update
            return

        case (SyncStatus.Inaccessible, _):  # try to clear status
            if await accessible(db, link):
                link = set_status(SyncStatus.Unsynced)
                await change_status(db, link, to_stat)

        case (SyncStatus.Conflict, _):  # try to clear status
            await resolve_org_conflicts(db, link)
            if link.status not in SYNC_ORG_ERR:
                await change_status(db, link, to_stat)

        case (active, SyncStatus.Unsynced) if active in SYNC_ACTIVE:  # desync
            log.info(f"Desyncing <JDRecordLink {link.uri}>")
            await try_unsync(db, link)
            set_status(to_stat, link)
            await resolve_org_conflicts(db, link)  # May update status to CONFLICT

        case (SyncStatus.Synced | SyncStatus.Pending, SyncStatus.Paused):  # pause
            set_status(to_stat)

        case (_, active) if active in SYNC_ACTIVE:  # sync
            await resolve_org_conflicts(db, link)
            if link.status in SYNC_ORG_ERR:
                return

            if link.parent and link.parent.status not in SYNC_ACTIVE:
                return  # if it has a parent, it must be active

            end_stat = to_stat if to_stat != SyncStatus.Pending else SyncStatus.Synced
            if link.status != SyncStatus.Pending:
                link = set_status(SyncStatus.Pending)
                db.commit()  # NOTE: Commit status so queries during sync show DIRTY.
            await try_sync(db, link)
            set_status(end_stat)


# endregion
# region ------------------------------ Worker Functions ------------------------------

# TODO: just pass the link as an arg to each? the endpoint gets it to check it anyway.


async def discover_orgs(ctx, user_id: UUID, member_only=True):
    log.info(f"Discovering orgs for {user_id=}")
    with user_session(ctx["engine"], user_id) as db:
        client = JDClient.from_user(db, user_id)
        links = []
        for org in await client.orgs(member_only):
            org_links = crud.jd_link.get_paginated(
                db, 0, None, JDRecordLink.uri == org.uri
            )
            if next((v for v in org_links.data if v.user_id == user_id), None):
                continue  # NOTE: if a link exists, just leave it be.

            # Starting status
            others = [v for v in org_links.data if v.user_id != user_id]
            if any(v.status in SYNC_ACTIVE for v in others):
                status = SyncStatus.Conflict
            elif org.has_conn_link:
                status = SyncStatus.Inaccessible
            else:
                status = SyncStatus.Unsynced

            links.append(
                JDRecordLink(
                    uri=org.uri,
                    data=org.model_dump(),
                    status=status,
                    local_persistent=False,
                    table_name="org",
                    table_key=None,
                    parent_id=None,
                    user_id=deepcopy(user_id),
                )
            )
        return crud.jd_link.create_multiple(db, links)


async def modify_sync(ctx, user_id: UUID, uri: str, update: JDLinkUpdate) -> None:
    with user_session(ctx["engine"], user_id) as db:
        link = crud.jd_link.get_by_user_and_uri(db, user_id, uri)
        if not link:
            return

        if update.status:  # Update status by whatever action is needed to do so
            await change_status(db, link, update.status)

        new_lp = update.local_persistent
        if new_lp is not None and link.local_persistent != new_lp:
            crud.jd_link.update(db, link, JDLinkUpdate(local_persistent=new_lp))


async def prepare_op(
    ctx, user_id: UUID, uri: str
) -> tuple[list[JDRecordLink], list[JDRecordLink]] | None:
    with user_session(ctx["engine"], user_id) as db:
        link = crud.jd_link.get_by_user_and_uri(db, user_id, uri)
        if not link:
            return None

        client = JDClient(db, link.connection)
        return await links_from_op(client, link)


# NOTE: event.clientKey, eventTypeId, targetResource, token (if given), metadata, links
async def handle_webhook_event(ctx, user_id: UUID, event: dict) -> None:
    with user_session(ctx["engine"], user_id) as db:
        event_type = event.get("eventTypeId")
        uri = event.get("targetResource")
        link = crud.jd_link.get_by_user_and_uri(db, user_id, uri) if uri else None
        log.info(f"[Webhook Event] Resource {uri=} has {link=}")
        match event_type:
            case "heartbeat":
                log.info("[Webhook Event] Ba-dum <3")
            case "subscriptionVerification":
                log.info(f"[Webhook Event] Subscription Verified, {uri=}")
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


# TODO: I need a function that I can run at startup/periodically to validate sync trees.

# endregion
