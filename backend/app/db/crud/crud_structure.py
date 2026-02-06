from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    BoundaryUpdate,
    Farm,
    FarmCreate,
    FarmUpdate,
    Field,
    FieldBoundary,
    FieldUpdate,
    Org,
    OrgBase,
)


class CRUDOrg(CRUDBase[Org, OrgBase, OrgBase]):
    pass


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    pass


class CRUDField(CRUDBase[Field, Field, FieldUpdate]):
    pass


class CRUDFieldBoundary(CRUDBase[FieldBoundary, FieldBoundary, BoundaryUpdate]):
    pass


org = CRUDOrg(Org)
farm = CRUDFarm(Farm)
field = CRUDField(Field)
boundary = CRUDFieldBoundary(FieldBoundary)
