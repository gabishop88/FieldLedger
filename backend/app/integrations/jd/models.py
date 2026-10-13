import logging
from copy import deepcopy
from datetime import datetime
from functools import cached_property
from typing import Any, ClassVar, Literal, overload

from pydantic import AliasChoices, BaseModel, field_validator, model_validator
from pydantic import Field as ColInfo
from shapely import MultiPolygon, Point, Polygon

from app.core.config import settings

# TODO: Go through and remove all fields that I don't need/use?
# TODO: Go through and remove "---" placeholder values (often in companyName, name, etc)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

JDProductType = Literal["SEED", "CHEMICAL", "FERTILIZER"]

# region -------------------------------- Core Models ---------------------------------


class JDBaseModel(BaseModel):
    def model_dump(self, **kwargs) -> dict[str, Any]:
        kwargs.setdefault("exclude_unset", True)
        kwargs.setdefault("exclude_defaults", True)
        return super().model_dump(**kwargs)

    @model_validator(mode="before")
    @classmethod
    def remove_placeholders(cls, data: Any) -> Any:
        placeholders = ("---", "unknown")
        if isinstance(data, dict):
            return {k: None if v in placeholders else v for k, v in data.items()}
        return data


class JDLink(JDBaseModel):
    rel: str
    uri: str


class Meas(JDBaseModel):
    value: float = ColInfo(
        validation_alias=AliasChoices("value", "Value", "valueAsDouble")
    )
    unit: str = ColInfo(validation_alias=AliasChoices("unit", "Unit", "unitId"))


_MISSING = object()

class JDModel(JDBaseModel):
    keep_links: ClassVar[set[str]] = {"self", "owningOrganization", "organization"}
    links: list[JDLink]

    @overload
    def get_link(self, rel: str) -> JDLink: ...

    @overload
    def get_link[T](self, rel: str, default: T) -> JDLink | T: ...

    def get_link(self, rel: str, default=_MISSING):
        """###Get a link from `self.links` by `rel`.
        See `self.keep_links` to see the possible values of `rel`.

        Raises LookupError if rel is not found,
        unless a default value is given as a second argument.
        """
        link = next((x for x in self.links if x.rel == rel), default)
        if link is _MISSING:
            raise LookupError(f"No link with {rel=}")
        return link

    @cached_property
    def uri(self) -> str:
        """This is a resource's identifier: 'self' link minus protocol/domain."""
        uri = self.get_link("self").uri
        if uri.startswith(settings.JD_API_BASE):
            uri = uri[len(settings.JD_API_BASE) :].lstrip("/")
        return uri

    @field_validator("links", mode="before")
    @classmethod
    def filter_links(cls, value):
        return [link for link in value if link.get("rel") in cls.keep_links]


class JDMulti[ContentModel: JDModel](JDModel):
    keep_links = JDModel.keep_links | {"nextPage",}

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
    name: str | None
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


class JDPoint(JDBaseModel):
    lat: float
    lon: float

    def as_shapely(self) -> Point:
        return Point(self.lon, self.lat)


class JDExtent(JDBaseModel):
    topLeft: JDPoint
    bottomRight: JDPoint


class JDRing(JDBaseModel):
    points: list[JDPoint]
    type: Literal["interior", "exterior"]

    @property
    def coords(self) -> list[tuple[float, float]]:
        return [(p.lon, p.lat) for p in self.points]


class JDPolygon(JDBaseModel):
    rings: list[JDRing]

    def as_shapely(self) -> Polygon:
        return Polygon(
            shell=next(r for r in self.rings if r.type == "exterior").coords,
            holes=[r.coords for r in self.rings if r.type == "interior"],
        )


class JDBoundary(JDModel):
    keep_links: ClassVar[set[str]] = {"self", "owningOrganization"}
    name: str
    area: Meas | None = None
    workableArea: Meas | None = None
    multipolygons: list[JDPolygon]
    centroid: JDPoint | None = None
    extent: JDExtent | None = None
    archived: bool
    id: str | None = None
    links: list[JDLink]
    active: bool
    irrigated: bool

    def as_shapely(self) -> MultiPolygon:
        return MultiPolygon([p.as_shapely() for p in self.multipolygons])

    @property
    def wkt(self) -> str:
        """Well-Known-Text representation of the boundary geometry."""
        return self.as_shapely().wkt

    @model_validator(mode="before")
    @classmethod
    def log_invalid_multipolygons(cls, data):
        if (
            isinstance(data, dict)
            and (
                "multipolygons" not in data
                or not data["multipolygons"]
                or "rings" not in data["multipolygons"][0]
            )
        ):
            log.error("Invalid JDBoundary: %r", data)

        return data


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


class JDMeasType(JDBaseModel):
    measurementName: str
    area: Meas | None = None
    # Application Ops
    applicationProductTotals: list[JDAppTotal] | None = None
    # Seeding Ops
    totalMaterial: Meas | None = None
    averageMaterial: Meas | None = None
    # Harvest Ops
    yield_: Meas | None = ColInfo(default=None, alias="yield")
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


# TODO: Do any of these need `area` outside of the whole JDMeasurement?
class InputMeasurement(JDBaseModel):
    guid: str
    area: Meas | None = None
    total: Meas | None = None
    rate: Meas | None = None


class OutputMeasurement(JDBaseModel):
    guid: str
    area: Meas | None = None
    wet_mass: Meas | None = None
    wet_mass_rate: Meas | None = None
    yield_: Meas | None = ColInfo(
        default=None, validation_alias="yield", serialization_alias="yield"
    )
    yield_rate: Meas | None = None
    moisture: Meas | None = None


class EquipmentMeasurement(JDBaseModel):
    # some id
    area: Meas | None = None
    speed: Meas | None = None
    pressure: Meas | None = None
    depth: Meas | None = None


class JDMeasurement(JDBaseModel):
    area: Meas | None = None
    # speed: Meas | None = None
    # pressure: Meas | None = None
    # depth: Meas | None = None

    inputs: list[InputMeasurement] = ColInfo(default_factory=list)
    outputs: list[OutputMeasurement] = ColInfo(default_factory=list)
    eq: EquipmentMeasurement | None = None
    # inputs: dict[str, InputMeasurements] = ColInfo(default_factory=dict)
    # outputs: dict[str, OutputMeasurements] = ColInfo(default_factory=dict)


class JDComponent(JDBaseModel):
    name: str
    rate: Meas
    guid: str
    productType: JDProductType | None = None


class JDProduct(JDBaseModel):
    guid: str
    productType: JDProductType | None = None
    productId: str
    name: str | None = None
    brand: str | None = None

    tankMix: bool
    rate: Meas | None = None
    carrier: JDComponent | None = None
    components: list[JDComponent] | None = None

    @field_validator("productType", mode="before")
    def remove_product_type_other(cls, value):
        return None if value == "OTHER" else value


class JDOpMachine(JDBaseModel):
    name: str | None = None
    vin: str | None = None
    GUID: str
    machineId: int | None = None


class JDTillageProduct(JDBaseModel):
    tillageType: str | None = None


class JDFieldOp(JDModel):
    # Maybe keep: rel "field" (should I keep parent links?)
    keep_links: ClassVar[set[str]] = {"self", "organization", "shapeFileAsync"}
    fieldOperationType: str
    adaptMachineType: str | None = None
    cropSeason: int
    startDate: datetime
    endDate: datetime
    cropName: str | None = None

    products: list[JDProduct] | None = None
    measurementTypes: list[JDMeasType] | None = None
    fieldOperationMachines: list[JDOpMachine] | None = None
    tillageProducts: list[JDTillageProduct] | None = None
    varieties: list[JDProduct] | None = None
    id: str
    links: list[JDLink]

    @cached_property
    def measurements(self) -> JDMeasurement:
        return parse_measurements(self)

    @property
    def generate_boundary_uri(self) -> str:
        return f"{self.get_link('self').uri}/boundary"


# endregion
# region ------------------------------ Shapefile Models ------------------------------


class JDShpMetaDataAttribute(JDBaseModel):
    Name: str
    Unit: str | None = None
    Description: str


class JDShpMetaComponent(JDBaseModel):
    Carrier: bool
    Name: str
    Rate: Meas
    BrandName: str | None = None


class JDShpMetaProduct(JDBaseModel):
    ProductId: str
    ProductName: str
    BrandName: str | None = None
    TankMix: bool
    Rate: Meas
    ProductUseHash: str
    Components: list[JDShpMetaComponent]


class JDShpMetaMachineUse(JDBaseModel):
    MachineId: str
    MachineSerial: str
    PrincipalId: str | None = None


class JDShpMeta(JDBaseModel):
    OrgId: int
    FarmId: str
    FarmName: str
    FieldId: str
    FieldName: str
    FieldOperationId: str
    Operation: str
    CropSeason: int
    CropToken: str | None = None
    CropName: str | None = None
    Product: JDShpMetaProduct | None = None
    FieldOperationStartDate: datetime
    FileCreatedTimeStamp: datetime
    DataAttributes: list[JDShpMetaDataAttribute]
    MachineUsage: dict[str, JDShpMetaMachineUse]
    # Implements
    # Products

    @field_validator("Product", mode="before")
    @classmethod
    def check_products(cls, v):
        if "Products" in v and v["Product"] != v["Products"]:
            raise ValueError("'Products' exists and is different from 'Product'")


# endregion
# region -------------------------- Product/Equipment Models --------------------------


class JDVariety(JDModel):
    id: str
    name: str
    category: str
    cropName: str
    companyName: str | None = None
    archived: bool
    parentErid: str | None = None
    cleanupStatus: str | None = None


class JDChemical(JDModel):
    id: str
    name: str
    companyName: str | None = None
    registration: str | None = None
    category: str
    type: str
    restrictedUse: bool
    archived: bool
    parentErid: str | None = None
    cleanupStatus: str | None = None


class JDFertilizer(JDChemical):
    pass


# endregion
# region ----------------------------- Operation Helpers ------------------------------


def _prefer(a: JDMeasType, b: JDMeasType) -> bool:
    """Return True if measurements in a should take precedence over b."""

    def base(name: str) -> str:
        return name.removesuffix("Target").removesuffix("Result")

    def is_result(name: str) -> bool:
        return name.endswith("Result")

    a_name = a.measurementName
    b_name = b.measurementName
    return base(a_name) == base(b_name) and is_result(a_name) and not is_result(b_name)


def _merge_lists(a: list[Any], b: list[Any]) -> list[Any]:
    if not a:
        return deepcopy(b)
    if not b:
        return deepcopy(a)

    key = {
        JDVarietyTotal: "varietyId",
        JDProductTotal: "productId",
        JDAppTotal: "productId",
    }.get(type(a[0]))
    if not isinstance(a[0], JDBaseModel) or key is None:
        return deepcopy(a)

    merged = {getattr(item, key): deepcopy(item) for item in a}
    for item in b:
        item_key = getattr(item, key)
        if item_key in merged:
            merged[item_key] = _merge(merged[item_key], item)
        else:
            merged[item_key] = deepcopy(item)
    return list(merged.values())


def _merge(a: Any, b: Any) -> Any:
    if a in (None, [], {}):
        return deepcopy(b)
    if b in (None, [], {}):
        return deepcopy(a)

    if isinstance(a, JDBaseModel) and isinstance(b, JDBaseModel):
        values = {}
        for field in a.__class__.model_fields:
            values[field] = _merge(getattr(a, field), getattr(b, field))
        return a.__class__.model_construct(**values)
    if isinstance(a, list) and isinstance(b, list):
        return _merge_lists(a, b)
    return deepcopy(a)


def merge_measurements(ms: list[JDMeasType]) -> JDMeasType:
    if not ms:
        return JDMeasType(measurementName="Merged")
    merged = deepcopy(ms[0])
    for othr in ms[1:]:
        merged = _merge(othr, merged) if _prefer(othr, merged) else _merge(merged, othr)
    return merged


def parse_measurements(op: JDFieldOp) -> JDMeasurement:
    meas = JDMeasurement()
    mts = op.measurementTypes or []
    if not mts:
        return meas

    merged = merge_measurements(mts)
    meas.area = merged.area
    meas.eq = EquipmentMeasurement(
        # TODO: add the id field here.
        area=merged.area,
        speed=merged.averageSpeed,
        pressure=merged.averagePressure,
        depth=merged.averageDepth,
    )
    # result.area = merged.area
    # result.speed = merged.averageSpeed
    # result.pressure = merged.averagePressure
    # result.depth = merged.averageDepth

    match op.fieldOperationType.lower():
        case "application":
            app = next(iter(merged.applicationProductTotals or []), None)
            if app:
                meas.area = meas.eq.area = app.appliedArea or app.area or meas.area
                meas.eq.speed = app.averageSpeed or meas.eq.speed
                # result.area = app.appliedArea or app.area or result.area
                # result.speed = app.averageSpeed or result.speed
                meas.inputs = [
                    InputMeasurement(
                        guid=p.productId,
                        area=meas.area,
                        total=p.totalMaterial or app.totalMaterial,
                        rate=p.averageMaterial or app.averageMaterial,
                    )
                    for p in app.productTotals
                ]
        case "seeding":
            meas.inputs = [
                InputMeasurement(
                    guid=v.varietyId,
                    area=v.area or meas.area,
                    total=v.totalMaterial or merged.totalMaterial,
                    rate=v.averageMaterial or merged.averageMaterial,
                )
                for v in merged.varietyTotals or []
            ]
        case "harvest":
            meas.outputs = [
                OutputMeasurement(
                    guid=v.varietyId,
                    area=v.area or meas.area,
                    wet_mass=v.wetMass or merged.wetMass,
                    wet_mass_rate=v.averageWetMass or merged.averageWetMass,
                    yield_=v.yield_ or merged.yield_,
                    yield_rate=v.averageYield or merged.averageYield,
                    moisture=v.averageMoisture or merged.averageMoisture,
                )
                for v in merged.varietyTotals or []
            ]
    return meas


# endregion
