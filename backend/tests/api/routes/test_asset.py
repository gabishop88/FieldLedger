from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.messages import ExeMsg
from app.core.config import settings
from app.db import crud
from app.db.models import Farm, FarmCreate, FarmUpdate
from tests.utils.rng import generate_str

PFIX = settings.API_PREFIX


def test_create_farm(cli: TestClient, db: Session, seed, user_head) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    res = cli.put(f"{PFIX}/farm", json=farm_in.model_dump(), headers=user_head)
    assert res.status_code == 200
    farm_res = res.json()
    assert farm_res["name"] == farm_in.name
    assert farm_res["description"] == farm_in.description
    assert farm_res["private"] is False

    db_farm = db.get(Farm, farm_res["id"])
    assert db_farm
    assert db_farm.name == farm_in.name


def test_fail_create_farm(cli: TestClient, db: Session, seed, user_head) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    crud.farm.create(db, farm_in)

    res = cli.put(f"{PFIX}/farm", json=farm_in.model_dump(), headers=user_head)
    assert res.status_code == 409
    assert res.json()["detail"] == f"Key (name)=({farm_in.name}) already exists."


def test_farm_search(cli: TestClient, db: Session, seed) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    # Test search by name
    query = {"name": generate_str(seed)}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by description
    query = {"description": generate_str(seed + 1)}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial name
    query = {"name": generate_str(seed)[:-4]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial description
    query = {"description": generate_str(seed + 1)[:4]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by name no results (not similar)
    query = {"name": generate_str(seed + 2)}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Test search by name no results (similar, but not enough)
    query = {"name": generate_str(seed)[:4]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Test search by description (not similar)
    query = {"description": generate_str(seed + 2)[:8]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0


def test_get_farm(cli: TestClient, db: Session, seed) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    # Get by id
    res = cli.get(f"{PFIX}/farm", params={"id": str(farm.id)})
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Get by name
    res = cli.get(f"{PFIX}/farm", params={"name": generate_str(seed)})
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Fail get by id
    bad_id = str(uuid4())
    res = cli.get(f"{PFIX}/farm", params={"id": bad_id})
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)

    # Fail get by name
    bad_name = generate_str(seed + 2)
    res = cli.get(f"{PFIX}/farm", params={"name": bad_name})
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_name)

    # Fail get no params
    res = cli.get(f"{PFIX}/farm", params={})
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_EMPTY_SEARCH


def test_update_farm(cli: TestClient, db: Session, seed, user_head) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)
    assert farm.private is False
    assert farm.description == generate_str(seed + 1)

    edits = FarmUpdate(
        name=generate_str(seed + 3), private=True, description=generate_str(seed + 4)
    ).model_dump()
    res = cli.patch(f"{PFIX}/farm/{farm.id}", json=edits, headers=user_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)
    assert res.json()["name"] == generate_str(seed + 3)
    assert res.json()["private"] is True
    assert res.json()["description"] == generate_str(seed + 4)

    db.refresh(farm)
    assert res.json()["id"] == str(farm.id)
    assert res.json()["name"] == farm.name
    assert res.json()["private"] == farm.private
    assert res.json()["description"] == farm.description


def test_fail_update_nonexistant_farm(cli: TestClient, user_head) -> None:
    bad_id = str(uuid4())
    edits = FarmUpdate(name=generate_str()).model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/farm/{bad_id}", json=edits, headers=user_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)


def test_delete_farm(cli: TestClient, db: Session, seed, user_head) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    res = cli.delete(f"{PFIX}/farm/{farm.id}", headers=user_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)
    assert res.json()["name"] == farm.name

    assert db.get(Farm, farm.id) is None


def test_fail_delete_nonexistant_farm(cli: TestClient, user_head) -> None:
    bad_id = str(uuid4())
    res = cli.delete(f"{PFIX}/farm/{bad_id}", headers=user_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)
