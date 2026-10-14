from app.api.models import EquipmentUpdate, ProductUpdate
from app.db.crud.crud_base import CRUDBase
from app.db.models import Equipment, Product


class CRUDEquipment(CRUDBase[Equipment, Equipment, EquipmentUpdate]):
    pass


class CRUDProduct(CRUDBase[Product, Product, ProductUpdate]):
    pass


equipment = CRUDEquipment(Equipment)
product = CRUDProduct(Product)
