from enum import EnumMeta, StrEnum, _EnumDict


class DocTag(StrEnum):
    # Asset Tags
    ASSET = "Available Assets"
    ASSET_FARM = "Assets · Farms"
    ASSET_FIELD = "Assets · Fields"
    ASSET_BOUND = "Assets · Boundaries"
    ASSET_PROD = "Assets · Products"
    ASSET_EQUIP = "Assets · Equipment"

    USER = "User Information and Authentication"
    OP = "Field Operations"
    REF = "Reference Tables"
    MISC = "Miscellaneous"


class ErrMsg(StrEnum):
    """### Provides literals to maintain consistent error messages.
    Use `.format()` to replace placeholers (like the `{0}` in `ExeMsg.NF`):
    > `ExeMsg.NF.format("User", missing_user_id)`

    > `<{0} {1}> Not Found.` -> `<User 123e4567-e89b-12d3-a456-426614174000> Not Found.`

    See https://docs.python.org/3/library/stdtypes.html#str.format for more information.
    """

    # HTTP_400_BAD_REQUEST
    BAD_PWD = "Incorrect Password."
    BAD_EMPTY_SEARCH = "Provide A Search Option"

    # HTTP_403_FORBIDDEN
    FBDN_CRED = "Unable To Validate Credentials."
    FBDN_PRIV = "User Missing Priveleges."
    FBDN_DEL_1SU = "YOU ARE NEEDED, ADMINISTRATOR."
    FBDN_REM_1SU = "Cannot Delete First Superuser."

    # HTTP_404_NOT_FOUND
    NF = "<{0} {1}> Not Found."

    # HTTP_409_CONFLICT (Matches the detail sent by the DB when violating constraints)
    KEY_EXISTS = "Key ({0})=({1}) already exists."

    # HTTP_422_UNPROCESSABLE_ENTITY
    INVALID_WKT = "'geom' is not valid WKT."
    INVALID_TOPO = "'geom' has invalid topology."


class LoadStrEnumMeta(EnumMeta):
    """### StrEnum metaclass dynamically filled at runtime.
    E.g. `class MyEnum(StrEnum, metaclass=RuntimeStrEnumMeta, vals=value_list): ...`
    """

    def __new__(mcls, name, bases, dct: _EnumDict, vals: list[str]):
        if vals:
            dct.update({v: v for v in vals})
        return super().__new__(mcls, name, bases, dct)


# class RefTables(StrEnum, metaclass=DynamicStrEnumMeta, vals=get_table_names()): ...


class TypeEnum(StrEnum):
    """### A StrEnum designed to constrain a table column to predefined values.
    Create a TableEnum like:
    ```
    class TestType(TypeEnum):
        Label = ("name", "description)
        Next Label = ("other name")
    ```
    E.g. define the column: `type: TestType` in your `Example` model in `models.py`.

    To get the values (e.g. for an endpoint response): `TestType.asdict()`

    NOTE: When using a TypeEnum subclass as a type annotation in `models.py`,
    it is recommended to set the column type to a string (VARCHAR) to let pydantic
    handle type checking, not the database (also because otherwise you would have to
    make an alembic revision every time you changed an enum value to update the db enum)
    ```
    from sqlmodel import Field as ColInfo
    class SomeModel(SQLModel):
        name: str = ColInfo(primary_key=True, max_length=32)
        test: TestType =  ColInfo(sa_column=Column("test", String(32), nullable=False))
    ```
    """

    description: str | None

    def __new__(cls, value: str, desc: str | None = None):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.description = desc
        return obj

    @classmethod
    def asdict(cls) -> list[dict[str, str | None]]:
        return [{"name": t.value, "description": t.description} for t in cls]


class FieldType(TypeEnum):
    FieldCrops = ("Field Crops", "Row Crops, Specialty Crops, Hay or Forage, etc.")
    Forest = ("Agroforestry", "Perennials; Orchard, Alley Cropping, Silvopasture, etc.")
    Pasture = ("Pasture", "Permanent Pasture or Grazed Area, but not Silvopasture.")
    Indoor = ("Covered", "Sheltered Production; Greenhouse, High/Low tunnels, etc.")
    Reserve = ("Reserved", "Minimal disturbance from ag; Habitat, Hunting, Bees, etc.")
    Mixed = ("Mixed Use", "Inseparable mix of field types in one area or over time.")
    Misc = ("Miscellaneous", "Last resort for a field that does not fit another type.")


class BoundaryType(TypeEnum):
    Primary = ("Primary", "Main field boundary. One active Primary is allowed.")
    Subfield = ("Subfield", "Field section such as for trials or alternate management.")
    Obstacle = ("Obstacle", "Impassable feature; Tree, Boulder, Tile Control, etc.")
    Forest = ("Agroforestry", "Perennial Features; Windbreak, Alleys, Riparian Buffer.")
    Conservation = ("Conservation", "CRP, Grass Waterway, Wetland, etc.")
    Road = ("Road or Path", "Access Road, Field Entrance, Livestock Pathways, etc.")
    Misc = ("Miscellaneous", "Last resort for boundaries that do not fit another type.")


# TODO: Add Biological/Chemical label to help organize product types?
class ProductType(TypeEnum):
    Cultivar = ("Variety or Cultivar", "Specific crop to be planted or harvested.")
    Breed = ("Livestock Breed", "Breed of livestock to be pastured or processed.")
    Manure = ("Manure", "Solid or Liquid manure that has not been further processed.")
    Compost = ("Compost", "Dry or Brewed composed organic material from any source.")
    Bioinput = ("Bio-input", "Biological product; Inoculants, Biochar, Insects, etc.")
    Water = ("Water", "As a carrier or for irrigation. Add mix-ins separately.")
    Coating = ("Seed Coating", "Anything applied directly to seeds before planting.")
    SynFert = ("Fertilizer", "Mined or Refined N, P, or K sources; Ammonia, Urea, etc.")
    FertAdd = ("Fertilizer Additive", "Non-nutritive; stabilizers, inhibitors, etc.")
    Ammendment = ("Soil Ammendment", "Inorganic micronutrients, pH balancers, etc.")
    Herbicide = ("Herbicide", "Controls or Suppresses unwated plants, organic or not.")
    Insecticide = ("Insecticide", "Kills insects, organic or not.")
    Fungicide = ("Fungicide", "Suppresses fungal pathogens, organic or not.")
    OtherPesticide = ("Other Pesticide", "Suppresses pests/pathogens, not listed.")
    Adjuvant = "Tank Mix Additives; surfactants, spreaders, drift reducers, etc."
    Regulator = ("Growth Regulator", "Any product that modifies plant growth.")
    Misc = ("Miscellaneous", "Last resort for products that do not fit another type.")


class EquipmentType(TypeEnum):
    """A machine is self propelled, an implement is operated by a machine."""

    Tractor = ("Tractor", "Attaches to, moves, or operates other equipment.")
    Harvester = ("Harvester", "Harvest and collect a crop; Combine, Forage Harvester.")
    Mower = ("Mower", "Cuts and leaves biomass for Harvesting, Forage, or Maintenance.")
    Header = ("Header", "An attachment for a harvestor; Corn Head for a Combine.")
    Planter = ("Planter", "Plants, Drills, or Broadcasts seed.")
    Sprayer = ("Sprayer", "Sprays liquid Pesticides, Fertiliers, Mixes, etc.")
    App = ("Applicator", "Physically applies liquid Fertilizer, Ammendments, etc.")
    Spreader = ("Spreader", "Spreads dry materials like Fertilizer or Ammendments.")
    Till = ("Tillage", "Disturbs soil for Planting, Cultivating, or to Manage Residue.")
    Rake = ("Rake", "Manipulates cut residue; Windrowing, Tedding, Chopping, etc.")
    Baler = ("Baler", "Forms/Wraps bales; Round or Square Baler, Sileage Wrapper, etc.")
    Trailer = ("Wagon/Trailer", "Gravity Wagon, Livestock Trailer, Grain Truck, etc.")
    Mill = ("Feed Mill", "Mixes and/or Mills livestock feed.")
    Irrigator = ("Irrigation", "Water Reel, Center-Pivor Irrigator, Sprinkler, etc.")
    Misc = ("Miscellaneous", "Last resort for equipment in no other category.")
