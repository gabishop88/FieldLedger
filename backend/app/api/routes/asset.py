from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import func, select

from app.api.deps import ReadSession, WriteSession
from app.api.messages import ExeMsg
from app.db import crud
from app.db.models import Farm, FarmCreate, FarmPublic, FarmsPublic, FarmUpdate

# Similarity thresholds when searching
FARM_NAME_THRESHOLD = 0.4
FARM_DESC_THRESHOLD = 0.2

# Shorten the status codes I use explicitly
BAD_REQUEST = status.HTTP_400_BAD_REQUEST
NOT_FOUND = status.HTTP_404_NOT_FOUND

router = APIRouter(prefix="/farm")


@router.get("/search", response_model=FarmsPublic)
def farm_search(
    db: ReadSession,
    name: str | None = None,
    description: str | None = None,
    skip=0,
    limit=10,
) -> FarmsPublic:
    """## Search for one or more farms.
    You may search by name, which will have to be somewhat close to the full name,
    or by description which will match any farm whose description approximately contains the search term.
    """
    filters = []
    if name:
        filters.append(func.similarity(Farm.name, name) > FARM_NAME_THRESHOLD)
    if description:
        filters.append(
            func.word_similarity(Farm.description, description) > FARM_DESC_THRESHOLD
        )
    count = db.exec(select(func.count()).where(*filters)).one()
    data = db.exec(select(Farm).where(*filters).offset(skip).limit(limit)).all()
    return FarmsPublic(count=count, data=data)  # type: ignore


@router.get("/", response_model=FarmPublic)
def get_one_farm(
    db: ReadSession, id: UUID | None = None, name: str | None = None
) -> Farm:
    """## Find a single farm based on either its id or name.
    If both are provided, the id will be prioritized.
    """
    if id is None and name is None:
        raise HTTPException(BAD_REQUEST, ExeMsg.BAD_EMPTY_SEARCH)

    if id is None and name:
        farm = crud.farm.get_by_name(db, name)
    else:
        farm = db.get(Farm, id)

    if farm is None:
        raise HTTPException(NOT_FOUND, ExeMsg.NF_FARM.format(id or name))
    return farm


@router.put("/", response_model=FarmPublic)
def create_farm(db: WriteSession, farm_in: FarmCreate) -> Farm:
    return crud.farm.create(db, farm_in)


@router.patch("/{farm_id}", response_model=FarmPublic)
def update_farm(db: WriteSession, edits: FarmUpdate, farm_id: UUID) -> Farm:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(NOT_FOUND, ExeMsg.NF_FARM.format(farm_id))
    return crud.farm.update(db, farm, edits)


@router.delete("/{farm_id}", response_model=FarmPublic)
def delete_farm(db: WriteSession, farm_id: UUID) -> Farm:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(NOT_FOUND, ExeMsg.NF_FARM.format(farm_id))
    return crud.farm.delete(db, farm)
