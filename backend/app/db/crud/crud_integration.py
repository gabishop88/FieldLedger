from app.db.crud.crud_base import CRUDBase
from app.db.models import JDConnection, JDRecordLink


class CRUDJDConnection(CRUDBase[JDConnection, JDConnection, JDConnection]):
    pass


class CRUDJDRecordLink(CRUDBase[JDRecordLink, JDRecordLink, JDRecordLink]):
    pass


jd_connection = CRUDJDConnection(JDConnection)
jd_link = CRUDJDRecordLink(JDRecordLink)
