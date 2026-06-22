from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ReadSession, UserSession
from app.core.config import settings
from app.core.enums import DocTag
from app.db import crud
from app.db.crud.crud_operation import CRUDOpEquipment, CRUDOpInput, CRUDOpOutput
from app.db.models import (
    BulkResource,
    FieldOp,
    FieldOpCreate,
    FieldOpUpdate,
    OpEquipmentPublic,
    OpInputPublic,
    OpOutputPublic,
    Paginated,
)

LIM = settings.DEFAULT_PAGE_LIMIT

router = APIRouter(tags=[DocTag.OP])


# region ---------------------------- Operation Endpoints -----------------------------


# TODO: Implement `embed_resources`
@router.get("/fields/{id}/ops", response_model=Paginated[FieldOp])
def list_operations(
    db: ReadSession,
    id: UUID,
    resources: bool = True,
    skip: int = 0,
    limit: int | None = LIM,
):
    field = crud.field.get_or_raise(db, id)
    return crud.field_op.get_paginated(db, skip, limit, FieldOp.field_id == field.id)


@router.post("/fields/{id}/ops", response_model=FieldOp)
def add_operation(db: UserSession, id: UUID, data_in: FieldOpCreate):
    field = crud.field.get_or_raise(db, id)
    return crud.field_op.create(db, FieldOp(**data_in.model_dump(), field_id=field.id))


@router.get("/ops/{id}", response_model=FieldOp)
def get_operation(db: ReadSession, id: UUID):
    return crud.field_op.get_or_raise(db, id)


@router.patch("/ops/{id}", response_model=FieldOp)
def edit_operation(db: UserSession, id: UUID, data_in: FieldOpUpdate):
    record = crud.field_op.get_or_raise(db, id)
    return crud.field_op.update(db, record, data_in)


@router.delete("/ops/{id}", response_model=FieldOp)
def delete_operation(db: UserSession, id: UUID):
    record = crud.field_op.get_or_raise(db, id)
    return crud.field_op.delete(db, record)


# endregion
# region -------------------- Inputs, Outputs, Equipment Endpoints --------------------


@router.get("/ops/{id}/resources", response_model=BulkResource)
def list_op_resources(db: ReadSession, id: UUID):
    op = crud.field_op.get_or_raise(db, id)
    return BulkResource.model_validate(op)


@router.post("/ops/{id}/resources", response_model=BulkResource)
def add_op_resources(db: UserSession, id: UUID, data_in: BulkResource):
    def get_crud(resource_name: str) -> CRUDOpInput | CRUDOpOutput | CRUDOpEquipment:
        """Gets the relevant crud class based on a BulkResource field name."""
        # NOTE: BulkResource fields plural, crud class names singular.
        return getattr(crud, f"op_{resource_name}".strip("s"))

    crud.field_op.get_or_raise(db, id)  # NOTE: id unused; BulkResource has op/resor ids
    data = data_in.model_dump()
    return BulkResource.model_validate(
        {k: get_crud(k).create_multiple(db, data[k]) for k in data}
    )


@router.delete("/ops/{op}/inputs/{product}", response_model=OpInputPublic)
def delete_op_input(db: UserSession, op: UUID, product: UUID):
    record = crud.op_input.get_or_raise(db, (op, product))
    return crud.op_input.delete(db, record)


@router.delete("/ops/{op}/outputs/{product}", response_model=OpOutputPublic)
def delete_op_output(db: UserSession, op: UUID, product: UUID):
    record = crud.op_output.get_or_raise(db, (op, product))
    return crud.op_output.delete(db, record)


@router.delete("/ops/{op}/equipment/{equipment}", response_model=OpEquipmentPublic)
def delete_op_equipment(db: UserSession, op: UUID, equipment: UUID):
    record = crud.op_equipment.get_or_raise(db, (op, equipment))
    return crud.op_equipment.delete(db, record)


# endregion
