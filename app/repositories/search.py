from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table


class SearchRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._locations_table = quote_table(settings.resolved_locations_table)
        self._menu_table = quote_table(settings.resolved_menu_table)

        self._location_id_column = quote_column(settings.location_id_column)
        self._location_city_column = quote_column(settings.location_city_column)
        self._location_state_column = quote_column(settings.location_state_column)
        self._location_address_one_column = quote_column(settings.location_address_one_column)
        self._location_address_two_column = quote_column(settings.location_address_two_column)
        self._location_nearby_column = quote_column(settings.location_nearby_column)
        self._location_open_for_business_column = quote_column(
            settings.location_open_for_business_column
        )
        self._location_wifi_column = quote_column(settings.location_wifi_column)
        self._location_drive_thru_column = quote_column(settings.location_drive_thru_column)
        self._location_door_dash_column = quote_column(settings.location_door_dash_column)

        self._menu_id_column = quote_column(settings.menu_item_id_column)
        self._menu_name_column = quote_column(settings.menu_name_column)
        self._menu_category_column = quote_column(settings.menu_category_column)
        self._menu_size_column = quote_column(settings.menu_size_column)
        self._menu_price_column = quote_column(settings.menu_price_column)

    def search_locations(self, query_text: str, limit: int, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        where_filters: list[str] = []
        params = [
            bigquery.ScalarQueryParameter("pattern", "STRING", f"%{query_text}%"),
            bigquery.ScalarQueryParameter("prefix", "STRING", f"{query_text}%"),
            bigquery.ScalarQueryParameter("exact", "STRING", query_text),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]

        if filters.get("state"):
            where_filters.append(
                f"LOWER(CAST({self._location_state_column} AS STRING)) = LOWER(@state)"
            )
            params.append(bigquery.ScalarQueryParameter("state", "STRING", filters["state"]))
        if filters.get("city"):
            where_filters.append(
                f"LOWER(CAST({self._location_city_column} AS STRING)) = LOWER(@city)"
            )
            params.append(bigquery.ScalarQueryParameter("city", "STRING", filters["city"]))
        if filters.get("open_for_business") is not None:
            where_filters.append(f"CAST({self._location_open_for_business_column} AS BOOL) = @open_for_business")
            params.append(
                bigquery.ScalarQueryParameter(
                    "open_for_business",
                    "BOOL",
                    filters["open_for_business"],
                )
            )
        if filters.get("wifi") is not None:
            where_filters.append(f"CAST({self._location_wifi_column} AS BOOL) = @wifi")
            params.append(bigquery.ScalarQueryParameter("wifi", "BOOL", filters["wifi"]))
        if filters.get("drive_thru") is not None:
            where_filters.append(
                f"CAST({self._location_drive_thru_column} AS BOOL) = @drive_thru"
            )
            params.append(
                bigquery.ScalarQueryParameter("drive_thru", "BOOL", filters["drive_thru"])
            )
        if filters.get("door_dash") is not None:
            where_filters.append(
                f"CAST({self._location_door_dash_column} AS BOOL) = @door_dash"
            )
            params.append(
                bigquery.ScalarQueryParameter("door_dash", "BOOL", filters["door_dash"])
            )

        filter_clause = ""
        if where_filters:
            filter_clause = " AND " + " AND ".join(where_filters)
        query = f"""
            SELECT
                CAST({self._location_id_column} AS STRING) AS location_id,
                CAST({self._location_city_column} AS STRING) AS city,
                CAST({self._location_state_column} AS STRING) AS state,
                CAST({self._location_address_one_column} AS STRING) AS address_one,
                CAST({self._location_address_two_column} AS STRING) AS address_two,
                CAST({self._location_nearby_column} AS STRING) AS near_by,
                CASE
                    WHEN LOWER(CAST({self._location_city_column} AS STRING)) = LOWER(@exact) THEN 5
                    WHEN LOWER(CAST({self._location_state_column} AS STRING)) = LOWER(@exact) THEN 4
                    WHEN LOWER(CAST({self._location_address_one_column} AS STRING)) LIKE LOWER(@prefix) THEN 3
                    WHEN LOWER(CAST({self._location_address_one_column} AS STRING)) LIKE LOWER(@pattern) THEN 2
                    ELSE 1
                END AS score
            FROM {self._locations_table}
            WHERE (
                LOWER(CAST({self._location_city_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._location_state_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._location_address_one_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._location_address_two_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._location_nearby_column} AS STRING)) LIKE LOWER(@pattern)
            )
            {filter_clause}
            ORDER BY score DESC, {self._location_city_column}
            LIMIT @limit
        """
        return self._runner.fetch_all(query, params)

    def search_menu(self, query_text: str, limit: int, filters: dict | None = None) -> list[dict]:
        filters = filters or {}
        where_filters: list[str] = []
        params = [
            bigquery.ScalarQueryParameter("pattern", "STRING", f"%{query_text}%"),
            bigquery.ScalarQueryParameter("prefix", "STRING", f"{query_text}%"),
            bigquery.ScalarQueryParameter("exact", "STRING", query_text),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]

        if filters.get("category"):
            where_filters.append(
                f"LOWER(CAST({self._menu_category_column} AS STRING)) = LOWER(@category)"
            )
            params.append(
                bigquery.ScalarQueryParameter("category", "STRING", filters["category"])
            )
        if filters.get("size"):
            where_filters.append(
                f"LOWER(CAST({self._menu_size_column} AS STRING)) = LOWER(@size)"
            )
            params.append(bigquery.ScalarQueryParameter("size", "STRING", filters["size"]))
        if filters.get("min_price") is not None:
            where_filters.append(f"CAST({self._menu_price_column} AS NUMERIC) >= @min_price")
            params.append(
                bigquery.ScalarQueryParameter("min_price", "NUMERIC", filters["min_price"])
            )
        if filters.get("max_price") is not None:
            where_filters.append(f"CAST({self._menu_price_column} AS NUMERIC) <= @max_price")
            params.append(
                bigquery.ScalarQueryParameter("max_price", "NUMERIC", filters["max_price"])
            )

        filter_clause = ""
        if where_filters:
            filter_clause = " AND " + " AND ".join(where_filters)
        query = f"""
            SELECT
                CAST({self._menu_id_column} AS STRING) AS item_id,
                CAST({self._menu_name_column} AS STRING) AS name,
                CAST({self._menu_category_column} AS STRING) AS category,
                CAST({self._menu_size_column} AS STRING) AS size,
                CASE
                    WHEN LOWER(CAST({self._menu_name_column} AS STRING)) = LOWER(@exact) THEN 5
                    WHEN LOWER(CAST({self._menu_name_column} AS STRING)) LIKE LOWER(@prefix) THEN 4
                    WHEN LOWER(CAST({self._menu_name_column} AS STRING)) LIKE LOWER(@pattern) THEN 3
                    WHEN LOWER(CAST({self._menu_category_column} AS STRING)) LIKE LOWER(@pattern) THEN 2
                    ELSE 1
                END AS score
            FROM {self._menu_table}
            WHERE (
                LOWER(CAST({self._menu_name_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._menu_category_column} AS STRING)) LIKE LOWER(@pattern)
                OR LOWER(CAST({self._menu_size_column} AS STRING)) LIKE LOWER(@pattern)
            )
            {filter_clause}
            ORDER BY score DESC, {self._menu_name_column}
            LIMIT @limit
        """
        return self._runner.fetch_all(query, params)
