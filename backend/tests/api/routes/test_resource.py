from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.models import (
    EquipmentCreate,
    EquipmentUpdate,
    OrgCreate,
    ProductCreate,
    ProductUpdate,
)
from app.core.config import settings
from app.core.enums import EquipmentType, ErrMsg, ProductType
from app.db import crud
from app.db.models import Equipment, Product
from tests.utils.rng import generate_str

PFIX = settings.API_PREFIX


# region --------------------------- Equipment CRUD ---------------------------


def test_create_equipment(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    eq_in = EquipmentCreate(name=generate_str(seed + 1), type=EquipmentType.Tractor)

    res = cli.post(
        f"{PFIX}/orgs/{org.id}/equipment",
        json=eq_in.model_dump(mode="json"),
        headers=user_head,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == eq_in.name
    assert body["org_id"] == str(org.id)

    assert db.get(Equipment, body["id"])


def test_get_equipment(cli: TestClient, db: Session, seed: int):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    eq = crud.equipment.create(
        db,
        Equipment(
            name=generate_str(seed + 1), org_id=org.id, type=EquipmentType.Tractor
        ),
    )

    res = cli.get(f"{PFIX}/equipment/{eq.id}")
    assert res.status_code == 200
    assert res.json()["id"] == str(eq.id)

    bad_id = uuid4()
    res = cli.get(f"{PFIX}/equipment/{bad_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == ErrMsg.NF.format("Equipment", bad_id)


def test_list_org_equipment(cli: TestClient, db: Session, seed: int):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    other = crud.org.create(db, OrgCreate(name=generate_str(seed + 1)))

    eqs = [
        crud.equipment.create(
            db,
            Equipment(
                name=generate_str(seed + i), org_id=org.id, type=EquipmentType.Rake
            ),
        )
        for i in range(3)
    ]
    crud.equipment.create(
        db, Equipment(name="other", org_id=other.id, type=EquipmentType.Misc)
    )

    res = cli.get(f"{PFIX}/orgs/{org.id}/equipment")
    assert res.status_code == 200
    assert res.json()["count"] == 3
    returned_ids = {item["id"] for item in res.json()["data"]}
    assert all(str(e.id) in returned_ids for e in eqs)


def test_update_equipment(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    eq = crud.equipment.create(
        db, Equipment(name="old", org_id=org.id, type=EquipmentType.Harvester)
    )

    edits = EquipmentUpdate(name="new").model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/equipment/{eq.id}", json=edits, headers=user_head)
    assert res.status_code == 200
    assert res.json()["name"] == "new"


def test_delete_equipment(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    eq = crud.equipment.create(
        db, Equipment(name="x", org_id=org.id, type=EquipmentType.Header)
    )

    res = cli.delete(f"{PFIX}/equipment/{eq.id}", headers=user_head)
    assert res.status_code == 200
    assert db.get(Equipment, eq.id) is None


# endregion
# region --------------------------- Product CRUD ---------------------------


def test_create_product(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    prod_in = ProductCreate(name=generate_str(seed + 1), type=ProductType.Adjuvant)

    res = cli.post(
        f"{PFIX}/orgs/{org.id}/products",
        json=prod_in.model_dump(mode="json"),
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()["org_id"] == str(org.id)


def test_get_product(cli: TestClient, db: Session, seed: int):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    prod = crud.product.create(
        db, Product(name="p", org_id=org.id, type=ProductType.Water)
    )

    res = cli.get(f"{PFIX}/products/{prod.id}")
    assert res.status_code == 200

    bad = uuid4()
    res = cli.get(f"{PFIX}/products/{bad}")
    assert res.status_code == 404


def test_list_org_products(cli: TestClient, db: Session, seed: int):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    crud.product.create(db, Product(name="a", org_id=org.id, type=ProductType.Bioinput))
    crud.product.create(db, Product(name="b", org_id=org.id, type=ProductType.Seed))

    res = cli.get(f"{PFIX}/orgs/{org.id}/products")
    assert res.status_code == 200
    assert res.json()["count"] == 2


def test_update_product(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    prod = crud.product.create(
        db, Product(name="old", org_id=org.id, type=ProductType.Fungicide)
    )

    res = cli.patch(
        f"{PFIX}/products/{prod.id}",
        json=ProductUpdate(name="new").model_dump(exclude_unset=True),
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "new"


def test_delete_product(cli: TestClient, db: Session, seed: int, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    prod = crud.product.create(
        db, Product(name="x", org_id=org.id, type=ProductType.Manure)
    )

    res = cli.delete(f"{PFIX}/products/{prod.id}", headers=user_head)
    assert res.status_code == 200
    assert db.get(Product, prod.id) is None


# endregion
