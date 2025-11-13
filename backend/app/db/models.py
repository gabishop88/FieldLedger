from typing import ClassVar
from uuid import UUID

from geoalchemy2 import Geometry, WKTElement
from pydantic import EmailStr
from sqlmodel import Column, ForeignKey, Relationship, SQLModel
from sqlmodel import Field as ColInfo
from sqlmodel._compat import SQLModelConfig
from uuid6 import uuid7

# NOTE: I had to import `Field as ColInfo` since it conflicts with the `Field` table
# TODO: Should I separate the table models from the API models?
# TODO: Should I divide this into multiple files, possibly by schema?

# region ------------------------------- Miscellaneous ---------------------------------


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# endregion
# region -------------------------------- Schema: ref ----------------------------------


class BasicRef(SQLModel):
    name: str = ColInfo(primary_key=True, max_length=32)
    description: str | None = None


class FieldType(BasicRef, table=True):
    __tablename__: ClassVar[str] = "field_type"
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class BoundaryType(BasicRef, table=True):
    __tablename__: ClassVar[str] = "boundary_type"
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class EquipmentType(BasicRef, table=True):
    __tablename__: ClassVar[str] = "equipment_type"
    __table_args__: ClassVar[dict] = {"schema": "ref"}


class ProductType(BasicRef, table=True):
    __tablename__: ClassVar[str] = "product_type"
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    category: str | None = None


class Unit(BasicRef, table=True):
    __tablename__: ClassVar[str] = "unit"
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    category: str | None = None
    si_unit_name: str = ColInfo(
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    si_conv: float


class Crop(SQLModel, table=True):
    __tablename__: ClassVar[str] = "crop"
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    common_name: str
    latin_name: str
    description: str | None = None
    density: float | None = None

    density_unit_name: str | None = ColInfo(
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        )
    )
    density_unit: Unit = Relationship()


# endregion
# region -------------------------------- Schema: iam ----------------------------------


class UserBase(SQLModel):
    email: EmailStr = ColInfo(unique=True, index=True, max_length=255)
    is_superuser: bool = False
    full_name: str | None = None


class UserPublic(UserBase):
    id: UUID


class UsersPublic(SQLModel):
    count: int
    data: list[UserPublic]


class UserCreate(UserBase):
    password: str = ColInfo(min_length=8, max_length=255)


class UserRegister(SQLModel):
    email: EmailStr = ColInfo(max_length=255)
    password: str = ColInfo(min_length=8, max_length=255)
    full_name: str | None = None


class UserUpdate(UserBase):
    email: EmailStr | None = ColInfo(default=None, max_length=255)
    password: str | None = ColInfo(default=None, min_length=8, max_length=255)


class UserUpdateSelf(SQLModel):
    full_name: str | None = ColInfo(default=None, max_length=255)
    email: EmailStr | None = ColInfo(default=None, max_length=255)
    password: str | None = ColInfo(default=None, min_length=8, max_length=255)


class PasswordReset(SQLModel):
    token: str
    new_password: str = ColInfo(min_length=8, max_length=255)


class AppUser(UserBase, table=True):
    __tablename__: ClassVar[str] = "app_user"
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


class FarmUpdate(FarmBase):
    name: str | None = ColInfo(default=None, max_length=255)
    private: bool | None = None


class Farm(FarmBase, table=True):
    __tablename__: ClassVar[str] = "farm"
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class FarmsPublic(SQLModel):
    count: int
    data: list[Farm]


class FieldBase(SQLModel):
    name: str = ColInfo(nullable=False, max_length=255)
    type: str = ColInfo(
        sa_column=Column(
            ForeignKey("ref.field_type.name", onupdate="CASCADE", ondelete="RESTRICT")
        )
    )
    notes: str | None = None
    farm_id: UUID = ColInfo(foreign_key="asset.farm.id", ondelete="CASCADE")


class Field(FieldBase, table=True):
    __tablename__: ClassVar[str] = "field"
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class BoundaryBase(SQLModel, arbitrary_types_allowed=True):
    model_config = SQLModelConfig(arbitrary_types_allowed=True)  # type: ignore

    name: str | None = ColInfo(default=None, max_length=255)
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
    geom: WKTElement = ColInfo(
        sa_column=Column(
            Geometry("MULTIPOLYGON", 4326, spatial_index=True, nullable=False)
        )
    )
    field_id: UUID = ColInfo(foreign_key="asset.field.id", ondelete="CASCADE")


class FieldBoundary(BoundaryBase, table=True):
    __tablename__: ClassVar[str] = "field_boundary"
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


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
    __tablename__: ClassVar[str] = "product"
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
    __tablename__: ClassVar[str] = "equipment"
    __table_args__: ClassVar[dict] = {"schema": "asset"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
