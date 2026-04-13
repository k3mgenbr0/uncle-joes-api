from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    location_id: str
    name: str
    address: str
    city: str
    state: str
    postal_code: str | None = None
    phone: str | None = None
    hours: str | None = None


class LocationQueryParams(BaseModel):
    state: str | None = Field(default=None)
    city: str | None = Field(default=None)
    limit: int = Field(default=500, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
