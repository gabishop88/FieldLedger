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


class RefTables(StrEnum, metaclass=DynamicStrEnumMeta, vals=get_table_names()): ...


class CRUDRef(CRUDBase[ModelType, ReferenceCreate, ReferenceUpdate]):
    """## One CRUD object for all reference tables.
    To edit a reference table, provide table argument: `crud.ref.create(..., table)`

    Any value in the Enum `RefTables` is a valid value for `table` in any CRUD function.
    """

    def __init__(self):
        super().__init__(None)  # type: ignore

    @contextmanager
    def _use_model(self, tbl: RefTables) -> Generator[None, None, None]:
        """## Operations performed by `crud.ref` in this context apply to `table`.
        > Note: `all functions` use this internally when you provide `table`.

        e.g.
        ```
        # Uses crud.ref.model directly, so use _use_model
        with crud.ref._use_model(table):
            db.exec(select(crud.ref.model)).all()

        # Internal methods call _use_model internally, so no need to do so yourself
        crud.ref.update(db, table, record, changes)
        ```
        """
        if tbl not in RefTables:
            raise HTTPException(status.HTTP_404_NOT_FOUND, ExeMsg.NF_TABLE.format(tbl))
        try:
            self.model = getattr(models, tbl)
            yield
        finally:
            self.model = None

    def create(
        self, db: Session, new_record: ReferenceCreate, table: RefTables | None = None
    ) -> ModelType:
        if table is None:
            raise RuntimeError("Reference table is not set. Provide `table` argument.")
        with self._use_model(table):
            return super().create(db, new_record)

    def get_or_raise(
        self, db: Session, key: Any, table: RefTables | None = None
    ) -> ModelType:
        if table is None:
            raise RuntimeError("Reference table is not set. Provide `table` argument.")
        with self._use_model(table):
            return super().get_or_raise(db, key)

    def update(
        self,
        db: Session,
        record: ModelType,
        changes: ReferenceUpdate,
        table: RefTables | None = None,
    ) -> ModelType:
        if table is None:
            raise RuntimeError("Reference table is not set. Provide `table` argument.")
        with self._use_model(table):
            return super().update(db, record, changes)

    def delete(
        self, db: Session, record: ModelType, table: RefTables | None = None
    ) -> ModelType:
        if table is None:
            raise RuntimeError("Reference table is not set. Provide `table` argument.")
        with self._use_model(table):
            return super().delete(db, record)


ref = CRUDRef()
