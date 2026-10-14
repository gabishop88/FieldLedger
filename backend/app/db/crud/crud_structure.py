from app.api.models import (
    BoundaryUpdate,
    FarmCreate,
    FarmUpdate,
    FieldUpdate,
    OrgCreate,
    OrgFarmUpsert,
    OrgUpdate,
)
from app.db.crud.crud_base import CRUDBase
from app.db.models import Farm, Field, FieldBoundary, Org, OrgFarm


class CRUDOrg(CRUDBase[Org, OrgCreate, OrgUpdate]):
    pass


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    pass


class CRUDOrgFarm(CRUDBase[OrgFarm, OrgFarm, OrgFarmUpsert]):
    pass


class CRUDField(CRUDBase[Field, Field, FieldUpdate]):
    pass


class CRUDFieldBoundary(CRUDBase[FieldBoundary, FieldBoundary, BoundaryUpdate]):
    pass


org = CRUDOrg(Org)
farm = CRUDFarm(Farm)
org_farm = CRUDOrgFarm(OrgFarm)
field = CRUDField(Field)
boundary = CRUDFieldBoundary(FieldBoundary)
