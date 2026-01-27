"""## This is a collection of classes to simplify CRUD Operations.
*CRUD stands for Create, Read, Update, Delete*

To use them, you can: `from app.db import crud`.

Then, `crud.table.create()` (for example) to perform an operation.

Some classes add functions or alter logic, see each class in app/db/crud/ for more info.
"""

__all__ = ["farm", "field", "ref", "user"]

from .crud_asset import farm, field
from .crud_iam import user
from .crud_ref import ref
