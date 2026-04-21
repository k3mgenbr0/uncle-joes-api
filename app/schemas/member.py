from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.location import LocationSummary
from app.schemas.order import DashboardOrder, Order


class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")

    member_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None
    home_store: str | None = None
    rewards_tier: str | None = None
    points_to_next_reward: int | None = None
    preferred_store_id: str | None = None
    preferred_store: LocationSummary | None = None
    join_date: str | None = None
    birthday_month_day: str | None = None
    marketing_opt_in: bool | None = None
    profile_photo_url: str | None = None


class MemberQueryParams(BaseModel):
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class MemberPoints(BaseModel):
    member_id: str
    total_points: int


class MemberPointsHistoryEntry(BaseModel):
    order_id: str
    order_date: str | None = None
    store_id: str | None = None
    store_city: str | None = None
    store_state: str | None = None
    order_total: float | None = None
    points_earned: int = 0


class MemberFavoriteItem(BaseModel):
    menu_item_id: str
    item_name: str | None = None
    category: str | None = None
    size: str | None = None
    available_sizes: list[str] = Field(default_factory=list)
    default_size: str | None = None
    current_price: float | None = None
    image_url: str | None = None
    available_at_store: bool | None = None
    store_availability_status: str | None = None
    is_explicit: bool = False
    total_orders: int
    total_quantity: int
    total_revenue: float


class MemberFavoriteMutation(BaseModel):
    success: bool
    menu_item_id: str


class MemberFavoriteCreateRequest(BaseModel):
    menu_item_id: str


class MemberFavoriteTrendPoint(BaseModel):
    menu_item_id: str
    item_name: str | None = None
    week_start: str
    total_orders: int
    total_quantity: int
    total_revenue: float


class MemberSummary(BaseModel):
    member: Member
    points: MemberPoints
    recent_orders: list[Order]
    favorites: list[MemberFavoriteItem]


class MemberDashboard(BaseModel):
    member: Member
    points: MemberPoints
    orders: list[DashboardOrder]
    favorites: list[MemberFavoriteItem] = Field(default_factory=list)
    points_history: list[MemberPointsHistoryEntry] = Field(default_factory=list)
    pagination: dict | None = None
