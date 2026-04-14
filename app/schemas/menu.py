from pydantic import BaseModel, ConfigDict, Field


class MenuItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: str
    name: str
    category: str | None = None
    size: str | None = None
    calories: int | None = None
    price: float
    price_display: str | None = None


class MenuRecommendation(BaseModel):
    item_id: str
    item_name: str | None = None
    total_quantity: int
    total_revenue: float
    kind: str
    window_days: int | None = None


class MenuItemStats(BaseModel):
    item_id: str
    total_orders: int
    total_quantity: int
    total_revenue: float
    last_order_date: str | None = None


class MenuQueryParams(BaseModel):
    category: str | None = Field(default=None)
    min_price: float | None = Field(default=None, ge=0)
    max_price: float | None = Field(default=None, ge=0)
    limit: int = Field(default=500, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
    sort_by: str | None = None
    sort_dir: str = "asc"
