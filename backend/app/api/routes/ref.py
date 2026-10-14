from enum import StrEnum
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import ReadSession, SuperuserSession
from app.api.models import AnyReferencePublic, CropUpdate, Paginated, UnitUpdate
from app.core import enums
from app.core.config import settings
from app.core.enums import DynamicEnumMeta, ErrMsg, list_col_enums
from app.db import crud, models
from app.db.connection import list_tables
from app.db.models import Crop, Unit

LIM = settings.DEFAULT_PAGE_LIMIT

router = APIRouter(prefix="/ref")
ref_tables = list_col_enums() + list_tables("ref", pascal=True)


class RefTable(StrEnum, metaclass=DynamicEnumMeta, vals=ref_tables):
    pass


@router.get("/tables", response_model=list[str])
def list_reference_tables():
    return ref_tables


@router.get("/{table}", response_model=Paginated[AnyReferencePublic])
def list_reference_values(
    db: ReadSession, table: RefTable, skip: int = 0, limit: int | None = LIM
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
