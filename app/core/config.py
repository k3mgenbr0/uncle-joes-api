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

    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    bq_project_id: str | None = Field(default=None, alias="BQ_PROJECT_ID")
    bq_dataset: str = Field(default="uncle_joes", alias="BQ_DATASET")
    bq_locations_table: str | None = Field(default=None, alias="BQ_LOCATIONS_TABLE")
    bq_menu_table: str | None = Field(default=None, alias="BQ_MENU_TABLE")

    location_id_column: str = Field(default="location_id", alias="LOCATION_ID_COLUMN")
    location_name_column: str = Field(default="name", alias="LOCATION_NAME_COLUMN")
    location_address_column: str = Field(default="address", alias="LOCATION_ADDRESS_COLUMN")
    location_city_column: str = Field(default="city", alias="LOCATION_CITY_COLUMN")
    location_state_column: str = Field(default="state", alias="LOCATION_STATE_COLUMN")
    location_postal_code_column: str = Field(
        default="postal_code",
        alias="LOCATION_POSTAL_CODE_COLUMN",
    )
    location_phone_column: str = Field(default="phone", alias="LOCATION_PHONE_COLUMN")
    location_hours_column: str = Field(default="hours", alias="LOCATION_HOURS_COLUMN")

    menu_item_id_column: str = Field(default="item_id", alias="MENU_ITEM_ID_COLUMN")
    menu_name_column: str = Field(default="name", alias="MENU_NAME_COLUMN")
    menu_category_column: str = Field(default="category", alias="MENU_CATEGORY_COLUMN")
    menu_description_column: str = Field(
        default="description",
        alias="MENU_DESCRIPTION_COLUMN",
    )
    menu_price_column: str = Field(default="price", alias="MENU_PRICE_COLUMN")
    menu_currency_column: str = Field(default="currency", alias="MENU_CURRENCY_COLUMN")
    menu_is_available_column: str = Field(
        default="is_available",
        alias="MENU_IS_AVAILABLE_COLUMN",
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
        return self.bq_menu_table or f"{self.bigquery_project_id}.{self.bq_dataset}.menu"


@lru_cache
def get_settings() -> Settings:
    return Settings()
