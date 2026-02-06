"""### This is a collection of classes to simplify CRUD Operations.
*CRUD stands for Create, Read, Update, Delete*

To use them, you can: `from app.db import crud`.

Then, `crud.table.create()` (for example) to perform an operation.

Some classes add functions or alter logic, see each class in app/db/crud/ for more info.
"""

__all__ = [
    "user",
    "crop",
    "unit",
    "equipment",
    "product",
    "boundary",
    "farm",
    "field",
    "org",
    "org_farm",
]

from .crud_iam import user
from .crud_ref import crop, unit
from .crud_resource import equipment, product
from .crud_structure import boundary, farm, field, org, org_farm
