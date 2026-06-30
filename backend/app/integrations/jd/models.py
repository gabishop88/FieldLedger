from copy import deepcopy
from datetime import datetime
from functools import cached_property
from typing import Any, ClassVar, Literal

from pydantic import AliasChoices, BaseModel, field_validator
from pydantic import Field as ColInfo
from shapely import MultiPolygon, Point, Polygon

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
    keep_links: ClassVar[set[str]] = {"self", "owningOrganization", "organization"}
    links: list[JDLink]

    def get_uri(self, rel: str) -> str:
        """Get the uri of a link in `self.links`."""
        assert rel in self.keep_links, f"{rel=} not in {self.keep_links}."
        return next(link for link in self.links if link.rel == rel).uri

    @cached_property
    def uri(self) -> str:
        return self.get_uri("self")

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


class JDPoint(JDBaseModel):
    lat: float
    lon: float

    def as_shapely(self) -> Point:
        return Point(self.lon, self.lat)


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
    centroid: JDPoint
    archived: bool
    id: str
    links: list[JDLink]
    active: bool
    irrigated: bool

    def as_shapely(self) -> MultiPolygon:
        return MultiPolygon([p.as_shapely() for p in self.multipolygons])

    @property
    def wkt(self) -> str:
        """Well-Known-Text representation of the boundary geometry."""
        return self.as_shapely().wkt


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


class InputMeasurements(JDBaseModel):
    area: Meas | None = None
    total: Meas | None = None
    rate: Meas | None = None


class OutputMeasurements(JDBaseModel):
    area: Meas | None = None
    wet_mass: Meas | None = None
    wet_mass_rate: Meas | None = None
    yield_: Meas | None = ColInfo(
        default=None, validation_alias="yield", serialization_alias="yield"
    )
    yield_rate: Meas | None = None
    moisture: Meas | None = None


class JDMeasurements(JDBaseModel):
    area: Meas | None = None
    speed: Meas | None = None
    pressure: Meas | None = None
    depth: Meas | None = None

    inputs: dict[str, InputMeasurements] = ColInfo(default_factory=dict)
    outputs: dict[str, OutputMeasurements] = ColInfo(default_factory=dict)


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
    measurementTypes: list[JDMeasType] | None = None
    fieldOperationMachines: list[JDOpMachine] | None = None
    tillageProducts: list[JDTillageProduct] | None = None
    varieties: list[JDProduct] | None = None
    id: str
    links: list[JDLink]

    @cached_property
    def measurements(self) -> JDMeasurements:
        return parse_measurements(self)


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


def parse_measurements(op: JDFieldOp) -> JDMeasurements:
    result = JDMeasurements()
    mts = op.measurementTypes or []
    if not mts:
        return result

    merged = merge_measurements(mts)
    result.area = merged.area
    result.speed = merged.averageSpeed
    result.pressure = merged.averagePressure
    result.depth = merged.averageDepth

    match op.fieldOperationType.lower():
        case "application":
            app = next(iter(merged.applicationProductTotals or []), None)
            if app:
                result.area = app.appliedArea or app.area or result.area
                result.speed = app.averageSpeed or result.speed
                result.inputs = {
                    p.productId: InputMeasurements(
                        area=result.area,
                        total=p.totalMaterial or app.totalMaterial,
                        rate=p.averageMaterial or app.averageMaterial,
                    )
                    for p in app.productTotals
                }
        case "seeding":
            result.inputs = {
                v.varietyId: InputMeasurements(
                    area=v.area or result.area,
                    total=v.totalMaterial or merged.totalMaterial,
                    rate=v.averageMaterial or merged.averageMaterial,
                )
                for v in merged.varietyTotals or []
            }
        case "harvest":
            result.outputs = {
                v.varietyId: OutputMeasurements(
                    area=v.area or result.area,
                    wet_mass=v.wetMass or merged.wetMass,
                    wet_mass_rate=v.averageWetMass or merged.averageWetMass,
                    yield_=v.yield_ or merged.yield_,
                    yield_rate=v.averageYield or merged.averageYield,
                    moisture=v.averageMoisture or merged.averageMoisture,
                )
                for v in merged.varietyTotals or []
            }
    return result


# endregion
