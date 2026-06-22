import re
from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import Session, func, inspect, select

from app.api.deps import ReadSession, SuperuserSession
from app.core import enums
from app.core.config import settings
from app.core.enums import ErrMsg, LoadStrEnumMeta, TypeEnum
from app.db import crud, models
from app.db.connection import get_engine
from app.db.models import (
    AnyReferencePublic,
    Crop,
    CropUpdate,
    Paginated,
    Unit,
    UnitUpdate,
)

router = APIRouter(prefix="/ref")

LIM = settings.DEFAULT_PAGE_LIMIT
PASCALIZER = re.compile(r"(^|_)([a-z])")


# TODO: This probably belongs in app/core or something?
def pascalize(s: str) -> str:
    """Transform a (usually snake_case) string into PascalCase."""
    if s is None:
        return None
    return PASCALIZER.sub(lambda m: m.group(2).upper(), s)


def list_db_ref_tables() -> list[str]:
    with Session(get_engine(settings.READONLY_DATABASE_URI)) as db:
        tables = inspect(db.bind).get_table_names(schema="ref")  # type: ignore
        return list(map(pascalize, tables))


def list_enum_ref_tables() -> list[str]:
    return [c.__name__ for c in TypeEnum.__subclasses__()]


db_refs = list_db_ref_tables()
enum_refs = list_enum_ref_tables()


class RefTables(StrEnum, metaclass=LoadStrEnumMeta, vals=db_refs + enum_refs):
    pass


@router.get("/tables", response_model=list[str])
def list_reference_tables():
    return db_refs + enum_refs


@router.get("/{table}", response_model=Paginated[AnyReferencePublic])
def list_reference_values(
    db: ReadSession, table: RefTables, skip: int = 0, limit: int | None = LIM
):
    if table in ("Crop", "Unit"):
        sel_count = select(func.count()).select_from(getattr(models, table))
        sel_data = select(getattr(models, table)).offset(skip).limit(limit)
        return Paginated(count=db.exec(sel_count).one(), data=db.exec(sel_data).all())

    data = getattr(enums, table).asdict()
    return Paginated(
        count=len(data), data=data[skip : skip + limit if limit is not None else None]
    )


@router.post("/crop", response_model=Crop)
def add_crop(db: SuperuserSession, new: Crop):
    return crud.crop.create(db, new)


@router.patch("/crop/{id}", response_model=Crop)
def edit_crop(db: SuperuserSession, id: UUID, edits: CropUpdate):
    crop = db.get(Crop, id)
    if crop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Crop", id))
    return crud.crop.update(db, crop, edits)


@router.delete("/crop/{id}", response_model=Crop)
def delete_crop(db: SuperuserSession, id: UUID):
    crop = db.get(Crop, id)
    if crop is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Crop", id))
    return crud.crop.delete(db, crop)


@router.post("/unit", response_model=Unit)
def add_unit(db: SuperuserSession, new: Unit):
    return crud.unit.create(db, new)


@router.patch("/unit/{name}", response_model=Unit)
def edit_unit(db: SuperuserSession, name: str, edits: UnitUpdate):
    unit = db.get(Unit, name)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Unit", name))
    return crud.unit.update(db, unit, edits)


@router.delete("/unit/{name}", response_model=Unit)
def delete_unit(db: SuperuserSession, name: str):
    unit = db.get(Unit, name)
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format("Unit", name))
    return crud.unit.delete(db, unit)
