from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.db import crud
from app.db import models as db_models
from tests.utils.rng import generate_str

PFIX = settings.API_PREFIX + "/ref"


def test_list_ref_tables(cli: TestClient) -> None:
    res = cli.get(f"{PFIX}/tables")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert "Crop" in res.json()
    assert "Unit" in res.json()


def test_list_enum_ref_values(cli: TestClient) -> None:
    res = cli.get(f"{PFIX}/FieldType")
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test_ref")

    logger.info(res.json())
    assert res.status_code == 200
    body = res.json()
    assert "count" in body and "data" in body
    assert body["count"] >= len(body["data"])
    assert {"name", "description"} <= body["data"][0].keys()


def test_list_enum_ref_pagination(cli: TestClient) -> None:
    res = cli.get(f"{PFIX}/FieldType?skip=1&limit=1")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 1
    assert len(body["data"]) <= 1


def test_list_crop_refs(cli: TestClient, db: Session, seed: int) -> None:
    crops = [
        crud.crop.create(
            db,
            db_models.Crop(
                common_name=generate_str(seed + i),
                latin_name=generate_str(seed + i),
                family=generate_str(seed + i),
            ),
        )
        for i in range(3)
    ]

    res = cli.get(f"{PFIX}/Crop", params={"limit": 1000})
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 3
    names = [c["common_name"] for c in body["data"]]
    assert crops[0].common_name in names


def test_add_crop(cli: TestClient, seed: int, su_head: dict[str, str]) -> None:
    crop = {
        "common_name": generate_str(seed),
        "latin_name": generate_str(seed),
        "family": generate_str(seed),
    }
    res = cli.post(f"{PFIX}/crop", json=crop, headers=su_head)
    assert res.status_code == 200
    assert res.json()["common_name"] == crop["common_name"]


def test_edit_crop(cli: TestClient, db: Session, seed: int, su_head) -> None:
    crop = crud.crop.create(
        db,
        db_models.Crop(
            common_name=generate_str(seed),
            latin_name=generate_str(seed),
            family=generate_str(seed),
        ),
    )

    res = cli.patch(
        f"{PFIX}/crop/{crop.id}",
        json={"common_name": generate_str(seed + 1)},
        headers=su_head,
    )
    assert res.status_code == 200
    assert res.json()["common_name"] == generate_str(seed + 1)


def test_delete_crop(cli: TestClient, db: Session, seed: int, su_head) -> None:
    crop = crud.crop.create(
        db,
        db_models.Crop(
            common_name=generate_str(seed),
            latin_name=generate_str(seed),
            family=generate_str(seed),
        ),
    )

    res = cli.delete(f"{PFIX}/crop/{crop.id}", headers=su_head)
    assert res.status_code == 200
    assert res.json()["id"] == str(crop.id)


def test_edit_crop_404(cli: TestClient, su_head) -> None:
    from uuid import uuid4

    res = cli.patch(f"{PFIX}/crop/{uuid4()}", json={"name": "X"}, headers=su_head)
    assert res.status_code == 404


def test_list_unit_refs(cli: TestClient, db: Session, seed: int) -> None:
    units = [
        crud.unit.create(
            db,
            db_models.Unit(
                name=generate_str(seed + i),
                si_unit_name=generate_str(seed + i),
                si_conv=1.0,
            ),
        )
        for i in range(3)
    ]

    res = cli.get(f"{PFIX}/Unit", params={"limit": 1000})
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 3
    names = [c["name"] for c in body["data"]]
    assert units[0].name in names


def test_edit_unit(cli: TestClient, db: Session, seed: int, su_head) -> None:
    unit = crud.unit.create(
        db,
        db_models.Unit(
            name=generate_str(seed),
            si_unit_name=generate_str(seed),
            si_conv=1.0,
        ),
    )

    res = cli.patch(
        f"{PFIX}/unit/{unit.name}",
        json={"name": generate_str(seed + 1)},
        headers=su_head,
    )
    assert res.status_code == 200
    assert res.json()["name"] == generate_str(seed + 1)


def test_edit_unit_404(cli: TestClient, su_head) -> None:
    from uuid import uuid4

    res = cli.patch(f"{PFIX}/unit/{uuid4()}", json={"name": "X"}, headers=su_head)
    assert res.status_code == 404
