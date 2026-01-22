from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import ReadSession, SuperuserSession
from app.db import crud
from app.db.crud.crud_ref import RefTable, get_table_names
from app.db.models import (
    ReferenceCreate,
    ReferencePublic,
    ReferencesPublic,
    ReferenceUpdate,
)

router = APIRouter(prefix="/ref")


@router.get("/tables", response_model=list[str])
def list_reference_tables():
    return get_table_names()


@router.get("/{table}", response_model=ReferencesPublic)
def list_reference_values(db: ReadSession, table: RefTable):
    with crud.ref._use_model(table):
        return db.exec(select(crud.ref.model)).all()


@router.put("/{table}", response_model=ReferencePublic)
def add_reference_value(db: SuperuserSession, table: RefTable, new: ReferenceCreate):
    return crud.ref.create(db, table, new)


@router.patch("/{table}/{key}", response_model=ReferencePublic)
def update_reference_value(
    db: SuperuserSession, table: RefTable, key: str, changes: ReferenceUpdate
):
    record = crud.ref.get_or_raise(db, table, key)
    return crud.ref.update(db, table, record, changes)


@router.delete("/{table}/{key}", response_model=ReferencePublic)
def delete_reference_value(db: SuperuserSession, table: RefTable, key: str):
    record = crud.ref.get_or_raise(db, table, key)
    return crud.ref.delete(db, table, record)
