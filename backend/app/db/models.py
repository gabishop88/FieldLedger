import json
from datetime import datetime
from functools import cached_property
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, ClassVar, Optional
from uuid import UUID
from zipfile import ZipFile

import geopandas
from geoalchemy2 import Geometry, WKBElement, WKTElement
from geoalchemy2.shape import to_shape
from pydantic import EmailStr, field_serializer, field_validator
from shapely import wkt
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import (
    TIMESTAMP,
    Column,
    DateTime,
    ForeignKey,
    LargeBinary,
    Relationship,
    SQLModel,
    String,
    UniqueConstraint,
    func,
    text,
)
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
    SyncStatus,
)

# TODO: Replace all x/x_unit values with a string and use the postgresql-unit extension?
# TODO: If using postgresql-unit, define an enum with the available units maybe per col
# TODO: Add changelog hooks here so they are more visible/explicit?

# region ------------------------------------ IAM -------------------------------------


class UserBase(SQLModel):
    email: EmailStr = ColInfo(unique=True, index=True, max_length=255)
    is_superuser: bool = False
    full_name: str | None = None


class AppUser(UserBase, table=True):
    __tablename__: ClassVar[str] = "app_user"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "iam"}

    hashed_password: str
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region --------------------------------- Structure ----------------------------------


class OrgBase(SQLModel):
    name: str = ColInfo(max_length=255, unique=True)
    description: str | None = None


class Org(OrgBase, table=True):
    __tablename__: ClassVar[str] = "org"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class FarmBase(SQLModel):
    name: str = ColInfo(max_length=255, unique=True)
    private: bool = False  # TODO: how do I use this with org being how it is? remove?
    description: str | None = None


class Farm(FarmBase, table=True):
    __tablename__: ClassVar[str] = "farm"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


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
                raise ValueError(ErrMsg.INVLD_TOPO)
        except Exception:
            raise ValueError(ErrMsg.INVLD_WKT)

        return value

    @field_serializer("geom")
    def serialize_geom(self, value) -> str | None:
        if isinstance(value, WKBElement):
            return to_shape(value).wkt
        return value


class FieldBoundary(BoundaryBase, table=True):
    __tablename__: ClassVar[str] = "field_boundary"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "structure"}

    field_id: UUID = ColInfo(foreign_key="structure.field.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region ------------------------------------ Ref -------------------------------------


# NOTE: This gets reused a LOT, hence the helper
def unit_fk(nullable=True):
    return ColInfo(
        default=None if nullable else ...,
        sa_column=Column(
            ForeignKey("ref.unit.name", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=nullable,
        ),
    )


class Unit(SQLModel, table=True):
    __tablename__: ClassVar[str] = "unit"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    name: str = ColInfo(primary_key=True, max_length=32)
    description: str | None = None
    category: str | None = None
    si_unit_name: str = unit_fk(nullable=False)
    si_conv: float


class CropBase(SQLModel):
    common_name: str
    latin_name: str
    family: str
    description: str | None = None
    density: float | None = None
    density_unit_name: str | None = unit_fk()


class Crop(CropBase, table=True):
    __tablename__: ClassVar[str] = "crop"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "ref"}

    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    density_unit: Unit = Relationship()


# endregion
# region ---------------------------------- Resource ----------------------------------


class ProductBase(SQLModel):
    name: str = ColInfo(max_length=255)
    brand: str | None = None
    type: ProductType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    notes: str | None = None
    crop_id: UUID | None = ColInfo(
        default=None, foreign_key="ref.crop.id", ondelete="RESTRICT"
    )


class Product(ProductBase, table=True):
    __tablename__: ClassVar[str] = "product"  # type: ignore
    __table_args__ = (
        UniqueConstraint("org_id", "name"),
        {"schema": "resource"},
    )

    org_id: UUID = ColInfo(foreign_key="structure.org.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


class EquipmentBase(SQLModel):
    name: str = ColInfo(max_length=255)
    type: EquipmentType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    make: str | None = None
    model: str | None = None
    year: int | None = None
    serial_number: str | None = None
    active: bool = True
    notes: str | None = None


class Equipment(EquipmentBase, table=True):
    __tablename__: ClassVar[str] = "equipment"  # type: ignore
    __table_args__ = (
        UniqueConstraint("org_id", "name"),
        {"schema": "resource"},
    )

    org_id: UUID = ColInfo(foreign_key="structure.org.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)


# endregion
# region --------------------------------- Operation ----------------------------------


class FieldOpBase(SQLModel):
    type: OpType = ColInfo(sa_column=Column("type", String(32), nullable=False))
    season: int
    start: datetime | None = ColInfo(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    end: datetime | None = ColInfo(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    crop_id: UUID | None = None
    area: float | None = None
    area_unit: str | None = unit_fk()
    boundary_id: UUID | None = ColInfo(
        default=None, foreign_key="structure.field_boundary.id", ondelete="CASCADE"
    )


class FieldOp(FieldOpBase, table=True):
    __tablename__: ClassVar[str] = "field_op"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    field_id: UUID = ColInfo(foreign_key="structure.field.id", ondelete="CASCADE")
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)
    inputs: list["OpInput"] = Relationship(back_populates="op")
    outputs: list["OpOutput"] = Relationship(back_populates="op")
    equipment: list["OpEquipment"] = Relationship(back_populates="op")


class OpInputBase(SQLModel):
    area: float | None = None
    area_unit: str | None = unit_fk()
    quantity: float | None = None
    quantity_unit: str | None = unit_fk()
    rate: float | None = None
    rate_unit: str | None = unit_fk()


class OpInput(OpInputBase, table=True):
    __tablename__: ClassVar[str] = "op_input"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    op_id: UUID = ColInfo(
        primary_key=True, foreign_key="operation.field_op.id", ondelete="CASCADE"
    )
    product_id: UUID = ColInfo(
        primary_key=True, foreign_key="resource.product.id", ondelete="RESTRICT"
    )
    op: FieldOp = Relationship(back_populates="inputs")


class OpOutputBase(SQLModel):
    area: float | None = None
    area_unit: str | None = unit_fk()
    wet_mass_total: float | None = None
    wet_mass_total_unit: str | None = unit_fk()
    wet_mass_rate: float | None = None
    wet_mass_rate_unit: str | None = unit_fk()
    yield_total: float | None = None
    yield_total_unit: str | None = unit_fk()
    yield_rate: float | None = None
    yield_rate_unit: str | None = unit_fk()
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
    op: FieldOp = Relationship(back_populates="outputs")


class OpEquipmentBase(SQLModel):
    speed: float | None = None
    speed_unit: str | None = unit_fk()
    pressure: float | None = None
    pressure_unit: str | None = unit_fk()
    depth: float | None = None
    depth_unit: str | None = unit_fk()


class OpEquipment(OpEquipmentBase, table=True):
    __tablename__: ClassVar[str] = "op_equipment"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "operation"}

    op_id: UUID = ColInfo(
        primary_key=True, foreign_key="operation.field_op.id", ondelete="CASCADE"
    )
    equipment_id: UUID = ColInfo(
        primary_key=True, foreign_key="resource.equipment.id", ondelete="RESTRICT"
    )
    op: FieldOp = Relationship(back_populates="equipment")


# endregion
# region -------------------------------- Integration ---------------------------------


# TODO: Add a column that let's me track the current reason that it is not connected?
#   it would start out saying that it just hasn't been connected, but could also hold
#   errors when they are given by john deere.
# TODO: I am storing tokens as plaintext. I need to encrypt them, but SECREY_KEY
#   in settings changes when the API starts. I need a stable key for refresh_token
# NOTE: Right now, connection is based on user_id. This is mostly to prevent any
#   complications from multiple users being able to sync. Could replace pk with id
class JDConnection(SQLModel, table=True):
    __tablename__: ClassVar[str] = "jd_connection"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "integration"}

    access_token: str | None = None
    refresh_token: str | None = None
    access_expires_at: datetime | None = ColInfo(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    first_established: datetime | None = ColInfo(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    user_id: UUID = ColInfo(
        foreign_key="iam.app_user.id", ondelete="CASCADE", primary_key=True
    )

    records: list["JDRecordLink"] = Relationship(
        back_populates="connection",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# TODO: Is is possible to add a type parameter like JDRecordLink[Org] but still only
# store model.__tablename__ in table_name?
class JDRecordLink(SQLModel, table=True):
    __tablename__: ClassVar[str] = "jd_record_link"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "integration"}

    uri: str
    data: dict[str, Any] = ColInfo(sa_column=Column(JSONB, nullable=False))
    status: SyncStatus = ColInfo(
        SyncStatus.Unsynced, sa_column=Column("sync_status", String(32), nullable=False)
    )
    local_persistent: bool = False
    # last_sync: datetime
    table_name: str
    table_key: dict[str, Any] | None = ColInfo(None, sa_column=Column(JSONB))
    parent_id: UUID | None = ColInfo(
        None, foreign_key="integration.jd_record_link.id", ondelete="CASCADE"
    )
    user_id: UUID = ColInfo(
        foreign_key="integration.jd_connection.user_id", ondelete="CASCADE"
    )
    id: UUID = ColInfo(default_factory=uuid7, primary_key=True)

    connection: JDConnection = Relationship(back_populates="records")
    # NOTE: Optional["X"] rather than "X | None" because the latter made the API crash
    parent: Optional["JDRecordLink"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "JDRecordLink.id"},
    )
    children: list["JDRecordLink"] = Relationship(back_populates="parent")
    # NOTE: Shapefile only used for table_name == "field_op"
    shapefile: Optional["JDShapefile"] = Relationship(
        back_populates="record_link",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    @cached_property
    def child_uris(self) -> set[str]:
        return {x.uri for x in self.children}


class JDShapefile(SQLModel, table=True):
    __tablename__: ClassVar[str] = "jd_shapefile"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "integration"}

    zip_data: bytes = ColInfo(sa_type=LargeBinary)
    link_id: UUID = ColInfo(
        foreign_key="integration.jd_record_link.id",
        ondelete="CASCADE",
        primary_key=True,
    )
    record_link: JDRecordLink = Relationship(back_populates="shapefile")

    # TODO: Is this potentially too large to cache if there are many?
    @cached_property
    def gdf(self) -> geopandas.GeoDataFrame:
        """Extract and return the shapefile as a geopandas GeoDataFrame."""
        with TemporaryDirectory() as tmp:
            ZipFile(BytesIO(self.zip_data)).extractall(tmp)
            return geopandas.read_file(next(Path(tmp).rglob("*.shp")))

    @cached_property
    def shp_meta(self) -> dict:
        """Extract and return the metadata .json attached to the shapefile."""
        with TemporaryDirectory() as tmp:
            ZipFile(BytesIO(self.zip_data)).extractall(tmp)
            path = next(Path(tmp).rglob("*.json"))
            return json.load(path.open())


# endregion
# region ----------------------------------- Audit ------------------------------------


# NOTE: model has `schema_name` attr to not override BaseModel. Table col name 'schema'.
class Changelog(SQLModel, table=True):
    __tablename__: ClassVar[str] = "changelog"  # type: ignore
    __table_args__: ClassVar[dict] = {"schema": "audit"}

    timestamp: datetime = ColInfo(
        sa_column=Column(
            TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
        )
    )
    revision: str = ColInfo(max_length=32)
    schema_name: str = ColInfo(sa_column=Column("schema", String(32), nullable=False))
    table: str = ColInfo(max_length=32)
    op: str = ColInfo(max_length=32)
    role: str = ColInfo(
        sa_column=Column(
            String(32), nullable=False, server_default=text("SESSION_USER")
        )
    )
    new_data: dict[str, Any] | None = ColInfo(None, sa_column=Column(JSONB))
    old_data: dict[str, Any] | None = ColInfo(None, sa_column=Column(JSONB))
    app_user: dict[str, Any] | None = ColInfo(None, sa_column=Column(JSONB))
    id: UUID = ColInfo(primary_key=True, default_factory=uuid7)


# TODO: add audit table for storing webhook events.


# endregion
