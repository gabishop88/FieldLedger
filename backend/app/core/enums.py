"""
### IMPORTANT
The enums below that subclass TypeEnum are used as model constraints in `models.py`.
If you want to change a value in any of these enums, you will have to update all records
in the database that have the value you changed. This is an unfortunate side effect of
using enums at the pydantic level and not a dedicated table with FK constraints.

However, it is not difficult, just run this query in the database:
```
# For example, if I changed FieldType.FieldCrops from "Field Crops" to "Row Crops"
UPDATE asset.field SET type='Row Crops' WHERE type='Field Crops';
```

This is only necessary when changing the name that shows up in the database.
For an enum entry that looks like `ShortType = ("Type Name", "Field Type Description")`,
you would have to run the `UPDATE` query only for changing `"Type Name"`.
either `ShortType` or `"Field Type Description"` can be changed with no updates to the
database.

For adding new entries, no changes need to be made to the database unless you want to
manually change any previously existing records to use the new type. For deleting an
enum value, you will have to run the same `UPDATE` query prior to deleting the enum
value in order to change them to a different enum value so the records remain valid.
"""

from enum import EnumMeta, StrEnum, _EnumDict


class DocTag(StrEnum):
    # Asset Tags
    STRUCT_ORG = "Structure • Organizations"
    STRUCT_FARM = "Structure • Farms"
    STRUCT_FIELD = "Structure • Fields"
    STRUCT_BOUND = "Structure • Field Boundaries"

    RES_PROD = "Resources • Products"
    RES_EQIP = "Resources • Equipment"

    IAM_USER = "Access • Users"
    OP = "Field Operations"
    REF = "Reference Tables"
    # NOTE: If I add integrations, do what I did with struct tags for heirarchy.
    INTEG = "Integrations"
    MISC = "Miscellaneous"


class ErrMsg(StrEnum):
    """### Provides literals to maintain consistent error messages.
    Use `.format()` to replace placeholers (like the `{0}` in `ExeMsg.NF`):
    > `ExeMsg.NF.format("AppUser", missing_user_id)`

    > `<{0} {1}> Not Found.` -> `<User 123e4567-e89b-12d3-a456-426614174000> Not Found.`

    See https://docs.python.org/3/library/stdtypes.html#str.format for more information.
    """

    # HTTP_400_BAD_REQUEST
    BAD_PWD = "Incorrect Password."
    BAD_EMPTY_SEARCH = "Provide A Search Option"

    # HTTP_401_UNAUTHORIZED
    UNAUTH_CRED = "Unable To Validate Credentials."
    UNAUTH_JD = "John Deere Integration is not Authorized."

    # HTTP_403_FORBIDDEN
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

    # HTTP_503_SERVICE_UNAVAILABLE
    NO_QUEUE = "Unable to enqueue job to check on worker."
    NO_WORKER = "Worker health check timed out."


class SyncStatus(StrEnum):
    SYNC = "Synced"  # Completely synced and up-to-date. filled green checkbox
    DIRTY = "Unsynced"  # Sync enabled, data maybe old/loading. filled yellow checkbox
    PAUSE = "Paused"  # previously synced, currently not updating. empty yellow checkbox
    FLAG = "Flagged"  # Sync detected likely garbage data
    NOSYNC = "Not Synced"  # Found in heirarchy, not synced. empty gray checkbox
    # Status options for orgs only
    # NOTE: https://developer.deere.com/dev-docs/webhook#events:~:text=Post%20authorization%20redirect%20to%20enable%20organization%20access
    NORG = "No Org Access"  # User is authenticated in jd, but hasn't enabled org access
    CONFLICT = "Synced by Another User"


SYNC_ACTIVE = {SyncStatus.SYNC, SyncStatus.DIRTY, SyncStatus.PAUSE, SyncStatus.FLAG}
SYNC_INACTIVE = {SyncStatus.NOSYNC, SyncStatus.NORG, SyncStatus.CONFLICT}


class LoadStrEnumMeta(EnumMeta):
    """### StrEnum metaclass dynamically filled at runtime.
    E.g. `class MyEnum(StrEnum, metaclass=RuntimeStrEnumMeta, vals=value_list): ...`
    """

    def __new__(mcls, name, bases, dct: _EnumDict, vals: list[str]):
        if vals:
            dct.update({v: v for v in vals})
        return super().__new__(mcls, name, bases, dct)


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
    Covered = ("Covered", "Sheltered Production; Greenhouse, High/Low tunnels, etc.")
    Reserve = ("Reserved", "Minimal disturbance from ag; Habitat, Hunting, Bees, etc.")
    Mixed = ("Mixed Use", "Inseparable mix of field types in one area or over time.")
    Misc = ("Miscellaneous", "Last resort for a field that does not fit another type.")


class BoundaryType(TypeEnum):
    Primary = ("Primary", "Main field boundary. One active Primary is allowed.")
    Subfield = ("Subfield", "Field section such as for trials or alternate management.")
    Obstacle = ("Obstacle", "Impassable feature; Tree, Boulder, Tile Control, etc.")
    Forest = ("Agroforestry", "Perennial Features; Windbreak, Alleys, Riparian Buffer.")
    Conservation = ("Conservation", "CRP, Grass Waterway, Wetlandcan, etc.")
    Road = ("Road or Path", "Access Road, Field Entrance, Livestock Pathways, etc.")
    Misc = ("Miscellaneous", "Last resort for boundaries that do not fit another type.")


# TODO: Add Biological/Chemical label to help organize product types?
# I could also add a prefix just to the enum name and use it to sort them?
# like BioCultivar or ChemHerbicide, or maybe BIO_Cultivar or something
# TODO: Is biochar a bio-input or an ammendment?
class ProductType(TypeEnum):
    Seed = ("Seed", "Specific crop to be planted or otherwise propogated.")
    Crop = ("Crop", "Plant products not for planting; grain, biomass, forage, etc.")
    Animal = ("Animal", "Animal products to be harvested or applied.")  # TODO: graze?
    Manure = ("Manure", "Solid or Liquid manure that has not been further processed.")
    Compost = ("Compost", "Dry or Brewed composed organic material from any source.")
    Bioinput = ("Bio-input", "Biological product; Inoculants, Biochar, Insects, etc.")
    Water = ("Water", "As a carrier or for irrigation. Add mix-ins separately.")
    Coating = ("Seed Coating", "Anything applied directly to seeds before planting.")
    SynFert = ("Fertilizer", "Mined or Refined N, P, or K sources; Ammonia, Urea, etc.")
    Additive = ("Additive", "Non-nutritive fertilizer additives; inhibitors, etc.")
    Ammendment = ("Soil Ammendment", "Inorganic micronutrients, pH balancers, etc.")
    Herbicide = ("Herbicide", "Controls or Suppresses unwated plants, organic or not.")
    Insecticide = ("Insecticide", "Kills insects, organic or not.")
    Fungicide = ("Fungicide", "Suppresses fungal pathogens, organic or not.")
    Othercide = ("Other Pesticide", "Suppresses pests/pathogens, not listed.")
    Adjuvant = ("Adjuvant", "Tank Mix Additives; surfactants, drift reducers, etc.")
    Regulator = ("Growth Regulator", "Any product designed to modify plant growth.")
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


class OrgFarmType(TypeEnum):
    Own = "Owner"
    Operate = ("Operator", "Manages day-to-day operations, does not own")
    Lease = ("Lessee", "Leases the farm from an owner, but manages production.")
    Share = ("Sharecropper", "Farms the land under a sharecropping agreement.")
    Research = ("Research Partner", "Conducts research on, but does not own the farm.")
    Cooperates = ("Cooperator", "Co-operates or co-owns the farm with another org.")
    Gov = ("Government Admin", "Administers a program on behalf of a government.")
    Consult = ("Consultant", "Consults for the owner/operator of the farm.")


class OpType(TypeEnum):
    Seed = ("Seeding", "Planting, Transplanting, Drilling, or Flying on seed.")
    Harvest = ("Harvest", "Harvesting Grain/Biomass, Baling Hay, etc.")
    App = ("Application", "Water, Compost/Fertilizer, Ammendment, Pesticide, etc.")
    Till = ("Tillage", "Soil Disturbance; Harrow, Disc, Cultivate, Strip Till, etc.")
    NoTill = ("Non-Tillage", "No-Till Physical Disturbance; Mowing, Zapping, Raking.")
    Livestock = ("Livestock", "Moving Livestock on a Field; Grazing, Moving, Clearing.")
    Misc = ("Miscellaneous", "Any operation that does not belong in another category.")
