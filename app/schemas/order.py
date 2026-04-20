from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from app.schemas.location import LocationSummary

OrderStatus = Literal[
    "order_received",
    "brewing",
    "finishing_touches",
    "ready_for_pickup",
    "completed",
    "cancelled",
]


class OrderItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_item_id: str | None = None
    order_id: str | None = None
    menu_item_id: str | None = None
    item_name: str | None = None
    size: str | None = None
    quantity: int | None = None
    price: float | None = None
    unit_price: float | None = None
    line_total: float | None = None


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    member_id: str | None = None
    store_id: str | None = None
    store_name: str | None = None
    store_city: str | None = None
    store_state: str | None = None
    store_phone: str | None = None
    order_date: datetime | None = None
    items_subtotal: float | None = None
    order_discount: float | None = None
    order_subtotal: float | None = None
    sales_tax: float | None = None
    order_total: float | None = None
    pickup_time: datetime | None = None
    ready_by_estimate: datetime | None = None
    submitted_at: datetime | None = None
    order_status: OrderStatus | None = None
    estimated_prep_minutes: int | None = None
    special_instructions: str | None = None
    points_earned: int | None = None
    points_redeemed: int | None = None
    items: list[OrderItem] = Field(default_factory=list)


class OrderQueryParams(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    include_items: bool = False
    sort_by: str | None = None
    sort_dir: str = "desc"


class DashboardOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    store_id: str | None = None
    store_city: str | None = None
    store_state: str | None = None
    order_date: datetime | None = None
    order_total: float | None = None
    points_earned: int | None = None
    pickup_time: datetime | None = None
    ready_by_estimate: datetime | None = None
    submitted_at: datetime | None = None
    order_status: OrderStatus | None = None
    estimated_prep_minutes: int | None = None
    items: list[OrderItem] = Field(default_factory=list)


class PaymentSummary(BaseModel):
    subtotal: float | None = None
    discount: float | None = None
    tax: float | None = None
    total: float | None = None
    method: str | None = None
    status: str | None = None


class CreateOrderItemRequest(BaseModel):
    menu_item_id: str
    quantity: int = Field(ge=1)
    size: str


class CreateOrderRequest(BaseModel):
    store_id: str
    items: list[CreateOrderItemRequest] = Field(min_length=1)
    payment_method: Literal["pay_in_store"]
    pickup_time: datetime | None = None
    special_instructions: str | None = Field(default=None, max_length=500)


class OrderDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    member_id: str | None = None
    store_id: str | None = None
    store_name: str | None = None
    store_city: str | None = None
    store_state: str | None = None
    store_phone: str | None = None
    location: LocationSummary | None = None
    order_date: datetime | None = None
    pickup_time: datetime | None = None
    ready_by_estimate: datetime | None = None
    submitted_at: datetime | None = None
    order_status: OrderStatus | None = None
    estimated_prep_minutes: int | None = None
    special_instructions: str | None = None
    subtotal: float | None = None
    discount: float | None = None
    tax: float | None = None
    total: float | None = None
    points_earned: int | None = None
    points_redeemed: int | None = None
    items: list[OrderItem] = Field(default_factory=list)
    payment_summary: PaymentSummary | None = None
