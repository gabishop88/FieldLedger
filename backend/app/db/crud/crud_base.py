# To perform CRUD operations, it is recommended to: `from app.db import crud` -> `crud.tablename.operation()`

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel


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
        db.add(obj)
        try:
            db.flush()
            db.refresh(obj)
        except IntegrityError as e:
            detail = e.orig
            if hasattr(detail, "diag"):
                detail = detail.diag.message_detail  # type: ignore
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail)
        return obj

    # ---------------- CREATE ----------------

    def create(self, db: Session, new_record: CreateType) -> ModelType:
        db_obj = self.model.model_validate(new_record)
        self._safe_add(db, db_obj)
        return db_obj

    # ---------------- UPDATE ----------------

    def update(self, db: Session, record: ModelType, changes: UpdateType) -> ModelType:
        """Modify the selected `record` with the provided `changes`."""
        update_dict = changes.model_dump(exclude_unset=True)
        record.sqlmodel_update(update_dict)
        self._safe_add(db, record)
        return record

    # ---------------- DELETE ----------------

    def delete(self, db: Session, record: ModelType) -> ModelType | None:
        """Deletes the given `record`. Returns it if deleted, returns `None` if nothing was deleted."""
        db.delete(record)
        db.flush()
        return record
