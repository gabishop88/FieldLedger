from sqlmodel import Session, select

from app.db.crud.crud_base import CRUDBase
from app.db.models import Farm, FarmCreate, FarmUpdate


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    def get_by_name(self, db: Session, name: str):
        return db.exec(select(Farm).where(Farm.name == name)).first()


farm = CRUDFarm(Farm)
