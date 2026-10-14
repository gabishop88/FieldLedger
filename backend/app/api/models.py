from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any, TypeVar
from uuid import UUID

from geoalchemy2 import WKTElement
from pydantic import EmailStr
from sqlmodel import Field as ColInfo
from sqlmodel import SQLModel

from app.core.enums import (
    BoundaryType,
    EquipmentType,
    FieldType,
    OrgFarmType,
    ProductType,
    SyncStatus,
)
from app.db.models import (
    BoundaryBase,
    Crop,
    EquipmentBase,
    FarmBase,
    FieldBase,
    FieldOpBase,
    OpEquipmentBase,
    OpInputBase,
    OpOutputBase,
    OrgBase,
    ProductBase,
    Unit,
    UserBase,
)

# TODO: For the crop tables: Make a CropCreate and CropPublic? Remove density_unit?
# TODO: Make alt xPublic classes w/ Relationships, requested via query param or smth?
# TODO: Clean up inconsistency on whether parent ids can be upated in Update schemas.

# region ------------------------------- Miscellaneous ---------------------------------

T = TypeVar("T")


class Paginated[T](SQLModel):
    count: int
    data: Sequence[T]


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires_min: int


class TypeEnumPublic(SQLModel):
    name: str
    description: str | None


# endregion
# region ------------------------------------ IAM -------------------------------------


class UserPublic(UserBase):
    id: UUID


class UserCreate(UserBase):
    password: str = ColInfo(min_length=8, max_length=255)


class UserRegister(SQLModel):
    email: EmailStr = ColInfo(max_length=255)
    password: str = ColInfo(min_length=8, max_length=255)
    full_name: str | None = None


class UserUpdate(SQLModel):
    email: EmailStr | None = ColInfo(default=None, max_length=255)
    password: str | None = ColInfo(default=None, min_length=8, max_length=255)
    is_superuser: bool = False
    full_name: str | None = None


class UserUpdateSelf(SQLModel):
    full_name: str | None = ColInfo(default=None, max_length=255)
    email: EmailStr | None = ColInfo(default=None, max_length=255)
    password: str | None = ColInfo(default=None, min_length=8, max_length=255)


class LoginBody(SQLModel):
    username: EmailStr
    password: str


class PasswordReset(SQLModel):
    token: str
    new_password: str = ColInfo(min_length=8, max_length=255)


# endregion
# region --------------------------------- Structure ----------------------------------


class OrgCreate(OrgBase):
    pass


class OrgUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(SQLModel):
    name: str | None = ColInfo(default=None, max_length=255)
    private: bool | None = None
    description: str | None = None


class OrgFarmUpsert(SQLModel):
    type: OrgFarmType


class OrgFarmPublic(SQLModel):
    type: OrgFarmType | None = None
    org_id: UUID
    farm_id: UUID


class FieldCreate(FieldBase):
    pass


class FieldUpdate(SQLModel):
    name: str | None = ColInfo(default=None, max_length=255)
    type: FieldType | None = None
    description: str | None = None
    # farm_id: UUID | None = None  # TODO: Allow field transfer?


class BoundaryCreate(BoundaryBase):
    pass


class BoundaryUpdate(SQLModel):
    type: BoundaryType | None = None
    active: bool | None = None
    covered: bool | None = None
    description: str | None = None
    geom: Annotated[str, WKTElement] | None = None
    field_id: UUID | None = None


# endregion
# region ------------------------------------ Ref -------------------------------------


class UnitUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    si_unit_name: str | None = None
    si_conv: float | None = None


class CropUpdate(SQLModel):
    common_name: str | None = None
    latin_name: str | None = None
    family: str | None = None
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = None


AnyReferencePublic = TypeEnumPublic | Crop | Unit

# endregion
# region ---------------------------------- Resource ----------------------------------


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    name: str | None = None
    brand: str | None = None
    type: ProductType | None = None
    notes: str | None = None
    org_id: UUID | None = None
    crop_id: UUID | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(SQLModel):
    name: str | None = None
    type: EquipmentType | None = None
    make: str | None = None
    model: str | None = None
    active: bool | None = None
    notes: str | None = None
    # org_id: UUID | None = None


# endregion
# region --------------------------------- Operation ----------------------------------


class FieldOpUpdate(SQLModel):
    type: str | None = None
    season: int | None = None
    start: datetime | None = None
    end: datetime | None = None
    crop_id: UUID | None = None
    area: float | None = None
    area_unit: str | None = None
    boundary_id: UUID | None = None


class FieldOpCreate(FieldOpBase):
    pass


class OpInputCreate(OpInputBase):
    pass


class OpInputUpdate(OpInputBase):
    pass


class OpInputPublic(OpInputBase):
    op_id: UUID
    product_id: UUID


class OpOutputCreate(OpOutputBase):
    pass


class OpOutputUpdate(OpOutputBase):
    pass


class OpOutputPublic(OpOutputBase):
    op_id: UUID
    product_id: UUID


class OpEquipmentCreate(OpEquipmentBase):
    pass


class OpEquipmentUpdate(OpEquipmentBase):
    pass


class OpEquipmentPublic(OpEquipmentBase):
    op_id: UUID
    equipment_id: UUID


class BulkResource(SQLModel):
    inputs: list[OpInputPublic]
    outputs: list[OpOutputPublic]
    equipment: list[OpEquipmentPublic]


# endregion
# region -------------------------------- Integration ---------------------------------


class AuthPublic(SQLModel):
    authorized: bool
    auth_uri: str | None = None


class JDConnectionUpdate(SQLModel):
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    first_established: datetime | None = None


# TODO: Reduce this down to just what the frontend needs?
class SyncTreeNode(SQLModel):
    uri: str
    data: dict[str, Any]
    status: SyncStatus
    local_persistent: bool
    table_name: str
    table_key: dict | None
    id: UUID

    children: list["SyncTreeNode"]


class JDLinkUpdate(SQLModel):
    """Since this is not a simple update, every field is handled in
    `integrations.jd.sync.modify_sync separately.
    """

    status: SyncStatus | None = None
    local_persistent: bool | None = None


class SyncLinkUpdate(SQLModel):
    """This is an update model designed to be used internally when syncing."""

    data: dict[str, Any] | None = None
    table_key: dict[str, Any] | None = None
    local_persistent: bool | None = None


# endregion
