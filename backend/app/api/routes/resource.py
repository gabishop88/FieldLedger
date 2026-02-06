from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ReadSession, UserSession
from app.core.enums import DocTag
from app.db import crud
from app.db.models import (
    Equipment,
    EquipmentCreate,
    EquipmentUpdate,
    Paginated,
    Product,
    ProductCreate,
    ProductUpdate,
)

equipment_router = APIRouter(tags=[DocTag.RES_EQIP])
product_router = APIRouter(tags=[DocTag.RES_PROD])

router = APIRouter()  # Combine routers at the end (after endpoints are added)

# region ---------------------------- Equipment Endpoints -----------------------------


@equipment_router.get("/orgs/{id}/equipment", response_model=Paginated[Equipment])
def list_org_equipment(db: ReadSession, id: UUID, skip: int = 0, limit: int = 10):
    org = crud.org.get_or_raise(db, id)
    return crud.equipment.get_paginated(db, skip, limit, Equipment.org_id == org.id)


@equipment_router.post("/equipment", response_model=Equipment)
def create_equipment(db: UserSession, data_in: EquipmentCreate):
    return crud.equipment.create(db, data_in)


@equipment_router.get("/equipment/{id}", response_model=Equipment)
def get_eqiuipment(db: ReadSession, id: UUID):
    return crud.equipment.get_or_raise(db, id)


@equipment_router.patch("/equipment/{id}", response_model=Equipment)
def edit_equipment(db: UserSession, id: UUID, data_in: EquipmentUpdate):
    record = crud.equipment.get_or_raise(db, id)
    return crud.equipment.update(db, record, data_in)


@equipment_router.delete("/equipment/{id}", response_model=Equipment)
def delete_equipment(db: UserSession, id: UUID):
    record = crud.equipment.get_or_raise(db, id)
    return crud.equipment.delete(db, record)


# endregion
# region ----------------------------- Product Endpoints ------------------------------


@product_router.get("/orgs/{id}/products", response_model=Paginated[Product])
def list_org_products(db: ReadSession, id: UUID, skip: int = 0, limit: int = 10):
    org = crud.org.get_or_raise(db, id)
    return crud.product.get_paginated(db, skip, limit, Product.org_id == org.id)


@product_router.post("/products", response_model=Product)
def create_product(db: UserSession, data_in: ProductCreate):
    return crud.product.create(db, data_in)


@product_router.get("/products/{id}", response_model=Product)
def get_product(db: ReadSession, id: UUID):
    return crud.product.get_or_raise(db, id)


@product_router.patch("/products/{id}", response_model=Product)
def edit_product(db: UserSession, id: UUID, data_in: ProductUpdate):
    record = crud.product.get_or_raise(db, id)
    return crud.product.update(db, record, data_in)


@product_router.delete("/products/{id}", response_model=Product)
def delete_product(db: UserSession, id: UUID):
    record = crud.product.get_or_raise(db, id)
    return crud.product.delete(db, record)


# endregion

router.include_router(equipment_router)
router.include_router(product_router)
