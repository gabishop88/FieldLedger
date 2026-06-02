from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    FieldOp,
    FieldOpUpdate,
    OpEquipment,
    OpEquipmentUpdate,
    OpInput,
    OpInputUpdate,
    OpOutput,
    OpOutputUpdate,
)


class CRUDFieldOp(CRUDBase[FieldOp, FieldOp, FieldOpUpdate]):
    pass


class CRUDOpInput(CRUDBase[OpInput, OpInput, OpInputUpdate]):
    pass


class CRUDOpOutput(CRUDBase[OpOutput, OpOutput, OpOutputUpdate]):
    pass


class CRUDOpEquipment(CRUDBase[OpEquipment, OpEquipment, OpEquipmentUpdate]):
    pass


op = CRUDFieldOp(FieldOp)
op_input = CRUDOpInput(OpInput)
op_output = CRUDOpOutput(OpOutput)
op_equipment = CRUDOpEquipment(OpEquipment)
