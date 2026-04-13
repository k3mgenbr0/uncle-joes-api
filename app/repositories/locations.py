from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table
from app.schemas.location import LocationQueryParams


class LocationRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._table = quote_table(settings.resolved_locations_table)
        self._id_column = quote_column(settings.location_id_column)
        self._name_column = quote_column(settings.location_name_column)
        self._address_column = quote_column(settings.location_address_column)
        self._city_column = quote_column(settings.location_city_column)
        self._state_column = quote_column(settings.location_state_column)
        self._postal_code_column = quote_column(settings.location_postal_code_column)
        self._phone_column = quote_column(settings.location_phone_column)
        self._hours_column = quote_column(settings.location_hours_column)

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
                CAST({self._name_column} AS STRING) AS name,
                CAST({self._address_column} AS STRING) AS address,
                CAST({self._city_column} AS STRING) AS city,
                CAST({self._state_column} AS STRING) AS state,
                CAST({self._postal_code_column} AS STRING) AS postal_code,
                CAST({self._phone_column} AS STRING) AS phone,
                CAST({self._hours_column} AS STRING) AS hours
            FROM {self._table}
            {where_sql}
            ORDER BY {self._state_column}, {self._city_column}, {self._name_column}
            LIMIT @limit OFFSET @offset
        """
        return self._runner.fetch_all(query, query_params)

    def get_location(self, location_id: str) -> dict | None:
        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS location_id,
                CAST({self._name_column} AS STRING) AS name,
                CAST({self._address_column} AS STRING) AS address,
                CAST({self._city_column} AS STRING) AS city,
                CAST({self._state_column} AS STRING) AS state,
                CAST({self._postal_code_column} AS STRING) AS postal_code,
                CAST({self._phone_column} AS STRING) AS phone,
                CAST({self._hours_column} AS STRING) AS hours
            FROM {self._table}
            WHERE CAST({self._id_column} AS STRING) = @location_id
            LIMIT 1
        """
        params = [bigquery.ScalarQueryParameter("location_id", "STRING", location_id)]
        return self._runner.fetch_one(query, params)
