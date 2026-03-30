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


class CRUDFieldOp(CRUDBase[FieldOp, FieldOp, FieldOpUpdate]): ...


class CRUDOpInput(CRUDBase[OpInput, OpInput, OpInputUpdate]): ...


class CRUDOpOutput(CRUDBase[OpOutput, OpOutput, OpOutputUpdate]): ...


class CRUDOpEquipment(CRUDBase[OpEquipment, OpEquipment, OpEquipmentUpdate]): ...


op = CRUDFieldOp(FieldOp)
op_input = CRUDOpInput(OpInput)
op_output = CRUDOpOutput(OpOutput)
op_equipment = CRUDOpEquipment(OpEquipment)
