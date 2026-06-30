from sqlmodel import Session, func

from app.db.crud.crud_base import CRUDBase
from app.db.models import Crop, CropUpdate, Unit, UnitUpdate


class CRUDCrop(CRUDBase[Crop, Crop, CropUpdate]):
    def get_first_similar_name(
        self, db: Session, crop_name: str | None, threshold=0.3
    ) -> Crop | None:
        if crop_name is None:
            return None

        similarity = func.similarity(Crop.common_name, crop_name)
        return self.get_first(db, similarity > threshold, order_by=similarity.desc())


class CRUDUnit(CRUDBase[Unit, Unit, UnitUpdate]):
    pass


crop = CRUDCrop(Crop)
unit = CRUDUnit(Unit)
