from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.db.crud.crud_base import CRUDBase
from app.db.models import JDConnection, JDConnectionUpdate, JDLinkUpdate, JDRecordLink


class CRUDJDConnection(CRUDBase[JDConnection, JDConnection, JDConnectionUpdate]):
    pass


class CRUDJDRecordLink(CRUDBase[JDRecordLink, JDRecordLink, JDLinkUpdate]):
    def get_trees_paginated(
        self, db: Session, user_id: UUID, skip: int = 0, limit: int | None = None
    ):
        filters = [JDRecordLink.user_id == user_id, JDRecordLink.parent is None]
        return self.get_paginated(db, skip, limit, *filters)

    def get_by_link(self, db: Session, user_id: UUID, link: str) -> JDRecordLink | None:
        filters = [JDRecordLink.user_id == user_id, JDRecordLink.link == link]
        count_query = select(func.count()).select_from(JDRecordLink).where(*filters)
        if db.exec(count_query).one() > 1:
            raise HTTPException(status.HTTP_409_CONFLICT)
        return db.exec(select(JDRecordLink).where(*filters)).first()


jd_connection = CRUDJDConnection(JDConnection)
jd_link = CRUDJDRecordLink(JDRecordLink)
