from pydantic import BaseModel


class OrderStats(BaseModel):
    total_orders: int
    total_revenue: float
    avg_order_total: float


class TopMenuItem(BaseModel):
    menu_item_id: str
    item_name: str | None = None
    total_quantity: int
    total_revenue: float


class TopLocation(BaseModel):
    store_id: str
    city: str | None = None
    state: str | None = None
    total_orders: int
    total_revenue: float


class LocationOrderStats(BaseModel):
    store_id: str
    total_orders: int
    total_revenue: float
    avg_order_total: float


class LocationDailyStats(BaseModel):
    store_id: str
    order_date: str
    total_orders: int
    total_revenue: float


class LocationWeeklyStats(BaseModel):
    store_id: str
    week_start: str
    total_orders: int
    total_revenue: float
