"""
This is designed to be a scratchpad or playground where I can work with the API, similar
to 'Try it out' on the /docs page, but programatic.

Mostly this is for testing things that I think may need to become endpoints, or doing
repetitive tasks that would be annoying to have to keep repeating on /docs page but I
don't think need to be a fullly implemented and tested endpoint.
"""

import json
import logging
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

# If this is not being run from inside docker, this loads the .env variables
try:
    from app.core.config import settings
except ValidationError:
    from dotenv import load_dotenv

    env_path = Path(__file__).parents[3] / ".env"
    load_dotenv(env_path)
    from app.core.config import settings
from app.db.models import BoundaryUpdate, Farm, Field, FieldBoundary, Paginated
from app.main import app

EMAIL = settings.FIRST_SUPERUSER
PWD = settings.FIRST_SUPERUSER_PASSWORD

client = TestClient(app)
client.base_url = f"http://localhost:8000{settings.API_PREFIX}"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("scratchpad")

# region ------------------------------ API Call Helpers ------------------------------


def login() -> None:
    res = client.post(
        "/account/login/access-token", data={"username": EMAIL, "password": PWD}
    )
    res.raise_for_status()
    client.headers["Authorization"] = f"Bearer {res.json()['access_token']}"


def logout() -> None:
    client.headers.pop("Authorization")


def list_farms() -> Paginated[Farm]:
    res = client.get("/farm/search?limit=20")
    res.raise_for_status()
    body = res.json()
    return Paginated(count=body["count"], data=[Farm(**f) for f in body["data"]])


def get_farm(name_or_id: str) -> Farm:
    res = client.get(f"/farm/{name_or_id}")
    res.raise_for_status()
    return Farm(**res.json())


def list_fields(farm: Farm) -> Paginated[Field]:
    res = client.get(f"/farm/{farm.id}/fields?limit=100")
    res.raise_for_status()
    body = res.json()
    return Paginated(count=body["count"], data=[Field(**f) for f in body["data"]])


def get_boundaries(field) -> Paginated[FieldBoundary]:
    res = client.get(f"/farm/{field.farm_id}/fields/{field.id}/boundaries")
    res.raise_for_status()
    body = res.json()
    return Paginated(
        count=body["count"], data=[FieldBoundary(**b) for b in body["data"]]
    )


def edit_boundary(boundary: FieldBoundary, edits: BoundaryUpdate) -> FieldBoundary:
    data = edits.model_dump(mode="json", exclude_unset=True)
    res = client.patch(f"/farm/boundaries/{boundary.id}", json=data)
    res.raise_for_status()
    return FieldBoundary(**res.json())


# endregion
# region ----------------------------- Data Prep Helpers ------------------------------


def log_model(model) -> None:
    logger.info(json.dumps(model.model_dump(mode="json"), indent=2))


# endregion
# region ------------------------------- Main Functions -------------------------------


def change_boundary_notes(message: str) -> None:
    """## Changes the notes column in ALL field boundaries to the given message.
    Probably could have just emitted an update via db session?
    """
    boundary_update = BoundaryUpdate(notes=message)

    farms = list_farms()
    logger.info(f"{farms.count} Farms")
    for farm in farms.data:
        fields = list_fields(farm)
        logger.info(f"{farm.name}: {fields.count} Fields")

        for field in fields.data:
            boundaries = get_boundaries(field)
            for b in boundaries.data:
                updated = edit_boundary(b, boundary_update)
                logger.info(f"{field.name}: {updated.notes == boundary_update.notes}")

def main():
    login()
    change_boundary_notes("Source: My John Deere API")


if __name__ == "__main__":
    main()

# endregion
