from datetime import datetime
from typing import Any, ClassVar, Literal

from pydantic import AliasChoices, BaseModel, field_validator
from pydantic import Field as ColInfo

# region -------------------------------- Core Models ---------------------------------


class JDBaseModel(BaseModel):
    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("exclude_unset", True)
        kwargs.setdefault("exclude_defaults", True)
        return super().model_dump(**kwargs)


class JDLink(JDBaseModel):
    rel: str
    uri: str


class Meas(JDBaseModel):
    value: float = ColInfo(validation_alias=AliasChoices("value", "valueAsDouble"))
    unit: str


class JDModel(JDBaseModel):
    keep_links: ClassVar[set[str]] = {"self", "owningOrganization"}
    links: list[JDLink]

    def linked(self, rel: str) -> str:
        """Get the uri of a link in `self.links`"""
        assert rel in self.keep_links, f"{rel=} not in {self.keep_links}."
        return next(link for link in self.links if link.rel == rel).uri

    @property
    def uri(self) -> str:
        return self.linked("self")

    @field_validator("links", mode="before")
    @classmethod
    def filter_links(cls, value):
        return [link for link in value if link.get("rel") in cls.keep_links]


class JDMulti[ContentModel: JDModel](JDModel):
    total: int
    values: list[ContentModel]


# endregion
# region --------------------------- Org/Farm/Field Models ----------------------------


class JDOrg(JDModel):
    keep_links: ClassVar[set[str]] = {"self", "connection", "farms"}

    name: str
    member: bool
    id: str
    links: list[JDLink]

    @property
    def has_conn_link(self) -> bool:
        return "connections" in {link.rel for link in self.links}


class JDFarm(JDModel):
    keep_links: ClassVar[set[str]] = {"self", "fields", "owningOrganization"}
    name: str
    archived: bool
    id: str
    links: list[JDLink]


class JDField(JDModel):
    # NOTE: maybes: "farms", "simplifiedBoundaries"
    keep_links: ClassVar[set[str]] = {
        "self",
        "owningOrganization",
        "boundaries",
        "fieldOperation",
    }
    name: str
    archived: bool
    id: str
    links: list[JDLink]


# endregion
# region ------------------------------ Boundary Models -------------------------------


class Point(JDBaseModel):
    lat: float
    lon: float


class Polygon(JDBaseModel):
    rings: list[Point]
    type: Literal["interior", "exterior"]


class JDBoundary(JDModel):
    keep_links: ClassVar[set[str]] = {"self", "owningOrganization"}
    name: str
    area: Meas
    workableArea: Meas
    multipolygons: list[Polygon]
    centroid: Point
    archived: bool
    id: str
    links: list[JDLink]
    active: bool
    irrigated: bool


# endregion
# region ------------------------------ Operation Models ------------------------------


class JDVarietyTotal(JDBaseModel):
    varietyId: str
    name: str | None = None
    area: Meas
    # Harvest Ops
    yield_: Meas | None = ColInfo(None, alias="yield")
    averageYield: Meas | None = None
    averageMoisture: Meas | None = None
    wetMass: Meas | None = None
    averageWetMass: Meas | None = None
    # Seeding Ops
    totalMaterial: Meas | None = None
    averageMaterial: Meas | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class JDProductTotal(JDBaseModel):
    productId: str
    name: str | None = None
    brand: str | None = None
    totalMaterial: Meas
    averageMaterial: Meas


class JDAppTotal(JDBaseModel):
    productId: str
    name: str | None = None
    area: Meas
    averageSpeed: Meas
    totalMaterial: Meas
    averageMaterial: Meas
    appliedArea: Meas | None = None
    productTotals: list[JDProductTotal]


class JDOpMeas(JDBaseModel):
    measurementName: str
    area: Meas | None = None
    # Application Ops
    applicationProductTotals: list[JDAppTotal] | None = None
    # Seeding Ops
    totalMaterial: Meas | None = None
    averageMaterial: Meas | None = None
    # Harvest Ops
    yield_: Meas | None = ColInfo(None, alias="yield")
    averageYield: Meas | None = None
    averageMoisture: Meas | None = None
    wetMass: Meas | None = None
    averageWetMass: Meas | None = None
    averageSpeed: Meas | None = None
    # Tillage Ops
    averageDepth: Meas | None = None
    averagePressure: Meas | None = None

    varietyTotals: list[JDVarietyTotal] | None = None
    productTotals: list[JDProductTotal] | None = None

    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class JDComponent(JDBaseModel):
    name: str
    rate: Meas
    guid: str
    productType: str


class JDProduct(JDBaseModel):
    guid: str
    productType: str | None = None
    productId: str
    name: str | None = None
    brand: str | None = None

    tankMix: bool
    rate: Meas | None = None
    carrier: JDComponent | None = None
    components: list[JDComponent] | None = None


class JDOpMachine(JDBaseModel):
    name: str | None = None
    vin: str | None = None
    GUID: str
    machineId: str | None = None


class JDTillageProduct(JDBaseModel):
    tillageType: str


class JDFieldOp(JDModel):
    # Maybe keep: "field" (should I keep parent links?)
    # NOTE: using self link + '/boundary' generates a boundary for the op.
    keep_links: ClassVar[set[str]] = {"self", "organization", "shapeFileAsync"}
    fieldOperationType: str
    adaptMachineType: str | None = None
    cropSeason: int
    startDate: datetime
    endDate: datetime
    cropName: str | None = None

    products: list[JDProduct] | None = None
    # measurementTypes
    fieldOperationMachines: list[JDOpMachine] | None = None
    tillageProducts: list[JDTillageProduct] | None = None
    varieties: list[JDProduct] | None = None
    id: str
    links: list[JDLink]


# endregion
