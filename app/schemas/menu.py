from pydantic import BaseModel, ConfigDict, Field


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: str
    name: str
    category: str | None = None
    size: str | None = None
    calories: int | None = None
    price: float


class MenuQueryParams(BaseModel):
    category: str | None = Field(default=None)
    limit: int = Field(default=500, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
