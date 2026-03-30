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
    OrgCreate,
    OrgFarm,
    OrgFarmUpsert,
    OrgUpdate,
)


class CRUDOrg(CRUDBase[Org, OrgCreate, OrgUpdate]): ...


class CRUDFarm(CRUDBase[Farm, FarmCreate, FarmUpdate]): ...


class CRUDOrgFarm(CRUDBase[OrgFarm, OrgFarm, OrgFarmUpsert]): ...


class CRUDField(CRUDBase[Field, Field, FieldUpdate]): ...


class CRUDFieldBoundary(CRUDBase[FieldBoundary, FieldBoundary, BoundaryUpdate]): ...


org = CRUDOrg(Org)
farm = CRUDFarm(Farm)
org_farm = CRUDOrgFarm(OrgFarm)
field = CRUDField(Field)
boundary = CRUDFieldBoundary(FieldBoundary)
