from uuid import uuid4

from fastapi.testclient import TestClient
from shapely import wkt
from sqlmodel import Session

from app.core.config import settings
from app.core.enums import ErrMsg
from app.db import crud
from app.db.models import (
    Farm,
    FarmCreate,
    FarmUpdate,
    Field,
    FieldBoundary,
    FieldCreate,
)
from tests.utils.rng import generate_geom, generate_str

PFIX = settings.API_PREFIX

# region --------------------------------- Farm Tests ---------------------------------


def test_create_farm(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    res = cli.post(f"{PFIX}/farm", json=farm_in.model_dump(), headers=user_head)
    assert res.status_code == 200
    farm_res = res.json()
    assert farm_res["name"] == farm_in.name
    assert farm_res["description"] == farm_in.description
    assert farm_res["private"] is False

    db_farm = db.get(Farm, farm_res["id"])
    assert db_farm
    assert db_farm.name == farm_in.name


def test_fail_create_farm(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    crud.farm.create(db, farm_in)

    res = cli.post(f"{PFIX}/farm", json=farm_in.model_dump(), headers=user_head)
    assert res.status_code == 409
    assert res.json()["detail"] == f"Key (name)=({farm_in.name}) already exists."


def test_farm_search(cli: TestClient, db: Session, seed: int) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    # Test search by name
    query = {"name": generate_str(seed)}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by description
    query = {"desc": generate_str(seed + 1)}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    # print(res.json())
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial name
    query = {"name": generate_str(seed)[:-4]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(farm.id)

    # Test search by partial description
    query = {"desc": generate_str(seed + 1)[:4]}
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
    query = {"desc": generate_str(seed + 2)[:8]}
    res = cli.get(f"{PFIX}/farm/search", params=query)
    assert res.status_code == 200
    assert res.json()["count"] == 0


def test_get_farm(cli: TestClient, db: Session, seed: int) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    # Get by id
    res = cli.get(f"{PFIX}/farm/{farm.id}")
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Get by name
    res = cli.get(f"{PFIX}/farm/{generate_str(seed)}")
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)

    # Fail get by id
    bad_id = str(uuid4())
    res = cli.get(f"{PFIX}/farm/{bad_id}")
    assert res.status_code == 404
    assert res.json()["detail"] == ErrMsg.NF.format("Farm", bad_id)

    # Fail get by name
    bad_name = generate_str(seed + 2)
    res = cli.get(f"{PFIX}/farm/{bad_name}")
    assert res.status_code == 404
    assert res.json()["detail"] == ErrMsg.NF.format("Farm", bad_name)


def test_update_farm(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
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


def test_fail_update_nonexistant_farm(
    cli: TestClient, user_head: dict[str, str]
) -> None:
    bad_id = str(uuid4())
    edits = FarmUpdate(name=generate_str()).model_dump(exclude_unset=True)
    res = cli.patch(f"{PFIX}/farm/{bad_id}", json=edits, headers=user_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ErrMsg.NF.format("Farm", bad_id)


def test_delete_farm(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm_in = FarmCreate(name=generate_str(seed), description=generate_str(seed + 1))
    farm = crud.farm.create(db, farm_in)

    res = cli.delete(f"{PFIX}/farm/{farm.id}", headers=user_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(farm.id)
    assert res.json()["name"] == farm.name

    assert db.get(Farm, farm.id) is None


def test_fail_delete_nonexistant_farm(
    cli: TestClient, user_head: dict[str, str]
) -> None:
    bad_id = str(uuid4())
    res = cli.delete(f"{PFIX}/farm/{bad_id}", headers=user_head)
    assert res.status_code == 404
    assert res.json()["detail"] == ErrMsg.NF.format("Farm", bad_id)


# endregion
# region -------------------------------- Field Tests ---------------------------------


def test_create_field(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))

    field_in = FieldCreate(name=generate_str(seed + 1), type="Field Crops")
    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields",
        json=[field_in.model_dump()],
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()[0]["name"] == field_in.name

    field_2 = FieldCreate(name=generate_str(seed + 2), type="Mixed Use", notes="Test")
    field_3 = FieldCreate(name=generate_str(seed + 3), type="Agroforestry")
    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields",
        json=[field_2.model_dump(), field_3.model_dump()],
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()[0]["name"] == field_2.name
    assert res.json()[1]["name"] == field_3.name
    assert res.json()[1]["farm_id"] == str(farm.id)


def test_fail_create_field(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))

    field_in = FieldCreate(name=generate_str(seed + 1), type="Field Crops")
    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields",
        json=[field_in.model_dump()],
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()[0]["name"] == field_in.name

    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields",
        json=[field_in.model_dump()],
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()[0]["name"] == field_in.name
    # TODO: Add Unique constraing to Field (farm_id, name)?

    field_bad = FieldCreate(name=generate_str(seed + 2), type="Invalid Type")
    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields",
        json=[field_bad.model_dump()],
        headers=user_head,
    )
    assert res.status_code == 422
    assert (
        res.json()["detail"]
        == 'Key (type)=(Invalid Type) is not present in table "field_type".'
    )  # noqa: E501
    # invalid field_type
    pass


def test_list_fields(cli: TestClient, db: Session, seed: int) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    fields = crud.field.create_multiple(
        db,
        [
            Field(name=generate_str(seed + i), type="Field Crops", farm_id=farm.id)
            for i in range(5)
        ],
    )

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields")
    assert res.status_code == 200
    assert res.json()["count"] == 5
    returned_names = [item["name"] for item in res.json()["data"]]
    assert all(field.name in returned_names for field in fields)


def test_get_field(cli: TestClient, db: Session, seed: int) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )

    # Get by id
    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field.id}")
    assert res.status_code == 200
    assert res.json()["id"] == str(field.id)

    # Get by name
    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field.name}")
    assert res.status_code == 200
    assert res.json()["id"] == str(field.id)


def test_update_field(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )

    edits = {"name": generate_str(seed + 2), "notes": "Updated notes"}
    res = cli.patch(
        f"{PFIX}/farm/{farm.id}/fields/{field.id}", json=edits, headers=user_head
    )
    assert res.status_code == 200
    assert res.json()["id"] == str(field.id)
    assert res.json()["name"] == generate_str(seed + 2)
    assert res.json()["notes"] == "Updated notes"


def test_delete_field(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    fields = crud.field.create_multiple(
        db,
        [
            Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id),
            Field(name=generate_str(seed + 2), type="Agroforestry", farm_id=farm.id),
        ],
    )

    res = cli.delete(f"{PFIX}/farm/{farm.id}/fields/{fields[0].id}", headers=user_head)
    assert res.status_code == 200
    assert res.json() == fields[0].model_dump(mode="json")

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0] == fields[1].model_dump(mode="json")


# endregion
# region ------------------------------- Boundary Tests -------------------------------


def test_add_boundary(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    data = {"geom": generate_geom(seed), "type": "Primary Boundary"}

    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields/{field.id}/boundaries",
        json=data,
        headers=user_head,
    )
    assert res.status_code == 200
    assert res.json()["field_id"] == str(field.id)
    assert res.json()["geom"] == data["geom"]


def test_list_boundaries(cli: TestClient, db: Session, seed: int) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    for i in range(3):
        crud.boundary.create(
            db,
            FieldBoundary(
                field_id=field.id,
                geom=generate_geom(seed + i),
                type="Subfield" if i else "Primary Boundary",
            ),
        )

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field.id}/boundaries")
    assert res.status_code == 200
    assert res.json()["count"] == 3
    assert len(res.json()["data"]) == 3
    assert all(item["field_id"] == str(field.id) for item in res.json()["data"])


def test_boundary_scope(cli: TestClient, db: Session, seed: int):
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field1 = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    field2 = crud.field.create(
        db, Field(name=generate_str(seed + 2), type="Field Crops", farm_id=farm.id)
    )
    boundary = crud.boundary.create(
        db,
        FieldBoundary(
            field_id=field1.id, geom=generate_geom(seed), type="Primary Boundary"
        ),
    )

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field1.id}/boundaries")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["data"][0]["id"] == str(boundary.id)

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field2.id}/boundaries")
    assert res.status_code == 200
    assert res.json()["count"] == 0
    assert len(res.json()["data"]) == 0


def test_update_boundary(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    boundary = crud.boundary.create(
        db,
        FieldBoundary(
            field_id=field.id, geom=generate_geom(seed), type="Primary Boundary"
        ),
    )
    edits = {"type": "Subfield", "active": False, "geom": generate_geom(seed + 2)}

    res = cli.patch(
        f"{PFIX}/farm/boundaries/{boundary.id}",
        json=edits,
        headers=user_head,
    )
    assert res.status_code == 200
    assert wkt.loads(res.json()["geom"]).equals(wkt.loads(edits["geom"]))
    assert res.json()["type"] == edits["type"]
    assert res.json()["active"] == edits["active"]


def test_delete_boundary(
    cli: TestClient, db: Session, seed: int, user_head: dict[str, str]
) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    boundary = crud.boundary.create(
        db,
        FieldBoundary(
            field_id=field.id, geom=generate_geom(seed), type="Primary Boundary"
        ),
    )

    res = cli.delete(f"{PFIX}/farm/boundaries/{boundary.id}", headers=user_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(boundary.id)

    res = cli.get(f"{PFIX}/farm/{farm.id}/fields/{field.id}/boundaries")
    assert res.status_code == 200
    assert res.json()["count"] == 0


def test_fail_invalid_geom(cli: TestClient, db: Session, seed, user_head) -> None:
    farm = crud.farm.create(db, FarmCreate(name=generate_str(seed)))
    field = crud.field.create(
        db, Field(name=generate_str(seed + 1), type="Field Crops", farm_id=farm.id)
    )
    # Polygon is not closed
    data = {"geom": "MULTIPOLYGON(((0 0, 1 1, 1 0)))", "type": "Primary Boundary"}

    res = cli.post(
        f"{PFIX}/farm/{farm.id}/fields/{field.id}/boundaries",
        json=data,
        headers=user_head,
    )
    assert res.status_code == 422
    assert res.json()["detail"][0]["msg"] == f"Value error, {ErrMsg.INVALID_WKT}"


# endregion
