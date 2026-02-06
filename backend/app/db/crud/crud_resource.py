from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    Equipment,
    EquipmentBase,
    EquipmentUpdate,
    Product,
    ProductBase,
    ProductUpdate,
)


class CRUDEquipment(CRUDBase[Equipment, EquipmentBase, EquipmentUpdate]):
    pass


class CRUDProduct(CRUDBase[Product, ProductBase, ProductUpdate]):
    pass


equipment = CRUDEquipment(Equipment)
product = CRUDProduct(Product)
