# To perform CRUD ops: `from app.db import crud` -> `crud.tablename.operation()`

from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, InternalError
from sqlmodel import Session, SQLModel, func, select

from app.api.models import Paginated
from app.core.enums import ErrMsg

# TODO: improved/standalone create/delete functions that take 1+ objs:
# def create(self, db: Session, *objs: CreateType) -> tuple[ModelType, ...]:
#     try:
#         obj_models = tuple(self._validate(o) for o in objs)
#         db.add_all(obj_models)
#         db.flush()
#         return obj_models
#     except (IntegrityError, InternalError) as e:
#         db.rollback()
#         # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
#         msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
#         if "already exists" in msg:  # Unique/exclusion violation
#             raise HTTPException(status.HTTP_409_CONFLICT, msg)
#         raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

class CRUDBase[ModelType: SQLModel, CreateType: SQLModel, UpdateType: SQLModel]:
    """### Superclass for CRUD Operations on tables.
    For now, there are no READ operations defined since Session.get and Session.exec are
    so easy to use for those operations.

    If you want to query a table, instead of `crud.table.get(db, ...)`, use:

    `db.get(Table, pk)`, or `db.exec(select(Table).where()).first()`
    """

    def __init__(self, model: type[ModelType] | None = None):
        self.model: type[ModelType] | None = model

    def _ensure_model_exists(self) -> type[ModelType]:
        if self.model is None:
            raise RuntimeError("CRUD functions cannot be executed without a model.")
        return self.model

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
            if "already exists" in msg:  # Unique/exclusion violation
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    def _safe_delete(
        self, db: Session, objs: Sequence[ModelType]
    ) -> Sequence[ModelType]:
        try:
            for obj in objs:
                db.delete(obj)
            db.flush()
            return objs
        except (IntegrityError, InternalError) as e:
            db.rollback()
            # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
            msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
            if getattr(e.orig, "pgcode", None) in ("23503",):  # FK constraint
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    def _validate(self, obj: ModelType | CreateType | UpdateType) -> ModelType:
        """Make sure that an object is an instance of ModelType."""
        self.model = self._ensure_model_exists()
        if isinstance(obj, self.model):
            return obj
        return self.model.model_validate(obj)

    # ---------------- CREATE ----------------

    def create(self, db: Session, new_record: CreateType) -> ModelType:
        return self.create_multiple(db, [new_record])[0]

    def create_multiple(self, db: Session, new_records: Sequence[CreateType]
    ) -> Sequence[ModelType]:
        model_objs = [self._validate(obj) for obj in new_records]
        self._safe_add(db, model_objs)
        return model_objs

    # ----------------- READ -----------------

    def get_or_raise(self, db: Session, key: Any) -> ModelType:
        """### Get one record or raise HTTPException(404) if not found."""
        self.model = self._ensure_model_exists()
        record = db.get(self.model, key)
        if not record:
            table = self.model.__name__
            raise HTTPException(status.HTTP_404_NOT_FOUND, ErrMsg.NF.format(table, key))
        return record

    def get_first(self, db: Session, *filters, order_by=None) -> ModelType | None:
        """Similar to `get_paginated` but only get the first record, if it exists."""
        self.model = self._ensure_model_exists()
        query = select(self.model).where(*filters)
        query = query if order_by is None else query.order_by(order_by)
        return db.exec(query).first()

    def get_paginated(
        self, db: Session, skip: int, limit: int | None, *filters, order_by=None
    ) -> Paginated[ModelType]:
        self.model = self._ensure_model_exists()
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
        db.flush()
        return record

    # ---------------- DELETE ----------------

    def delete(self, db: Session, record: ModelType) -> ModelType:
        """### Deletes the given `record` and returns it (as it was before deletion)."""
        return self._safe_delete(db, [record])[0]

    def delete_multiple(
        self, db: Session, records: Sequence[ModelType]
    ) -> Sequence[ModelType]:
        return self._safe_delete(db, records)
