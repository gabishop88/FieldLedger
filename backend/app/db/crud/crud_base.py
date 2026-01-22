# To perform CRUD operations, it is recommended to: `from app.db import crud` -> `crud.tablename.operation()`

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel

from app.api.messages import ExeMsg


class CRUDBase[ModelType: SQLModel, CreateType: SQLModel, UpdateType: SQLModel]:
    """### Superclass for CRUD Operations on tables.
    For now, there are no READ operations defined since Session.get and Session.exec are
    so easy to use for those operations.

    If you want to query a table, instead of `crud.table.get(db, ...)`, use:

    `db.get(Table, pk)`, or `db.exec(select(Table).where()).first()`
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    def _safe_add(self, db: Session, obj: ModelType) -> ModelType:
        try:
            db.add(obj)
            db.flush()
            db.refresh(obj)
            return obj
        except IntegrityError as e:
            # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
            msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
            # TODO: Relying on msg contents to detect unique violation is unstable. However, I can't find the "pgcode" or similar to do this properly.
            if "already exists" in msg:  # Unique/exclusion violation
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            # FK, NOTNULL, Check, etc.
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    def _safe_delete(self, db: Session, obj: ModelType) -> ModelType:
        try:
            db.delete(obj)
            db.flush()
            return obj
        except IntegrityError as e:
            # Safely get e.orig.diag.message_detail, or fall back to str(e.orig)
            msg = str(getattr(getattr(e.orig, "diag", None), "message_detail", e.orig))
            if getattr(e.orig, "pgcode", None) in ("23503",):  # FK constraint
                raise HTTPException(status.HTTP_409_CONFLICT, msg)
            # delete fails for any other reason
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, msg)

    # ---------------- CREATE ----------------

    def create(self, db: Session, new_record: CreateType) -> ModelType:
        db_obj = self.model.model_validate(new_record)
        self._safe_add(db, db_obj)
        return db_obj

    # ----------------- READ -----------------

    def get_or_raise(self, db: Session, key: Any) -> ModelType:
        """## Get one record or raise HTTPException(404) if not found."""
        record = db.get(self.model, key)
        if not record:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                ExeMsg.NF_TABLE_KEY.format(self.model.__name__, key),
            )
        return record

    # ---------------- UPDATE ----------------

    def update(self, db: Session, record: ModelType, changes: UpdateType) -> ModelType:
        """## Modify the selected `record` with the provided `changes`."""
        update_dict = changes.model_dump(exclude_unset=True)
        record.sqlmodel_update(update_dict)
        return self._safe_add(db, record)

    # ---------------- DELETE ----------------

    def delete(self, db: Session, record: ModelType) -> ModelType:
        """## Deletes the given `record` and returns it (as it was before deletion)."""
        return self._safe_delete(db, record)
