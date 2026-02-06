from app.db.crud.crud_base import CRUDBase
from app.db.models import (
    BoundaryCreate,
    BoundaryUpdate,
    Farm,
    FarmCreate,
    FarmUpdate,
    Field,
    FieldBoundary,
    FieldCreate,
    FieldUpdate,
    Org,
    OrgCreate,
    OrgFarm,
    OrgFarmUpsert,
    OrgUpdate,
)


class CRUDOrg(CRUDBase[Org, OrgCreate, OrgUpdate]):
    pass


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]):
    pass


class CRUDOrgFarm(CRUDBase[OrgFarm, OrgFarm, OrgFarmUpsert]):
    pass


class CRUDField(CRUDBase[Field, FieldCreate, FieldUpdate]):
    pass


class CRUDFieldBoundary(CRUDBase[FieldBoundary, BoundaryCreate, BoundaryUpdate]):
    pass


org = CRUDOrg(Org)
farm = CRUDFarm(Farm)
org_farm = CRUDOrgFarm(OrgFarm)
field = CRUDField(Field)
boundary = CRUDFieldBoundary(FieldBoundary)
