from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import ReadSession, WriteSession
from app.db import crud
from app.db.models import Farm, FarmCreate, FarmPublic, FarmsPublic, FarmUpdate

FARM_NAME_THRESHOLD = 0.4
FARM_DESC_THRESHOLD = 0.3

router = APIRouter(prefix="/farm")


@router.get("/search", response_model=FarmsPublic)
def farm_search(
    db: ReadSession,
    name: str | None = None,
    description: str | None = None,
    skip=0,
    limit=10,
):
    """## Search for one or more farms.
    You may search by name, which will have to be somewhat close to the full name,
    or by description which will match any farm whose description approximately contains the search term.
    """
    filters = [
        func.similarity(Farm.name, name) > FARM_NAME_THRESHOLD,
        func.word_similarity(Farm.description, description) > FARM_DESC_THRESHOLD,
    ]
    count = db.exec(select(func.count()).where(*filters)).one()
    data = db.exec(select(Farm).where(*filters).offset(skip).limit(limit)).all()
    return FarmsPublic(count=count, data=data)  # type: ignore


@router.get("/", response_model=FarmPublic)
def get_one_farm(db: ReadSession, id: UUID | None = None, name: str | None = None):
    """## Find a single farm based on either its id or name.
    If both are provided, the id will be prioritized.
    """
    if id is None and name is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A name or id is required.")

    if id is None and name:
        return crud.farm.get_by_name(db, name)
    return db.get(Farm, id)


@router.put("/", response_model=FarmPublic)
def create_farm(db: WriteSession, farm_in: FarmCreate):
    return crud.farm.create(db, farm_in)


@router.patch("/{farm_id}", response_model=FarmPublic)
def update_farm(db: WriteSession, edits: FarmUpdate, farm_id: UUID):
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"<Farm {farm_id}> not found.")
    return crud.farm.update(db, farm, edits)


@router.delete("/{farm_id}", response_model=FarmPublic)
def delete_farm(db: WriteSession, farm_id: UUID):
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"<Farm {farm_id}> not found.")
    return crud.farm.delete(db, farm)
