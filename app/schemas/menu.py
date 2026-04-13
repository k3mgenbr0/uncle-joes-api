from pydantic import BaseModel, ConfigDict, Field


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: str
    name: str
    category: str | None = None
    description: str | None = None
    price: float
    currency: str = "USD"
    is_available: bool = True


class MenuQueryParams(BaseModel):
    category: str | None = Field(default=None)
    limit: int = Field(default=500, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
