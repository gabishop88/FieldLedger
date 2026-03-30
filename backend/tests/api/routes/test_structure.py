from uuid import UUID, uuid4

from app.core.config import settings
from app.core.enums import BoundaryType, FieldType, OrgFarmType
from app.db import crud
from app.db.models import (
    BoundaryCreate,
    Farm,
    FarmCreate,
    Field,
    FieldBoundary,
    FieldCreate,
    Org,
    OrgCreate,
    OrgFarm,
)
from tests.utils.rng import generate_geom, generate_str

PFIX = settings.API_PREFIX


def test_create_org(cli, db, seed, user_head):
    data = {"name": generate_str(seed)}
    res = cli.post(f"{PFIX}/orgs", json=data, headers=user_head)
    assert res.status_code == 200
    assert res.json()["name"] == data["name"]
    assert db.get(Org, res.json()["id"])


def test_get_org(cli, db, seed):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    res = cli.get(f"{PFIX}/orgs/{org.id}")
    assert res.status_code == 200
    assert res.json()["id"] == str(org.id)


def test_delete_org(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    res = cli.delete(f"{PFIX}/orgs/{org.id}", headers=user_head)
    assert res.status_code == 200
    assert db.get(Org, org.id) is None


def test_create_farm_under_org(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm_in = {"name": generate_str(seed + 1)}

    res = cli.post(f"{PFIX}/orgs/{org.id}/farms", json=farm_in, headers=user_head)
    assert res.status_code == 200

    farm_id = res.json()["id"]
    link = db.get(OrgFarm, (org.id, UUID(farm_id)))
    assert link and link.type == OrgFarmType.Own


def test_list_org_farms(cli, db, seed):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed + 1)))
    crud.org_farm.create(
        db, OrgFarm(org_id=org.id, farm_id=farm.id, type=OrgFarmType.Own)
    )

    res = cli.get(f"{PFIX}/orgs/{org.id}/farms")
    assert res.status_code == 200
    assert res.json()["count"] == 1


def test_access_missing(cli, db, seed):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed + 1)))

    res = cli.get(f"{PFIX}/orgs/{org.id}/farms/{farm.id}/access")
    assert res.status_code == 200
    assert res.json()["type"] is None


def test_put_create_access(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed + 1)))

    res = cli.put(
        f"{PFIX}/orgs/{org.id}/farms/{farm.id}/access",
        json={"type": OrgFarmType.Own},
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()["type"] == OrgFarmType.Own


def test_put_update_access(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed + 1)))
    crud.org_farm.create(
        db, OrgFarm(org_id=org.id, farm_id=farm.id, type=OrgFarmType.Own)
    )

    res = cli.put(
        f"{PFIX}/orgs/{org.id}/farms/{farm.id}/access",
        json={"type": OrgFarmType.Operate},
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()["type"] == OrgFarmType.Operate


def test_delete_access(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed + 1)))
    crud.org_farm.create(
        db, OrgFarm(org_id=org.id, farm_id=farm.id, type=OrgFarmType.Own)
    )

    res = cli.delete(f"{PFIX}/orgs/{org.id}/farms/{farm.id}/access", headers=user_head)
    assert res.status_code == 200

    res = cli.get(f"{PFIX}/orgs/{org.id}/farms/{farm.id}/access")
    assert res.json()["type"] is None


def test_access_404_org(cli, db):
    farm = crud.farm.create(db, FarmCreate(name="x"))
    res = cli.get(f"{PFIX}/orgs/{uuid4()}/farms/{farm.id}/access")
    assert res.status_code == 404


def test_access_404_farm(cli, db):
    org = crud.org.create(db, OrgCreate(name="x"))
    res = cli.get(f"{PFIX}/orgs/{org.id}/farms/{uuid4()}/access")
    assert res.status_code == 404


def test_create_farm_field_boundary(cli, db, seed, user_head):
    org = crud.org.create(db, OrgCreate(name=generate_str(seed)))

    farm_in = FarmCreate(name=generate_str(seed + 1))
    res = cli.post(
        f"{PFIX}/orgs/{org.id}/farms",
        json=farm_in.model_dump(mode="json"),
        headers=user_head,
    )
    assert res.status_code == 200
    farm_id = res.json()["id"]
    assert db.get(Farm, farm_id)
    # TODO: Check generated OrgFarm record

    field_in = FieldCreate(name=generate_str(seed + 2), type=FieldType.Pasture)
    res = cli.post(
        f"{PFIX}/farms/{farm_id}/fields",
        json=field_in.model_dump(mode="json"),
        headers=user_head,
    )
    assert res.status_code == 200
    field_id = res.json()["id"]
    assert db.get(Field, field_id)

    geom = generate_geom(seed + 3)
    boundary_in = BoundaryCreate(geom=geom, type=BoundaryType.Subfield)
    res = cli.post(
        f"{PFIX}/fields/{field_id}/boundaries",
        json=boundary_in.model_dump(mode="json"),
        headers=user_head,
    )
    assert res.status_code == 200
    boundary_id = res.json()["id"]

    record = db.get(FieldBoundary, boundary_id)
    assert record
    assert str(record.field_id) == field_id


# TODO: Write test to check geometries and geometry operations
# TODO: Test update, delete at all levels.
