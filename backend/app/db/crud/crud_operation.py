from app.api.models import (
    FieldOpUpdate,
    OpEquipmentUpdate,
    OpInputUpdate,
    OpOutputUpdate,
)
from app.db.crud.crud_base import CRUDBase
from app.db.models import FieldOp, OpEquipment, OpInput, OpOutput


class CRUDFieldOp(CRUDBase[FieldOp, FieldOp, FieldOpUpdate]):
    pass


class CRUDOpInput(CRUDBase[OpInput, OpInput, OpInputUpdate]):
    pass


class CRUDOpOutput(CRUDBase[OpOutput, OpOutput, OpOutputUpdate]):
    pass


class CRUDOpEquipment(CRUDBase[OpEquipment, OpEquipment, OpEquipmentUpdate]):
    pass


field_op = CRUDFieldOp(FieldOp)
op_input = CRUDOpInput(OpInput)
op_output = CRUDOpOutput(OpOutput)
op_equipment = CRUDOpEquipment(OpEquipment)
