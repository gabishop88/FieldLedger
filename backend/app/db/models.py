from collections.abc import Sequence
from typing import Annotated, ClassVar, TypeVar
from uuid import UUID

from geoalchemy2 import Geometry, WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from pydantic import EmailStr, field_serializer, field_validator
from shapely import wkt
from sqlmodel import Column, ForeignKey, Relationship, SQLModel
from sqlmodel import Field as ColInfo
from sqlmodel._compat import SQLModelConfig
from uuid6 import uuid7

from app.api.messages import ExeMsg

# NOTE: I had to import `Field as ColInfo` since it conflicts with the `Field` table
# TODO: Should I separate the table models from the API models?
# TODO: Should I divide this into multiple files, possibly by schema?

# region ------------------------------- Miscellaneous ---------------------------------


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires_min: int


T = TypeVar("T")


class Paginated[T](SQLModel):
    count: int
    data: Sequence[T]


# endregion
# region -------------------------------- Schema: ref ----------------------------------


class TypeRef(SQLModel):
    name: str = ColInfo(primary_key=True, max_length=32)
    description: str | None = None


class TypeRefUpdate(SQLModel):
    name: str | None = None
    description: str | None = None


class FieldType(TypeRef, table=True):
    __tablename__: ClassVar[str] = "field_type"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class BoundaryType(TypeRef, table=True):
    __tablename__: ClassVar[str] = "boundary_type"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class EquipmentType(TypeRef, table=True):
    __tablename__: ClassVar[str] = "equipment_type"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class ProductType(TypeRef, table=True):
    __tablename__: ClassVar[str] = "product_type"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    category: str | None = None


class Unit(TypeRef, table=True):
    __tablename__: ClassVar[str] = "unit"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    category: str | None = None
    si_unit_name: str = ColInfo(
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    si_conv: float


class UnitUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    si_unit_name: str | None = None
    si_conv: float | None = None


class CropBase(SQLModel):
    common_name: str
    latin_name: str
    family: str
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = ColInfo(
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        )
    )


class CropUpdate(SQLModel):
    common_name: str | None = None
    latin_name: str | None = None
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = None


# TODO: Make Crop.latin_name PK? Sstandardize the amount of detail (subsp, var, etc.)?
class Crop(CropBase, table=True):
    __tablename__: ClassVar[str] = "crop"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    density_unit: Unit = Relationship()


ReferencePublic = TypeRef | ProductType | Unit | Crop
ReferenceCreate = TypeRef | ProductType | Unit | CropBase
ReferenceUpdate = TypeRefUpdate | ProductType | UnitUpdate | CropUpdate


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

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    hashed_password: str


# endregion
# region ------------------------------- Schema: asset ---------------------------------


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
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class FieldBase(SQLModel):
    name: str = ColInfo(nullable=False, max_length=255)
    type: str = ColInfo(
        sa_column=Column(
            ForeignKey("ref.field_type.name", onupdate="CASCADE", ondelete="RESTRICT")
        )
    )
    notes: str | None = None
    farm_id: UUID = ColInfo(foreign_key="asset.farm.id", ondelete="CASCADE")


class FieldCreate(SQLModel):
    name: str = ColInfo(nullable=False, max_length=255)
    type: str
    notes: str | None = None


class FieldUpdate(SQLModel):
    name: str | None = ColInfo(default=None, max_length=255)
    type: str | None = None
    notes: str | None = None
    farm_id: UUID | None = None  # TODO: Allow field transfer?


class Field(FieldBase, table=True):
    __tablename__: ClassVar[str] = "field"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class BoundaryBase(SQLModel, arbitrary_types_allowed=True):
    model_config = SQLModelConfig(arbitrary_types_allowed=True)  # type: ignore

    type: str = ColInfo(
        sa_column=Column(
            ForeignKey(
                "ref.boundary_type.name", onupdate="CASCADE", ondelete="RESTRICT"
            )
        )
    )
    active: bool = True
    covered: bool = False
    notes: str | None = None
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
                raise ValueError(ExeMsg.INVALID_TOPO)
        except Exception:
            raise ValueError(ExeMsg.INVALID_WKT)

        return value

    @field_serializer("geom")
    def serialize_geom(self, value) -> str | None:
        if isinstance(value, WKBElement):
            return to_shape(value).wkt
        return value


class FieldBoundary(BoundaryBase, table=True):
    __tablename__: ClassVar[str] = "field_boundary"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    field_id: UUID = ColInfo(foreign_key="asset.field.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class BoundaryCreate(BoundaryBase):
    pass


class BoundaryUpdate(SQLModel):
    type: str | None = None
    active: bool | None = None
    covered: bool | None = None
    notes: str | None = None
    geom: Annotated[str, WKTElement] | None = None
    field_id: UUID | None = None


class ProductBase(SQLModel):
    name: str = ColInfo(max_length=255)
    type: str = ColInfo(
        sa_column=Column(
            ForeignKey(
                "ref.product_type.name", onupdate="CASCADE", ondelete="RESTRICT"
            ),
            nullable=False,
        )
    )
    company_name: str | None = None
    notes: str | None = None
    farm_id: UUID = ColInfo(foreign_key="asset.farm.id", ondelete="CASCADE")
    crop_id: UUID | None = ColInfo(foreign_key="ref.crop.id", ondelete="RESTRICT")


class Product(ProductBase, table=True):
    __tablename__: ClassVar[str] = "product"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class EquipmentBase(SQLModel):
    name: str = ColInfo(max_length=255)
    type: str = ColInfo(
        sa_column=Column(
            ForeignKey(
                "ref.equipment_type.name", onupdate="CASCADE", ondelete="RESTRICT"
            )
        )
    )
    make: str | None = None
    model: str | None = None
    notes: str | None = None
    farm_id: UUID = ColInfo(foreign_key="asset.farm.id", ondelete="CASCADE")


class Equipment(EquipmentBase, table=True):
    __tablename__: ClassVar[str] = "equipment"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
