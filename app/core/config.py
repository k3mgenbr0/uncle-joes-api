from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Uncle Joe's Coffee Shop API"
    app_version: str = "1.0.0"
    app_description: str = (
        "FastAPI backend serving Uncle Joe's Coffee Shop locations and menu data "
        "from BigQuery."
    )
    log_level: str = "INFO"
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    auth_secret_key: str = Field(default="dev-secret", alias="AUTH_SECRET_KEY")
    auth_cookie_name: str = Field(default="ucc_session", alias="AUTH_COOKIE_NAME")
    auth_cookie_ttl_minutes: int = Field(default=480, alias="AUTH_COOKIE_TTL_MINUTES")
    auth_cookie_secure: bool = Field(default=False, alias="AUTH_COOKIE_SECURE")
    auth_cookie_samesite: str = Field(default="lax", alias="AUTH_COOKIE_SAMESITE")

    google_cloud_project: str | None = Field(default="mgmt545proj", alias="GOOGLE_CLOUD_PROJECT")
    bq_project_id: str | None = Field(default="mgmt545proj", alias="BQ_PROJECT_ID")
    bq_dataset: str = Field(default="uncle_joes", alias="BQ_DATASET")
    bq_locations_table: str | None = Field(default=None, alias="BQ_LOCATIONS_TABLE")
    bq_menu_table: str | None = Field(default=None, alias="BQ_MENU_TABLE")
    bq_members_table: str | None = Field(default=None, alias="BQ_MEMBERS_TABLE")
    bq_orders_table: str | None = Field(default=None, alias="BQ_ORDERS_TABLE")
    bq_order_items_table: str | None = Field(
        default=None,
        alias="BQ_ORDER_ITEMS_TABLE",
    )

    location_id_column: str = Field(default="id", alias="LOCATION_ID_COLUMN")
    location_city_column: str = Field(default="city", alias="LOCATION_CITY_COLUMN")
    location_state_column: str = Field(default="state", alias="LOCATION_STATE_COLUMN")
    location_postal_code_column: str = Field(
        default="zip_code",
        alias="LOCATION_POSTAL_CODE_COLUMN",
    )
    location_phone_column: str = Field(default="phone_number", alias="LOCATION_PHONE_COLUMN")
    location_email_column: str = Field(default="email", alias="LOCATION_EMAIL_COLUMN")
    location_fax_column: str = Field(default="fax_number", alias="LOCATION_FAX_COLUMN")
    location_address_one_column: str = Field(
        default="address_one",
        alias="LOCATION_ADDRESS_ONE_COLUMN",
    )
    location_address_two_column: str = Field(
        default="address_two",
        alias="LOCATION_ADDRESS_TWO_COLUMN",
    )
    location_map_address_column: str = Field(
        default="location_map_address",
        alias="LOCATION_MAP_ADDRESS_COLUMN",
    )
    location_latitude_column: str = Field(
        default="location_map_lat",
        alias="LOCATION_LATITUDE_COLUMN",
    )
    location_longitude_column: str = Field(
        default="location_map_lng",
        alias="LOCATION_LONGITUDE_COLUMN",
    )
    location_nearby_column: str = Field(default="near_by", alias="LOCATION_NEARBY_COLUMN")
    location_open_for_business_column: str = Field(
        default="open_for_business",
        alias="LOCATION_OPEN_FOR_BUSINESS_COLUMN",
    )
    location_wifi_column: str = Field(default="wifi", alias="LOCATION_WIFI_COLUMN")
    location_drive_thru_column: str = Field(
        default="drive_thru",
        alias="LOCATION_DRIVE_THRU_COLUMN",
    )
    location_door_dash_column: str = Field(
        default="door_dash",
        alias="LOCATION_DOOR_DASH_COLUMN",
    )
    location_hours_monday_open_column: str = Field(
        default="hours_monday_open",
        alias="LOCATION_HOURS_MONDAY_OPEN_COLUMN",
    )
    location_hours_monday_close_column: str = Field(
        default="hours_monday_close",
        alias="LOCATION_HOURS_MONDAY_CLOSE_COLUMN",
    )
    location_hours_tuesday_open_column: str = Field(
        default="hours_tuesday_open",
        alias="LOCATION_HOURS_TUESDAY_OPEN_COLUMN",
    )
    location_hours_tuesday_close_column: str = Field(
        default="hours_tuesday_close",
        alias="LOCATION_HOURS_TUESDAY_CLOSE_COLUMN",
    )
    location_hours_wednesday_open_column: str = Field(
        default="hours_wednesday_open",
        alias="LOCATION_HOURS_WEDNESDAY_OPEN_COLUMN",
    )
    location_hours_wednesday_close_column: str = Field(
        default="hours_wednesday_close",
        alias="LOCATION_HOURS_WEDNESDAY_CLOSE_COLUMN",
    )
    location_hours_thursday_open_column: str = Field(
        default="hours_thursday_open",
        alias="LOCATION_HOURS_THURSDAY_OPEN_COLUMN",
    )
    location_hours_thursday_close_column: str = Field(
        default="hours_thursday_close",
        alias="LOCATION_HOURS_THURSDAY_CLOSE_COLUMN",
    )
    location_hours_friday_open_column: str = Field(
        default="hours_friday_open",
        alias="LOCATION_HOURS_FRIDAY_OPEN_COLUMN",
    )
    location_hours_friday_close_column: str = Field(
        default="hours_friday_close",
        alias="LOCATION_HOURS_FRIDAY_CLOSE_COLUMN",
    )
    location_hours_saturday_open_column: str = Field(
        default="hours_saturday_open",
        alias="LOCATION_HOURS_SATURDAY_OPEN_COLUMN",
    )
    location_hours_saturday_close_column: str = Field(
        default="hours_saturday_close",
        alias="LOCATION_HOURS_SATURDAY_CLOSE_COLUMN",
    )
    location_hours_sunday_open_column: str = Field(
        default="hours_sunday_open",
        alias="LOCATION_HOURS_SUNDAY_OPEN_COLUMN",
    )
    location_hours_sunday_close_column: str = Field(
        default="hours_sunday_close",
        alias="LOCATION_HOURS_SUNDAY_CLOSE_COLUMN",
    )

    menu_item_id_column: str = Field(default="id", alias="MENU_ITEM_ID_COLUMN")
    menu_name_column: str = Field(default="name", alias="MENU_NAME_COLUMN")
    menu_category_column: str = Field(default="category", alias="MENU_CATEGORY_COLUMN")
    menu_size_column: str = Field(default="size", alias="MENU_SIZE_COLUMN")
    menu_calories_column: str = Field(default="calories", alias="MENU_CALORIES_COLUMN")
    menu_price_column: str = Field(default="price", alias="MENU_PRICE_COLUMN")
    member_id_column: str = Field(default="id", alias="MEMBER_ID_COLUMN")
    member_first_name_column: str = Field(
        default="first_name",
        alias="MEMBER_FIRST_NAME_COLUMN",
    )
    member_last_name_column: str = Field(
        default="last_name",
        alias="MEMBER_LAST_NAME_COLUMN",
    )
    member_email_column: str = Field(default="email", alias="MEMBER_EMAIL_COLUMN")
    member_phone_column: str = Field(default="phone_number", alias="MEMBER_PHONE_COLUMN")
    member_home_store_column: str = Field(default="home_store", alias="MEMBER_HOME_STORE_COLUMN")
    member_password_column: str = Field(
        default="password",
        alias="MEMBER_PASSWORD_COLUMN",
    )

    order_id_column: str = Field(default="order_id", alias="ORDER_ID_COLUMN")
    order_member_id_column: str = Field(default="member_id", alias="ORDER_MEMBER_ID_COLUMN")
    order_store_id_column: str = Field(default="store_id", alias="ORDER_STORE_ID_COLUMN")
    order_date_column: str = Field(default="order_date", alias="ORDER_DATE_COLUMN")
    order_items_subtotal_column: str = Field(
        default="items_subtotal",
        alias="ORDER_ITEMS_SUBTOTAL_COLUMN",
    )
    order_discount_column: str = Field(
        default="order_discount",
        alias="ORDER_DISCOUNT_COLUMN",
    )
    order_subtotal_column: str = Field(
        default="order_subtotal",
        alias="ORDER_SUBTOTAL_COLUMN",
    )
    order_sales_tax_column: str = Field(
        default="sales_tax",
        alias="ORDER_SALES_TAX_COLUMN",
    )
    order_total_column: str = Field(default="order_total", alias="ORDER_TOTAL_COLUMN")

    order_item_id_column: str = Field(default="id", alias="ORDER_ITEM_ID_COLUMN")
    order_item_order_id_column: str = Field(
        default="order_id",
        alias="ORDER_ITEM_ORDER_ID_COLUMN",
    )
    order_item_menu_item_id_column: str = Field(
        default="menu_item_id",
        alias="ORDER_ITEM_MENU_ITEM_ID_COLUMN",
    )
    order_item_name_column: str = Field(
        default="item_name",
        alias="ORDER_ITEM_NAME_COLUMN",
    )
    order_item_size_column: str = Field(
        default="size",
        alias="ORDER_ITEM_SIZE_COLUMN",
    )
    order_item_quantity_column: str = Field(
        default="quantity",
        alias="ORDER_ITEM_QUANTITY_COLUMN",
    )
    order_item_price_column: str = Field(
        default="price",
        alias="ORDER_ITEM_PRICE_COLUMN",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def bigquery_project_id(self) -> str:
        project_id = self.bq_project_id or self.google_cloud_project
        if not project_id:
            msg = "BQ_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set."
            raise ValueError(msg)
        return project_id

    @property
    def resolved_locations_table(self) -> str:
        return self.bq_locations_table or (
            f"{self.bigquery_project_id}.{self.bq_dataset}.locations"
        )

    @property
    def resolved_menu_table(self) -> str:
        return self.bq_menu_table or (
            f"{self.bigquery_project_id}.{self.bq_dataset}.menu_items"
        )

    @property
    def resolved_members_table(self) -> str:
        return self.bq_members_table or (
            f"{self.bigquery_project_id}.{self.bq_dataset}.members"
        )

    @property
    def resolved_orders_table(self) -> str:
        return self.bq_orders_table or (
            f"{self.bigquery_project_id}.{self.bq_dataset}.orders"
        )

    @property
    def resolved_order_items_table(self) -> str:
        return self.bq_order_items_table or (
            f"{self.bigquery_project_id}.{self.bq_dataset}.order_items"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
