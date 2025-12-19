from fastapi.testclient import TestClient
from sqlmodel import Session

from app.api.routes.ref import get_table_names
from app.core.config import settings
from app.db import models
from tests.utils.rng import generate_str

PFIX = settings.API_PREFIX


def test_list_reference_tables(client: TestClient) -> None:
    res = client.get(f"{PFIX}/ref/tables")
    assert res.status_code == 200
    tables = res.json()
    assert isinstance(tables, list)
    assert tables == get_table_names()


def test_create_update_delete_field_type(
    client: TestClient, db: Session, seed: int, su_headers: dict[str, str]
) -> None:
    name = generate_str(seed)
    desc = generate_str(seed + 1)

    # create
    data = {"name": name, "description": desc}
    res = client.put(f"{PFIX}/ref/FieldType", json=data, headers=su_headers)
    assert res.status_code == 200
    created = res.json()
    assert created["name"] == name
    assert created["description"] == desc

    # verify in db
    ft = db.get(models.FieldType, name)
    assert ft is not None
    assert ft.name == name

    # update description
    new_desc = generate_str(seed + 2)
    edits = {"description": new_desc}
    res = client.patch(f"{PFIX}/ref/FieldType/{name}", json=edits, headers=su_headers)
    assert res.status_code == 200
    updated = res.json()
    assert updated["name"] == name
    assert updated["description"] == new_desc

    db.refresh(ft)
    assert ft.description == new_desc

    # delete
    res = client.delete(f"{PFIX}/ref/FieldType/{name}", headers=su_headers)
    assert res.status_code == 200
    deleted = res.json()
    assert deleted["name"] == name

    # ensure removed
    assert db.get(models.FieldType, name) is None


def test_fail_update_delete_nonexistent(
    client: TestClient, su_headers: dict[str, str]
) -> None:
    bad_name = "no_such_ref"

    edits = {"description": "nope"}
    res = client.patch(
        f"{PFIX}/ref/FieldType/{bad_name}", json=edits, headers=su_headers
    )
    assert res.status_code == 404

    res = client.delete(f"{PFIX}/ref/FieldType/{bad_name}", headers=su_headers)
    assert res.status_code == 404
