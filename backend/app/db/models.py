from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, ClassVar, TypeVar
from uuid import UUID

from geoalchemy2 import Geometry, WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from pydantic import EmailStr, field_serializer, field_validator
from shapely import wkt
from sqlmodel import (
    Column,
    ForeignKey,
    Relationship,
    SQLModel,
    String,
    UniqueConstraint,
)

# NOTE: Importing `Field as ColInfo` to avoid a conflict with the `Field` model below.
from sqlmodel import Field as ColInfo
from sqlmodel._compat import SQLModelConfig
from uuid6 import uuid7

from app.core.enums import (
    BoundaryType,
    EquipmentType,
    ErrMsg,
    FieldType,
    OpType,
    OrgFarmType,
    ProductType,
)

# TODO: For the crop tables: Make a CropCreate and CropPublic? Remove density_unit?
# TODO: Make alt xPublic classes w/ Relationships, requested via query param or smth?
# TODO: Replace all x/x_unit values with a string and use the postgresql-unit extension?
# TODO: If using postgresql-unit, define an enum with the available units maybe per col

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
# region -------------------------------- Schema: ref ----------------------------------


class UnitUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    si_unit_name: str | None = None
    si_conv: float | None = None


class Unit(SQLModel, table=True):
    __tablename__: ClassVar[str] = "unit"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    name: str = ColInfo(primary_key=True, max_length=32)
    description: str | None = None
    category: str | None = None
    si_unit_name: str = ColInfo(
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    si_conv: float


class CropBase(SQLModel):
    common_name: str
    latin_name: str
    family: str
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = ColInfo(
        default=None,
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
    )


class CropUpdate(SQLModel):
    common_name: str | None = None
    latin_name: str | None = None
    family: str | None = None
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = None


class Crop(CropBase, table=True):
    __tablename__: ClassVar[str] = "crop"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    density_unit: Unit = Relationship()


AnyReferencePublic = TypeEnumPublic | Crop | Unit

# endregion
# region -------------------------------- Schema: iam ----------------------------------


class UserBase(SQLModel):
    email: EmailStr = ColInfo(unique=True, index=True, max_length=255)
    is_superuser: bool = False
    full_name: str | None = None


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


class PasswordReset(SQLModel):
    token: str
    new_password: str = ColInfo(min_length=8, max_length=255)


class AppUser(UserBase, table=True):
    __tablename__: ClassVar[str] = "app_user"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "iam"}

    hashed_password: str
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region ----------------------------- Schema: structure ------------------------------


class OrgBase(SQLModel):
    name: str = ColInfo(max_length=255, unique=True)
    description: str | None = None


class OrgCreate(OrgBase):
    pass


class OrgUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class Org(OrgBase, table=True):
    __tablename__: ClassVar[str] = "org"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class FarmBase(SQLModel):
    name: str = ColInfo(max_length=255, unique=True)
    private: bool = False
    description: str | None = None


class FarmCreate(FarmBase):
    pass


class FarmUpdate(SQLModel):
    name: str | None = ColInfo(default=None, max_length=255)
    private: bool | None = None
    description: str | None = None


class Farm(FarmBase, table=True):
    __tablename__: ClassVar[str] = "farm"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class OrgFarmUpsert(SQLModel):
    type: OrgFarmType


class OrgFarmPublic(SQLModel):
    org_id: UUID
    farm_id: UUID
    type: OrgFarmType | None = None


class OrgFarm(SQLModel, table=True):
    __tablename__: ClassVar[str] = "org_farm"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    type: OrgFarmType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    org_id: UUID = ColInfo(
        primary_key=True, foreign_key="structure.org.id", ondelete="CASCADE"
    )
    farm_id: UUID = ColInfo(
        primary_key=True, foreign_key="structure.farm.id", ondelete="CASCADE"
    )


class FieldBase(SQLModel):
    name: str = ColInfo(nullable=False, max_length=255)
    type: FieldType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    description: str | None = None


class FieldCreate(FieldBase):
    pass


class FieldUpdate(SQLModel):
    name: str | None = ColInfo(default=None, max_length=255)
    type: FieldType | None = None
    description: str | None = None
    # farm_id: UUID | None = None  # TODO: Allow field transfer?


class Field(FieldBase, table=True):
    __tablename__: ClassVar[str] = "field"  # type: ignore
    __table_args__ = (
        UniqueConstraint("farm_id", "name"),
        {"schema": "structure"},
    )

    farm_id: UUID = ColInfo(foreign_key="structure.farm.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class BoundaryBase(SQLModel, arbitrary_types_allowed=True):
    model_config = SQLModelConfig(arbitrary_types_allowed=True)  # type: ignore

    type: BoundaryType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    active: bool = True
    covered: bool = False
    description: str | None = None
    geom: Annotated[str, WKTElement] = ColInfo(
        sa_column=Column(
            Geometry("MULTIPOLYGON", 4326, spatial_index=True, nullable=False)
        )
    )

    @field_validator("geom")
    @classmethod
    def validate_wkt(cls, value):
        try:
            shapely_geom = wkt.loads(value)
            if shapely_geom.is_empty or not shapely_geom.is_valid:
                raise ValueError(ErrMsg.INVALID_TOPO)
        except Exception:
            raise ValueError(ErrMsg.INVALID_WKT)

        return value

    @field_serializer("geom")
    def serialize_geom(self, value) -> str | None:
        if isinstance(value, WKBElement):
            return to_shape(value).wkt
        return value


class BoundaryCreate(BoundaryBase):
    pass


class BoundaryUpdate(SQLModel):
    type: BoundaryType | None = None
    active: bool | None = None
    covered: bool | None = None
    description: str | None = None
    geom: Annotated[str, WKTElement] | None = None
    field_id: UUID | None = None


class FieldBoundary(BoundaryBase, table=True):
    __tablename__: ClassVar[str] = "field_boundary"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    field_id: UUID = ColInfo(foreign_key="structure.field.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region ------------------------------ Schema: resource ------------------------------


class ProductBase(SQLModel):
    name: str = ColInfo(max_length=255)
    brand: str | None = None
    type: ProductType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    notes: str | None = None
    org_id: UUID = ColInfo(foreign_key="structure.org.id", ondelete="CASCADE")
    crop_id: UUID | None = ColInfo(
        default=None, foreign_key="ref.crop.id", ondelete="RESTRICT"
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    name: str | None = None
    brand: str | None = None
    type: ProductType | None = None
    notes: str | None = None
    org_id: UUID | None = None
    crop_id: UUID | None = None


class Product(ProductBase, table=True):
    __tablename__: ClassVar[str] = "product"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "resource"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class EquipmentBase(SQLModel):
    name: str = ColInfo(max_length=255)
    type: EquipmentType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    make: str | None = None
    model: str | None = None
    year: int | None = None
    active: bool = True
    notes: str | None = None


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


class Equipment(EquipmentBase, table=True):
    __tablename__: ClassVar[str] = "equipment"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "resource"}

    org_id: UUID = ColInfo(foreign_key="structure.org.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region ----------------------------- Schema: operation ------------------------------


class FieldOpBase(SQLModel):
    type: OpType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    season: int
    start: datetime | None = None
    end: datetime | None = None
    crop_id: UUID | None = None
    area: float | None = None
    area_unit: str | None = None


class FieldOp(FieldOpBase, table=True):
    __tablename__: ClassVar[str] = "field_op"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class OpInputBase(SQLModel):
    area: float | None = None
    area_unit: str | None = None
    quantity: float | None = None
    quantity_unit: str | None = None
    rate: float | None = None
    rate_unit: str | None = None


class OpInput(OpInputBase, table=True):
    __tablename__: ClassVar[str] = "op_input"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    op_id: UUID = ColInfo(
        primary_key=True, foreign_key="operation.field_op.id", ondelete="CASCADE"
    )
    product_id: UUID = ColInfo(
        primary_key=True, foreign_key="resource.product.id", ondelete="RESTRICT"
    )


class OpOutputBase(SQLModel):
    area: float | None = None
    area_unit: str | None = None
    wet_mass_total: float | None = None
    wet_mass_total_unit: str | None = None
    wet_mass_rate: float | None = None
    wet_mass_rate_unit: str | None = None
    yield_total: float | None = None
    yield_total_unit: str | None = None
    yield_rate: float | None = None
    yield_rate_unit: str | None = None
    moisture_pct: float | None = None


class OpOutput(OpOutputBase, table=True):
    __tablename__: ClassVar[str] = "op_output"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    op_id: UUID = ColInfo(
        primary_key=True, foreign_key="operation.field_op.id", ondelete="CASCADE"
    )
    product_id: UUID = ColInfo(
        primary_key=True, foreign_key="resource.product.id", ondelete="RESTRICT"
    )


class OpEquipmentBase(SQLModel):
    speed: float | None = None
    speed_unit: str | None = None
    pressure: float | None = None
    pressure_unit: str | None = None
    depth: float | None = None
    depth_unit: str | None = None


class OpEquipment(OpEquipmentBase, table=True):
    __tablename__: ClassVar[str] = "op_equipment"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    op_id: UUID = ColInfo(
        primary_key=True, foreign_key="operation.field_op.id", ondelete="CASCADE"
    )
    equipment_id: UUID = ColInfo(
        primary_key=True, foreign_key="resource.equipment.id", ondelete="RESTRICT"
    )


# endregion
