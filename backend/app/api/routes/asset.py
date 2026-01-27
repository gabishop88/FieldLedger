from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import ReadSession, UserSession
from app.api.messages import ExeMsg
from app.db import crud
from app.db.models import (
    Farm,
    FarmCreate,
    FarmUpdate,
    Field,
    FieldCreate,
    FieldUpdate,
    Paginated,
)

# Similarity thresholds when searching
NAME_THRESH = 0.4
DESC_THRESH = 0.2


router = APIRouter(prefix="/farm")


# region ------------------------------- Farm Endpoints -------------------------------


@router.get("/search", response_model=Paginated[Farm])
def farm_search(
    db: ReadSession,
    name: str | None = None,
    desc: str | None = None,
    skip=0,
    limit=10,
) -> Paginated[Farm]:
    """## Search for one or more farms.
    You may search by name, which will have to be close to the full name,
    or by description to match farm descriptions that approximately contain the search.
    """
    filters = []
    if name is not None:
        filters.append(func.similarity(Farm.name, name) > NAME_THRESH)
    if desc is not None:
        filters.append(func.word_similarity(Farm.description, desc) > DESC_THRESH)

    return crud.farm.get_paginated(db, skip, limit, *filters)


@router.get("/{farm}", response_model=Farm)
def get_one_farm(db: ReadSession, farm: str) -> Farm:
    """## Find a single farm based on either its id or name.
    Matches name using similarity search.
    """
    try:
        id = UUID(farm)
        rec = db.get(Farm, id)
    except ValueError:
        rec = db.exec(
            select(Farm)
            .where(func.similarity(Farm.name, farm) > NAME_THRESH)
            .order_by(func.similarity(Farm.name, farm).desc())
        ).first()

    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ExeMsg.NF.format("Farm", farm))
    return rec


@router.post("/", response_model=Farm)
def create_farm(db: UserSession, farm_in: FarmCreate) -> Farm:
    return crud.farm.create(db, farm_in)


@router.patch("/{farm}", response_model=Farm)
def update_farm(db: UserSession, edits: FarmUpdate, farm: str) -> Farm:
    rec = get_one_farm(db, farm)
    return crud.farm.update(db, rec, edits)


@router.delete("/{farm}", response_model=Farm)
def delete_farm(db: UserSession, farm: str) -> Farm:
    farm_obj = get_one_farm(db, farm)
    return crud.farm.delete(db, farm_obj)


# endregion
# region ------------------------------ Field Endpoints -------------------------------


@router.get("/{farm}/fields", response_model=Paginated[Field])
def get_farm_fields(
    db: ReadSession, farm: str, skip=0, limit=10
) -> Paginated[Field]:
    """## Get all fields for a given farm by its ID or name."""
    farm_rec = get_one_farm(db, farm)
    return crud.field.get_paginated(db, skip, limit, Field.farm_id == farm_rec.id)


@router.get("/{farm}/fields/{field}", response_model=Field)
def get_farm_field(db: ReadSession, farm: str, field: str) -> Field:
    """## Get a single field by its ID or name within a given farm by its ID or name."""
    farm_rec = get_one_farm(db, farm)

    try:
        field_id = UUID(field)
        field_rec = db.get(Field, field_id)
    except ValueError:
        field_rec = db.exec(
            select(Field)
            .where(
                Field.farm_id == farm_rec.id,
                func.similarity(Field.name, field) > NAME_THRESH,
            )
            .order_by(func.similarity(Field.name, field).desc())
        ).first()

    if field_rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ExeMsg.NF.format("Field", field))
    return field_rec


@router.post("/{farm}/fields", response_model=list[Field])
def add_fields(
    db: UserSession, farm: str, new_fields: list[FieldCreate]
) -> Sequence[Field]:
    """## Add one or more fields to a given farm by its ID or name."""
    farm_rec = get_one_farm(db, farm)
    fields_in_farm = [
        Field.model_validate(field, update={"farm_id": farm_rec.id})
        for field in new_fields
    ]

    return crud.field.create_multiple(db, fields_in_farm)


@router.patch("/{farm}/fields/{field}", response_model=Field)
def update_field(
    db: UserSession, farm: str, field: str, edits: FieldUpdate
) -> Field:
    """## Update a field within a given farm by their IDs or names."""
    field_rec = get_farm_field(db, farm, field)
    return crud.field.update(db, field_rec, edits)


@router.delete("/{farm}/fields/{field}", response_model=Field)
def delete_field(db: UserSession, farm: str, field: str) -> Field:
    """## Delete a field within a given farm by their IDs or names."""
    field_rec = get_farm_field(db, farm, field)
    return crud.field.delete(db, field_rec)


# endregion
