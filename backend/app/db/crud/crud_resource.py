from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    Equipment,
    EquipmentCreate,
    EquipmentUpdate,
    Product,
    ProductCreate,
    ProductUpdate,
)


class CRUDEquipment(CRUDBase[Equipment, EquipmentCreate, EquipmentUpdate]):
    pass


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    pass


equipment = CRUDEquipment(Equipment)
product = CRUDProduct(Product)
