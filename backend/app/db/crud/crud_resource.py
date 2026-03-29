from app.db.crud.crud_base import CRUDBase
from app.db.models import Equipment, EquipmentUpdate, Product, ProductUpdate


class CRUDEquipment(CRUDBase[Equipment, Equipment, EquipmentUpdate]):
    pass


class CRUDProduct(CRUDBase[Product, Product, ProductUpdate]):
    pass


equipment = CRUDEquipment(Equipment)
product = CRUDProduct(Product)
