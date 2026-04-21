from pydantic import BaseModel, ConfigDict, Field


class LocationHoursDay(BaseModel):
    open: str | None = None
    close: str | None = None


class HolidayHours(BaseModel):
    date: str
    open: str | None = None
    close: str | None = None
    note: str | None = None


class LocationHours(BaseModel):
    monday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    tuesday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    wednesday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    thursday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    friday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    saturday: LocationHoursDay = Field(default_factory=LocationHoursDay)
    sunday: LocationHoursDay = Field(default_factory=LocationHoursDay)


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    location_id: str
    city: str
    state: str
    address_one: str | None = None
    address_two: str | None = None
    map_address: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    fax_number: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    near_by: str | None = None
    open_for_business: bool | None = None
    wifi: bool | None = None
    drive_thru: bool | None = None
    door_dash: bool | None = None
    hours: LocationHours = Field(default_factory=LocationHours)
    full_address: str | None = None
    address: str | None = None
    hours_today: LocationHoursDay | None = None
    open_now: bool | None = None
    store_name: str | None = None
    display_name: str | None = None
    services: list[str] = Field(default_factory=list)
    holiday_hours: list[HolidayHours] = Field(default_factory=list)
    pickup_supported: bool | None = None
    dine_in_supported: bool | None = None
    ordering_available: bool = False
    availability_status: str = "coming_soon"
    availability_message: str | None = None
    nearby_store_ids: list[str] = Field(default_factory=list)
    distance_miles: float | None = None
    region: str | None = None
    metro_area: str | None = None


class LocationSummary(BaseModel):
    location_id: str
    store_name: str | None = None
    display_name: str | None = None
    city: str | None = None
    state: str | None = None
    full_address: str | None = None
    address: str | None = None
    phone: str | None = None


class LocationQueryParams(BaseModel):
    state: str | None = Field(default=None)
    city: str | None = Field(default=None)
    open_for_business: bool | None = None
    wifi: bool | None = None
    drive_thru: bool | None = None
    door_dash: bool | None = None
    orderable_only: bool = False
    limit: int = Field(default=500, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class NearbyLocationQueryParams(BaseModel):
    lat: float
    lng: float
    orderable_only: bool = False
    open_for_business: bool | None = None
    limit: int = Field(default=10, ge=1, le=100)


class PickupWindow(BaseModel):
    start: str
    end: str


class LocationAvailability(BaseModel):
    location_id: str
    display_name: str | None = None
    ordering_available: bool
    open_now: bool | None = None
    accepting_orders_now: bool
    availability_status: str
    availability_message: str | None = None
    next_open_at: str | None = None
    next_close_at: str | None = None
    valid_pickup_windows: list[PickupWindow] = Field(default_factory=list)
