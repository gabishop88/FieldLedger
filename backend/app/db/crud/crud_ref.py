from app.db.crud.crud_base import CRUDBase
from app.db.models import Crop, CropUpdate, Unit, UnitUpdate


class CRUDCrop(CRUDBase[Crop, Crop, CropUpdate]):
    pass


class CRUDUnit(CRUDBase[Unit, Unit, UnitUpdate]):
    pass


crop = CRUDCrop(Crop)
unit = CRUDUnit(Unit)
