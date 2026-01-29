# To perform CRUD ops: `from app.db import crud` -> `crud.tablename.operation()`

from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, InternalError
from sqlmodel import Session, SQLModel, func, select

from app.api.messages import ExeMsg
from app.db.models import Paginated


class CRUDBase[ModelType: SQLModel, CreateType: SQLModel, UpdateType: SQLModel]:
    """### Superclass for CRUD Operations on tables.
    For now, there are no READ operations defined since Session.get and Session.exec are
    so easy to use for those operations.

    If you want to query a table, instead of `crud.table.get(db, ...)`, use:

    `db.get(Table, pk)`, or `db.exec(select(Table).where()).first()`
    """

    def __init__(self, model: type[ModelType] | None = None):
        self.model: type[ModelType] | None = model

    def _safe_add(
        self, db: Session, objs: Sequence[ModelType], refresh=False
    ) -> Sequence[ModelType]:
        try:
            db.add_all(objs)
            db.flush()
            if refresh:
                for obj in objs:
                    db.refresh(obj)
            return objs
        except (IntegrityError, InternalError) as e:
            db.rollback()
            # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
            msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
            # TODO: Relying on msg contents to detect unique violation is unstable.
            # However, I can't find the "pgcode" or similar to do this properly.
            if "already exists" in msg:  # Unique/exclusion violation
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            # FK, NOTNULL, Check, etc.
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    def _safe_delete(self, db: Session, obj: ModelType) -> ModelType:
        try:
            db.delete(obj)
            db.flush()
            return obj
        except (IntegrityError, InternalError) as e:
            db.rollback()
            # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
            msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
            if getattr(e.orig, "pgcode", None) in ("23503",):  # FK constraint
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            # delete fails for any other reason
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    # ---------------- CREATE ----------------

    def create(self, db: Session, new_record: CreateType) -> ModelType:
        assert self.model is not None, "Cannot create record: model is not set."
        db_obj = self.model.model_validate(new_record)
        self._safe_add(db, [db_obj])
        return db_obj

    def create_multiple(
        self, db: Session, new_records: Sequence[CreateType]
    ) -> Sequence[ModelType]:
        assert self.model is not None, "Cannot create records: model is not set."
        db_objs = [self.model.model_validate(rec) for rec in new_records]
        self._safe_add(db, db_objs)
        return db_objs

    # ----------------- READ -----------------

    def get_or_raise(self, db: Session, key: Any) -> ModelType:
        """### Get one record or raise HTTPException(404) if not found."""
        assert self.model is not None, "Cannot get record: model is not set."
        record = db.get(self.model, key)
        if not record:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                ExeMsg.NF.format(self.model.__name__, key),
            )
        return record

    def get_paginated(
        self, db: Session, skip, limit, *filters, order_by=None
    ) -> Paginated[ModelType]:
        assert self.model is not None, "Cannot get paginated records: model is not set."
        query = select(self.model).where(*filters).offset(skip).limit(limit)
        if order_by is not None:
            query = query.order_by(order_by)

        return Paginated(
            count=db.exec(
                select(func.count()).select_from(self.model).where(*filters)
            ).one(),
            data=db.exec(query).all(),
        )

    # ---------------- UPDATE ----------------

    def update(self, db: Session, record: ModelType, changes: UpdateType) -> ModelType:
        """### Modify the selected `record` with the provided `changes`."""
        update_dict = changes.model_dump(exclude_unset=True)
        record.sqlmodel_update(update_dict)
        self._safe_add(db, [record], refresh=True)
        return record

    # ---------------- DELETE ----------------

    def delete(self, db: Session, record: ModelType) -> ModelType:
        """### Deletes the given `record` and returns it (as it was before deletion)."""
        return self._safe_delete(db, record)
