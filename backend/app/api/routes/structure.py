from uuid import UUID

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import ReadSession, UserSession
from app.core.enums import DocTag, OrgFarmType
from app.db import crud
from app.db.models import (
    BoundaryCreate,
    BoundaryUpdate,
    Farm,
    FarmCreate,
    FarmUpdate,
    Field,
    FieldBoundary,
    FieldCreate,
    FieldUpdate,
    Org,
    OrgCreate,
    OrgFarm,
    OrgFarmPublic,
    OrgFarmUpsert,
    OrgUpdate,
    Paginated,
)

org_router = APIRouter(tags=[DocTag.STRUCT_ORG])
farm_router = APIRouter(tags=[DocTag.STRUCT_FARM])
org_farm_router = APIRouter(tags=[DocTag.STRUCT_ORG, DocTag.STRUCT_FARM])
field_router = APIRouter(tags=[DocTag.STRUCT_FIELD])
boundary_router = APIRouter(tags=[DocTag.STRUCT_BOUND])

router = APIRouter()  # Combine routers at the end (after endpoints are added)

# region ------------------------------- Org Endpoints --------------------------------


@org_router.get("/orgs", response_model=Paginated[Org])
def list_orgs(db: ReadSession, skip: int = 0, limit: int = 10):
    return crud.org.get_paginated(db, skip, limit)


@org_router.post("/orgs", response_model=Org)
def create_org(db: UserSession, data_in: OrgCreate):
    return crud.org.create(db, data_in)


@org_router.get("/orgs/{id}", response_model=Org)
def get_org(db: ReadSession, id: UUID):
    return crud.org.get_or_raise(db, id)


@org_router.patch("/orgs/{id}", response_model=Org)
def edit_org(db: UserSession, id: UUID, data_in: OrgUpdate):
    record = crud.org.get_or_raise(db, id)
    return crud.org.update(db, record, data_in)


@org_router.delete("/orgs/{id}", response_model=Org)
def delete_org(db: UserSession, id: UUID):
    record = crud.org.get_or_raise(db, id)
    return crud.org.delete(db, record)


# endregion
# region ------------------------------- Farm Endpoints -------------------------------


@farm_router.get("/orgs/{id}/farms", response_model=Paginated[Farm])
def list_org_farms(db: ReadSession, id: UUID, skip: int = 0, limit: int = 10):
    query = select(1).where(OrgFarm.org_id == id, OrgFarm.farm_id == Farm.id).exists()
    return crud.farm.get_paginated(db, skip, limit, query)


@farm_router.post("/orgs/{id}/farms", response_model=Farm)
def create_farm(
    db: UserSession,
    id: UUID,
    data_in: FarmCreate,
    org_relation: OrgFarmType = OrgFarmType.Own,
):
    org = crud.org.get_or_raise(db, id)
    new_farm = crud.farm.create(db, data_in)
    crud.org_farm.create(
        db, OrgFarm(org_id=org.id, farm_id=new_farm.id, type=org_relation)
    )
    return new_farm


@farm_router.get("/farms/{id}", response_model=Farm)
def get_farm(db: ReadSession, id: UUID):
    return crud.farm.get_or_raise(db, id)


@farm_router.patch("/farms/{id}", response_model=Farm)
def edit_farm(db: UserSession, id: UUID, data_in: FarmUpdate):
    record = crud.farm.get_or_raise(db, id)
    return crud.farm.update(db, record, data_in)


@farm_router.delete("/farms/{id}", response_model=Farm)
def delete_farm(db: UserSession, id: UUID):
    record = crud.farm.get_or_raise(db, id)
    return crud.farm.delete(db, record)


# endregion
# region ------------------------- Org Farm Access Endpoints --------------------------


@org_farm_router.put(
    "/orgs/{org_id}/farms/{farm_id}/access", response_model=OrgFarmPublic
)
def set_org_farm_access(
    db: UserSession, org_id: UUID, farm_id: UUID, data_in: OrgFarmUpsert
):
    org = crud.org.get_or_raise(db, org_id)
    farm = crud.farm.get_or_raise(db, farm_id)
    access = db.get(OrgFarm, (org.id, farm.id))
    if access:
        return crud.org_farm.update(db, access, data_in)
    return crud.org_farm.create(
        db, OrgFarm(org_id=org.id, farm_id=farm.id, type=data_in.type)
    )


@org_farm_router.get(
    "/orgs/{org_id}/farms/{farm_id}/access", response_model=OrgFarmPublic
)
def check_org_farm_access(db: ReadSession, org_id: UUID, farm_id: UUID):
    org = crud.org.get_or_raise(db, org_id)
    farm = crud.farm.get_or_raise(db, farm_id)
    access = db.get(OrgFarm, (org.id, farm.id))
    if access:
        return access
    return OrgFarmPublic(org_id=org.id, farm_id=farm.id)


@org_farm_router.delete(
    "/orgs/{org_id}/farms/{farm_id}/access", response_model=OrgFarmPublic
)
def delete_org_farm_access(db: UserSession, org_id: UUID, farm_id: UUID):
    record = crud.org_farm.get_or_raise(db, (org_id, farm_id))
    return crud.org_farm.delete(db, record)


# endregion
# region ------------------------------- Field Endpoints -------------------------------


@field_router.get("/farms/{id}/fields", response_model=Paginated[Field])
def list_farm_fields(db: ReadSession, id: UUID, skip: int = 0, limit: int = 10):
    farm = crud.farm.get_or_raise(db, id)
    return crud.field.get_paginated(db, skip, limit, Field.farm_id == farm.id)


@field_router.post("/fields", response_model=Field)
def create_field(db: UserSession, data_in: FieldCreate):
    return crud.field.create(db, data_in)


@field_router.get("/fields/{id}", response_model=Field)
def get_field(db: ReadSession, id: UUID):
    return crud.field.get_or_raise(db, id)


@field_router.patch("/fields/{id}", response_model=Field)
def edit_field(db: UserSession, id: UUID, data_in: FieldUpdate):
    record = crud.field.get_or_raise(db, id)
    return crud.field.update(db, record, data_in)


@field_router.delete("/fields/{id}", response_model=Field)
def delete_field(db: UserSession, id: UUID):
    record = crud.field.get_or_raise(db, id)
    return crud.field.delete(db, record)


# endregion
# region ----------------------------- Boundary Endpoints -----------------------------


@boundary_router.get("/fields/{id}/boundaries", response_model=Paginated[FieldBoundary])
def list_field_boundaries(db: ReadSession, id: UUID, skip: int = 0, limit: int = 10):
    field = crud.field.get_or_raise(db, id)
    return crud.boundary.get_paginated(
        db, skip, limit, FieldBoundary.field_id == field.id
    )


@boundary_router.post("/boundaries", response_model=FieldBoundary)
def create_boundary(db: UserSession, data_in: BoundaryCreate):
    return crud.boundary.create(db, data_in)


@boundary_router.get("/boundaries/{id}", response_model=FieldBoundary)
def get_boundary(db: ReadSession, id: UUID):
    return crud.boundary.get_or_raise(db, id)


@boundary_router.patch("/boundaries/{id}", response_model=FieldBoundary)
def edit_boundary(db: UserSession, id: UUID, data_in: BoundaryUpdate):
    record = crud.boundary.get_or_raise(db, id)
    return crud.boundary.update(db, record, data_in)


@boundary_router.delete("/boundaries/{id}", response_model=FieldBoundary)
def delete_boundary(db: UserSession, id: UUID):
    record = crud.boundary.get_or_raise(db, id)
    return crud.boundary.delete(db, record)


# endregion

router.include_router(org_router)
router.include_router(farm_router)
router.include_router(org_farm_router)
router.include_router(field_router)
router.include_router(boundary_router)
