from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.messages import ExeMsg
from app.core.config import settings
from app.db import crud
from app.db.models import Farm, FarmCreate, FarmUpdate
from tests.utils.rng import generate_str

PFIX = settings.API_PREFIX


def test_create_farm(client: TestClient, db: Session, seed, user_headers) -> None:
    data = FarmCreate(
        name=generate_str(seed), description=generate_str(seed + 1)
    ).model_dump()
    res = client.put(f"{PFIX}/farm", json=data, headers=user_headers)
    assert res.status_code == 200
    farm_res = res.json()
    assert farm_res["name"] == generate_str(seed)
    assert farm_res["description"] == generate_str(seed + 1)

    farm_db = db.get(Farm, farm_res["id"])
    assert farm_db
    assert farm_db.name == farm_res["name"]
    assert farm_db.description == farm_res["description"]
    assert farm_db.private == farm_res["private"]


def test_fail_create_duplicate_farm_name(
    client: TestClient, db: Session, seed, user_headers
) -> None:
    assert crud.farm.get_by_name(db, generate_str(seed)), "Farm should exist."

    data = FarmCreate(
        name=generate_str(seed), description=generate_str(seed + 1)
    ).model_dump()
    res = client.put(f"{PFIX}/farm", json=data, headers=user_headers)
    assert res.status_code == 400
    assert res.json()["detail"] == f"Key (name)=({data['name']}) already exists."

    # Since that was an error caught and raised directly by the database, the session
    # must be rolled back and the farm inserted again. This is an issue because the tests
    # Reuse the same session (so that I can have persistent objects that get rolled back at the end).
    # In a regular API session, the transaction that caused the error would just send back
    # an exception to the user, so the following transactions would never get called.
    db.rollback()
    res = client.put(f"{PFIX}/farm", json=data, headers=user_headers)
    assert res.status_code == 200


def test_farm_search(client: TestClient, db: Session, seed) -> None:
    farm = crud.farm.get_by_name(db, generate_str(seed))
    assert farm is not None, "Test Farm should exist."

    # Test search by name
    query = {"name": generate_str(seed)}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by description
    query = {"description": generate_str(seed + 1)}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial name
    query = {"name": generate_str(seed)[:-4]}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial description
    query = {"description": generate_str(seed + 1)[:4]}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by name no results (not similar)
    query = {"name": generate_str(seed + 2)}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Test search by name no results (similar, but not enough)
    query = {"name": generate_str(seed)[:4]}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Test search by description (not similar)
    query = {"description": generate_str(seed + 2)[:8]}
    res = client.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # NOTE: Cannot test no search terms since I don't know how many farms are already in the db


def test_get_farm(client: TestClient, db: Session, seed) -> None:
    farm = crud.farm.get_by_name(db, generate_str(seed))
    assert farm is not None, "Test Farm should exist."

    # Get by id
    res = client.get(f"{PFIX}/farm", params={"id": str(farm.id)})
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Get by name
    res = client.get(f"{PFIX}/farm", params={"name": generate_str(seed)})
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Fail get by id
    bad_id = str(uuid4())
    res = client.get(f"{PFIX}/farm", params={"id": bad_id})
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)

    # Fail get by name
    bad_name = generate_str(seed + 2)
    res = client.get(f"{PFIX}/farm", params={"name": bad_name})
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_name)

    # Fail get no params
    res = client.get(f"{PFIX}/farm", params={})
    assert res.status_code == 400
    assert res.json()["detail"] == ExeMsg.BAD_EMPTY_SEARCH


def test_update_farm(client: TestClient, db: Session, seed, user_headers) -> None:
    farm = crud.farm.get_by_name(db, generate_str(seed))
    assert farm is not None, "Test farm should exist."
    assert farm.private is False
    assert farm.description == generate_str(seed + 1)

    edits = FarmUpdate(
        name=generate_str(seed + 3), private=True, description=generate_str(seed + 4)
    ).model_dump()
    res = client.patch(f"{PFIX}/farm/{farm.id}", json=edits, headers=user_headers)
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


def test_fail_update_nonexistant_farm(client: TestClient, user_headers) -> None:
    bad_id = str(uuid4())
    edits = FarmUpdate(name=generate_str()).model_dump(exclude_unset=True)
    res = client.patch(f"{PFIX}/farm/{bad_id}", json=edits, headers=user_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)


def test_delete_farm(client: TestClient, db: Session, seed, user_headers) -> None:
    farm = crud.farm.get_by_name(db, generate_str(seed + 3))
    assert farm is not None, "Test Farm should exist."

    res = client.delete(f"{PFIX}/farm/{farm.id}", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)
    assert res.json()["name"] == farm.name


def test_fail_delete_nonexistant_farm(client: TestClient,user_headers) -> None:
    bad_id = str(uuid4())
    res = client.delete(f"{PFIX}/farm/{bad_id}", headers=user_headers)
    assert res.status_code == 404
    assert res.json()["detail"] == ExeMsg.NF_FARM.format(bad_id)
