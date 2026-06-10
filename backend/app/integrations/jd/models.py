from pydantic import BaseModel, computed_field, field_validator


class JDLink(BaseModel):
    rel: str
    uri: str


class JDOrg(BaseModel):
    name: str
    member: bool
    id: str
    links: list[JDLink]

    @field_validator("links", mode="before")
    @classmethod
    def filter_links(cls, value):
        keep = {"self", "connections"}
        return [link for link in value if link.get("rel") in keep]

    @computed_field
    @property
    def self_link(self) -> JDLink:
        return next(link for link in self.links if link.rel == "self")

    @computed_field
    @property
    def conn_link(self) -> JDLink | None:
        return next((link for link in self.links if link.rel == "connections"), None)
