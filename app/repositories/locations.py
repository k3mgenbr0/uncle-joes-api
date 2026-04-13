from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table
from app.schemas.location import LocationQueryParams


class LocationRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._table = quote_table(settings.resolved_locations_table)
        self._id_column = quote_column(settings.location_id_column)
        self._city_column = quote_column(settings.location_city_column)
        self._state_column = quote_column(settings.location_state_column)
        self._postal_code_column = quote_column(settings.location_postal_code_column)
        self._phone_column = quote_column(settings.location_phone_column)
        self._email_column = quote_column(settings.location_email_column)
        self._fax_column = quote_column(settings.location_fax_column)
        self._address_one_column = quote_column(settings.location_address_one_column)
        self._address_two_column = quote_column(settings.location_address_two_column)
        self._map_address_column = quote_column(settings.location_map_address_column)
        self._latitude_column = quote_column(settings.location_latitude_column)
        self._longitude_column = quote_column(settings.location_longitude_column)
        self._nearby_column = quote_column(settings.location_nearby_column)
        self._open_for_business_column = quote_column(
            settings.location_open_for_business_column
        )
        self._wifi_column = quote_column(settings.location_wifi_column)
        self._drive_thru_column = quote_column(settings.location_drive_thru_column)
        self._door_dash_column = quote_column(settings.location_door_dash_column)
        self._hours_monday_open_column = quote_column(
            settings.location_hours_monday_open_column
        )
        self._hours_monday_close_column = quote_column(
            settings.location_hours_monday_close_column
        )
        self._hours_tuesday_open_column = quote_column(
            settings.location_hours_tuesday_open_column
        )
        self._hours_tuesday_close_column = quote_column(
            settings.location_hours_tuesday_close_column
        )
        self._hours_wednesday_open_column = quote_column(
            settings.location_hours_wednesday_open_column
        )
        self._hours_wednesday_close_column = quote_column(
            settings.location_hours_wednesday_close_column
        )
        self._hours_thursday_open_column = quote_column(
            settings.location_hours_thursday_open_column
        )
        self._hours_thursday_close_column = quote_column(
            settings.location_hours_thursday_close_column
        )
        self._hours_friday_open_column = quote_column(
            settings.location_hours_friday_open_column
        )
        self._hours_friday_close_column = quote_column(
            settings.location_hours_friday_close_column
        )
        self._hours_saturday_open_column = quote_column(
            settings.location_hours_saturday_open_column
        )
        self._hours_saturday_close_column = quote_column(
            settings.location_hours_saturday_close_column
        )
        self._hours_sunday_open_column = quote_column(
            settings.location_hours_sunday_open_column
        )
        self._hours_sunday_close_column = quote_column(
            settings.location_hours_sunday_close_column
        )

    def list_locations(self, params: LocationQueryParams) -> list[dict]:
        where_clauses: list[str] = []
        query_params: list[bigquery.ScalarQueryParameter] = []

        if params.state:
            where_clauses.append(f"LOWER({self._state_column}) = LOWER(@state)")
            query_params.append(
                bigquery.ScalarQueryParameter("state", "STRING", params.state)
            )

        if params.city:
            where_clauses.append(f"LOWER({self._city_column}) = LOWER(@city)")
            query_params.append(
                bigquery.ScalarQueryParameter("city", "STRING", params.city)
            )

        if params.open_for_business is not None:
            where_clauses.append(f"{self._open_for_business_column} = @open_for_business")
            query_params.append(
                bigquery.ScalarQueryParameter(
                    "open_for_business",
                    "BOOL",
                    params.open_for_business,
                )
            )

        if params.wifi is not None:
            where_clauses.append(f"{self._wifi_column} = @wifi")
            query_params.append(
                bigquery.ScalarQueryParameter("wifi", "BOOL", params.wifi)
            )

        if params.drive_thru is not None:
            where_clauses.append(f"{self._drive_thru_column} = @drive_thru")
            query_params.append(
                bigquery.ScalarQueryParameter("drive_thru", "BOOL", params.drive_thru)
            )

        if params.door_dash is not None:
            where_clauses.append(f"{self._door_dash_column} = @door_dash")
            query_params.append(
                bigquery.ScalarQueryParameter("door_dash", "BOOL", params.door_dash)
            )

        query_params.extend(
            [
                bigquery.ScalarQueryParameter("limit", "INT64", params.limit),
                bigquery.ScalarQueryParameter("offset", "INT64", params.offset),
            ]
        )

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS location_id,
                CAST({self._city_column} AS STRING) AS city,
                CAST({self._state_column} AS STRING) AS state,
                CAST({self._address_one_column} AS STRING) AS address_one,
                CAST({self._address_two_column} AS STRING) AS address_two,
                CAST({self._map_address_column} AS STRING) AS map_address,
                CAST({self._postal_code_column} AS STRING) AS postal_code,
                CAST({self._phone_column} AS STRING) AS phone,
                CAST({self._email_column} AS STRING) AS email,
                CAST({self._fax_column} AS STRING) AS fax_number,
                SAFE_CAST({self._latitude_column} AS FLOAT64) AS latitude,
                SAFE_CAST({self._longitude_column} AS FLOAT64) AS longitude,
                CAST({self._nearby_column} AS STRING) AS near_by,
                CAST({self._open_for_business_column} AS BOOL) AS open_for_business,
                CAST({self._wifi_column} AS BOOL) AS wifi,
                CAST({self._drive_thru_column} AS BOOL) AS drive_thru,
                CAST({self._door_dash_column} AS BOOL) AS door_dash,
                STRUCT(
                    STRUCT(CAST({self._hours_monday_open_column} AS STRING) AS open, CAST({self._hours_monday_close_column} AS STRING) AS close) AS monday,
                    STRUCT(CAST({self._hours_tuesday_open_column} AS STRING) AS open, CAST({self._hours_tuesday_close_column} AS STRING) AS close) AS tuesday,
                    STRUCT(CAST({self._hours_wednesday_open_column} AS STRING) AS open, CAST({self._hours_wednesday_close_column} AS STRING) AS close) AS wednesday,
                    STRUCT(CAST({self._hours_thursday_open_column} AS STRING) AS open, CAST({self._hours_thursday_close_column} AS STRING) AS close) AS thursday,
                    STRUCT(CAST({self._hours_friday_open_column} AS STRING) AS open, CAST({self._hours_friday_close_column} AS STRING) AS close) AS friday,
                    STRUCT(CAST({self._hours_saturday_open_column} AS STRING) AS open, CAST({self._hours_saturday_close_column} AS STRING) AS close) AS saturday,
                    STRUCT(CAST({self._hours_sunday_open_column} AS STRING) AS open, CAST({self._hours_sunday_close_column} AS STRING) AS close) AS sunday
                ) AS hours
            FROM {self._table}
            {where_sql}
            ORDER BY {self._state_column}, {self._city_column}, {self._id_column}
            LIMIT @limit OFFSET @offset
        """
        return self._runner.fetch_all(query, query_params)

    def get_location(self, location_id: str) -> dict | None:
        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS location_id,
                CAST({self._city_column} AS STRING) AS city,
                CAST({self._state_column} AS STRING) AS state,
                CAST({self._address_one_column} AS STRING) AS address_one,
                CAST({self._address_two_column} AS STRING) AS address_two,
                CAST({self._map_address_column} AS STRING) AS map_address,
                CAST({self._postal_code_column} AS STRING) AS postal_code,
                CAST({self._phone_column} AS STRING) AS phone,
                CAST({self._email_column} AS STRING) AS email,
                CAST({self._fax_column} AS STRING) AS fax_number,
                SAFE_CAST({self._latitude_column} AS FLOAT64) AS latitude,
                SAFE_CAST({self._longitude_column} AS FLOAT64) AS longitude,
                CAST({self._nearby_column} AS STRING) AS near_by,
                CAST({self._open_for_business_column} AS BOOL) AS open_for_business,
                CAST({self._wifi_column} AS BOOL) AS wifi,
                CAST({self._drive_thru_column} AS BOOL) AS drive_thru,
                CAST({self._door_dash_column} AS BOOL) AS door_dash,
                STRUCT(
                    STRUCT(CAST({self._hours_monday_open_column} AS STRING) AS open, CAST({self._hours_monday_close_column} AS STRING) AS close) AS monday,
                    STRUCT(CAST({self._hours_tuesday_open_column} AS STRING) AS open, CAST({self._hours_tuesday_close_column} AS STRING) AS close) AS tuesday,
                    STRUCT(CAST({self._hours_wednesday_open_column} AS STRING) AS open, CAST({self._hours_wednesday_close_column} AS STRING) AS close) AS wednesday,
                    STRUCT(CAST({self._hours_thursday_open_column} AS STRING) AS open, CAST({self._hours_thursday_close_column} AS STRING) AS close) AS thursday,
                    STRUCT(CAST({self._hours_friday_open_column} AS STRING) AS open, CAST({self._hours_friday_close_column} AS STRING) AS close) AS friday,
                    STRUCT(CAST({self._hours_saturday_open_column} AS STRING) AS open, CAST({self._hours_saturday_close_column} AS STRING) AS close) AS saturday,
                    STRUCT(CAST({self._hours_sunday_open_column} AS STRING) AS open, CAST({self._hours_sunday_close_column} AS STRING) AS close) AS sunday
                ) AS hours
            FROM {self._table}
            WHERE CAST({self._id_column} AS STRING) = @location_id
            LIMIT 1
        """
        params = [bigquery.ScalarQueryParameter("location_id", "STRING", location_id)]
        return self._runner.fetch_one(query, params)
