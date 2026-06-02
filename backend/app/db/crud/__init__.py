"""### This is a collection of classes to simplify CRUD Operations.
*CRUD stands for Create, Read, Update, Delete*

To use them, you can: `from app.db import crud`.

Then, `crud.table.create()` (for example) to perform an operation.

Some classes add functions or alter logic, see each class in app/db/crud/ for more info.
"""

__all__ = [
    "boundary",
    "crop",
    "equipment",
    "farm",
    "field",
    "jd_connection",
    "jd_link",
    "op",
    "op_equipment",
    "op_input",
    "op_output",
    "org",
    "org_farm",
    "product",
    "unit",
    "user",
]

from .crud_iam import user
from .crud_integration import jd_connection, jd_link
from .crud_operation import op, op_equipment, op_input, op_output
from .crud_ref import crop, unit
from .crud_resource import equipment, product
from .crud_structure import boundary, farm, field, org, org_farm
