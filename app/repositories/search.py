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

        self._menu_id_column = quote_column(settings.menu_item_id_column)
        self._menu_name_column = quote_column(settings.menu_name_column)
        self._menu_category_column = quote_column(settings.menu_category_column)
        self._menu_size_column = quote_column(settings.menu_size_column)

    def search_locations(self, query_text: str, limit: int) -> list[dict]:
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
            WHERE LOWER(CAST({self._location_city_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._location_state_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._location_address_one_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._location_address_two_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._location_nearby_column} AS STRING)) LIKE LOWER(@pattern)
            ORDER BY score DESC, {self._location_city_column}
            LIMIT @limit
        """
        params = [
            bigquery.ScalarQueryParameter("pattern", "STRING", f"%{query_text}%"),
            bigquery.ScalarQueryParameter("prefix", "STRING", f"{query_text}%"),
            bigquery.ScalarQueryParameter("exact", "STRING", query_text),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._runner.fetch_all(query, params)

    def search_menu(self, query_text: str, limit: int) -> list[dict]:
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
            WHERE LOWER(CAST({self._menu_name_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._menu_category_column} AS STRING)) LIKE LOWER(@pattern)
               OR LOWER(CAST({self._menu_size_column} AS STRING)) LIKE LOWER(@pattern)
            ORDER BY score DESC, {self._menu_name_column}
            LIMIT @limit
        """
        params = [
            bigquery.ScalarQueryParameter("pattern", "STRING", f"%{query_text}%"),
            bigquery.ScalarQueryParameter("prefix", "STRING", f"{query_text}%"),
            bigquery.ScalarQueryParameter("exact", "STRING", query_text),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._runner.fetch_all(query, params)
