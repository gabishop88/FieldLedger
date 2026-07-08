from collections.abc import Sequence
from typing import ClassVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic_core import to_jsonable_python
from sqlmodel import Session, func, select

from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    JDConnection,
    JDConnectionUpdate,
    JDLinkUpdate,
    JDRecordLink,
    SyncLinkUpdate,
)

LinkUpdate = JDLinkUpdate | SyncLinkUpdate


class CRUDJDConnection(CRUDBase[JDConnection, JDConnection, JDConnectionUpdate]):
    pass


class CRUDJDRecordLink(CRUDBase[JDRecordLink, JDRecordLink, LinkUpdate]):
    dict_fields: ClassVar[set[str]] = {"data", "table_key"}

    def _safe_add(
        self, db: Session, objs: Sequence[JDRecordLink], refresh=False
    ) -> Sequence[JDRecordLink]:
        for obj in objs:
            for key in self.dict_fields:
                if hasattr(obj, key):
                    setattr(obj, key, to_jsonable_python(getattr(obj, key)))
        return super()._safe_add(db, objs, refresh)

    def get_trees_paginated(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int | None = None
    ):
        # NOTE: Must use `== None`, not `is None` because `==` operator makes a filter.
        filters = [JDRecordLink.user_id == user_id, JDRecordLink.parent_id == None]  # noqa: E711
        return self.get_paginated(db, skip, limit, *filters)

    def get_by_user_and_uri(
        self, db: Session, user_id: UUID, uri: str
    ) -> JDRecordLink | None:
        filters = [JDRecordLink.user_id == user_id, JDRecordLink.uri == uri]
        count_query = select(func.count()).select_from(JDRecordLink).where(*filters)
        if db.exec(count_query).one() > 1:
            raise HTTPException(status.HTTP_409_CONFLICT)
        return db.exec(select(JDRecordLink).where(*filters)).first()

    def update(
        self, db: Session, record: JDRecordLink, changes: LinkUpdate
    ) -> JDRecordLink:
        # Make dict fields jsonable
        for key in self.dict_fields:
            if getattr(changes, key, None):
                setattr(changes, key, to_jsonable_python(getattr(changes, key)))
        return super().update(db, record, changes)


jd_connection = CRUDJDConnection(JDConnection)
jd_link = CRUDJDRecordLink(JDRecordLink)
