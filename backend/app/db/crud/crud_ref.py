import re
from collections.abc import Generator
from contextlib import contextmanager
from enum import EnumMeta, StrEnum, _EnumDict
from typing import Any, TypeVar

from fastapi import HTTPException, status
from sqlmodel import Session, SQLModel, inspect

from app.api.messages import ExeMsg
from app.core.config import settings
from app.db import models
from app.db.connection import get_engine
from app.db.crud.crud_base import CRUDBase
from app.db.models import ReferenceCreate, ReferenceUpdate

PASCALIZER = re.compile(r"(^|_)([a-z])")

ModelType = TypeVar("ModelType", bound=SQLModel)


def pascalize(s: str) -> str:
    """Transform a (usually snake_case) string into PascalCase."""
    if s is None:
        return None
    return PASCALIZER.sub(lambda m: m.group(2).upper(), s)


def get_table_names(schema: str = "ref") -> list[str]:
    with Session(get_engine(settings.READONLY_DATABASE_URI)) as db:
        tables = inspect(db.bind).get_table_names(schema=schema)  # type: ignore
        return list(map(pascalize, tables))


class DynamicStrEnumMeta(EnumMeta):
    """## StrEnum metaclass dynamically filled at runtime."""

    def __new__(mcls, name, bases, dct: _EnumDict, vals: list[str]):
        if vals:
            dct.update({v: v for v in vals})
        return super().__new__(mcls, name, bases, dct)


class RefTable(StrEnum, metaclass=DynamicStrEnumMeta, vals=get_table_names()): ...


class CRUDRef(CRUDBase[ModelType, ReferenceCreate, ReferenceUpdate]):
    """## One CRUD object for all reference tables.
    To edit a reference table, just provide the table as an argument: `crud.ref.create(table, ...)`

    Any value in the Enum `RefTable` is a valid value for `table` in any CRUD function.
    """

    def __init__(self):
        super().__init__(None)  # type: ignore

    @contextmanager
    def _use_model(self, tbl: RefTable) -> Generator[None, None, None]:
        """Operations performed by `crud.ref` in this context use provided table model.
        > Note: `crud.ref.create, update, delete` use this internally, just give them `table`.

        e.g.
        ```
        # Uses crud.ref.model directly, so use _use_model
        with crud.ref._use_model(table):
            db.exec(select(crud.ref.model)).all()

        # Internal methods call _use_model internally, so no need to do so yourself
        crud.ref.update(db, table, record, changes)
        ```
        """
        if tbl not in RefTable:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ExeMsg.NF_TABLE.format(tbl))
        try:
            self.model = getattr(models, tbl)
            yield
        finally:
            self.model = None

    def create(
        self, db: Session, table: RefTable, new_record: ReferenceCreate
    ) -> ModelType:
        with self._use_model(table):
            return super().create(db, new_record)

    def get_or_raise(self, db: Session, table: RefTable, key: Any) -> ModelType:
        with self._use_model(table):
            return super().get_or_raise(db, key)

    def update(
        self, db: Session, table: RefTable, record: ModelType, changes: ReferenceUpdate
    ) -> ModelType:
        with self._use_model(table):
            return super().update(db, record, changes)

    def delete(self, db: Session, table: RefTable, record: ModelType) -> ModelType:
        with self._use_model(table):
            return super().delete(db, record)


ref = CRUDRef()
