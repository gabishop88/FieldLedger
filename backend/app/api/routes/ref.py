from fastapi import APIRouter

from app.api.deps import ReadSession, SuperuserSession
from app.db import crud
from app.db.crud.crud_ref import RefTables, get_table_names
from app.db.models import Paginated, ReferenceCreate, ReferencePublic, ReferenceUpdate

router = APIRouter(prefix="/ref")


@router.get("/tables", response_model=list[str])
def list_reference_tables():
    return get_table_names()


@router.get("/{table}", response_model=Paginated[ReferencePublic])
def list_reference_values(db: ReadSession, table: RefTables, skip=0, limit=10):
    return crud.ref.get_paginated(db, skip, limit, table=table)


@router.post("/{table}", response_model=ReferencePublic)
def add_reference_value(db: SuperuserSession, table: RefTables, new: ReferenceCreate):
    return crud.ref.create(db, new, table)


@router.patch("/{table}/{key}", response_model=ReferencePublic)
def update_reference_value(
    db: SuperuserSession, table: RefTables, key: str, changes: ReferenceUpdate
):
    record = crud.ref.get_or_raise(db, key, table)
    return crud.ref.update(db, record, changes, table)


@router.delete("/{table}/{key}", response_model=ReferencePublic)
def delete_reference_value(db: SuperuserSession, table: RefTables, key: str):
    record = crud.ref.get_or_raise(db, key, table)
    return crud.ref.delete(db, record, table)
