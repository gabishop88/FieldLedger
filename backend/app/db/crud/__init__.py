"""## This is a collection of classes to simplify CRUD Operations.
*CRUD stands for Create, Read, Update, Delete*

To use them, you can: `from app.db import crud`.

Then, `crud.table.create()` (for example) to perform an operation.

Some classes define convienience functions or custom logic, see their class in app/db/crud/ for more information.
"""

__all__ = ["farm", "user"]

from .crud_asset import farm
from .crud_iam import user
