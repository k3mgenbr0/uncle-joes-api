from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table


class StatsRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._orders_table = quote_table(settings.resolved_orders_table)
        self._order_items_table = quote_table(settings.resolved_order_items_table)
        self._locations_table = quote_table(settings.resolved_locations_table)

        self._order_id_column = quote_column(settings.order_id_column)
        self._order_store_id_column = quote_column(settings.order_store_id_column)
        self._order_total_column = quote_column(settings.order_total_column)

        self._order_item_menu_item_id_column = quote_column(
            settings.order_item_menu_item_id_column
        )
        self._order_item_name_column = quote_column(settings.order_item_name_column)
        self._order_item_quantity_column = quote_column(settings.order_item_quantity_column)
        self._order_item_price_column = quote_column(settings.order_item_price_column)

        self._location_id_column = quote_column(settings.location_id_column)
        self._location_city_column = quote_column(settings.location_city_column)
        self._location_state_column = quote_column(settings.location_state_column)

    def get_order_stats(self) -> dict:
        query = f"""
            SELECT
                COUNT(1) AS total_orders,
                COALESCE(SUM(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS total_revenue,
                COALESCE(AVG(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS avg_order_total
            FROM {self._orders_table}
        """
        return self._runner.fetch_one(query) or {
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_order_total": 0.0,
        }

    def get_top_menu_items(self, limit: int) -> list[dict]:
        query = f"""
            SELECT
                CAST({self._order_item_menu_item_id_column} AS STRING) AS menu_item_id,
                CAST({self._order_item_name_column} AS STRING) AS item_name,
                COALESCE(SUM(SAFE_CAST({self._order_item_quantity_column} AS INT64)), 0)
                    AS total_quantity,
                COALESCE(
                    SUM(
                        SAFE_CAST({self._order_item_quantity_column} AS FLOAT64)
                        * SAFE_CAST({self._order_item_price_column} AS FLOAT64)
                    ),
                    0.0
                ) AS total_revenue
            FROM {self._order_items_table}
            GROUP BY menu_item_id, item_name
            ORDER BY total_quantity DESC, total_revenue DESC
            LIMIT @limit
        """
        params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]
        return self._runner.fetch_all(query, params)

    def get_top_locations(self, limit: int) -> list[dict]:
        query = f"""
            SELECT
                CAST(o.{self._order_store_id_column} AS STRING) AS store_id,
                CAST(l.{self._location_city_column} AS STRING) AS city,
                CAST(l.{self._location_state_column} AS STRING) AS state,
                COUNT(1) AS total_orders,
                COALESCE(SUM(SAFE_CAST(o.{self._order_total_column} AS FLOAT64)), 0.0)
                    AS total_revenue
            FROM {self._orders_table} o
            LEFT JOIN {self._locations_table} l
                ON CAST(o.{self._order_store_id_column} AS STRING)
                = CAST(l.{self._location_id_column} AS STRING)
            GROUP BY store_id, city, state
            ORDER BY total_orders DESC, total_revenue DESC
            LIMIT @limit
        """
        params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]
        return self._runner.fetch_all(query, params)
