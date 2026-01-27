from app.db.crud.crud_base import CRUDBase
from app.db.models import Farm, FarmCreate, FarmUpdate, Field, FieldUpdate


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    pass


class CRUDField(CRUDBase[Field, Field, FieldUpdate]):
    pass


farm = CRUDFarm(Farm)
field = CRUDField(Field)
