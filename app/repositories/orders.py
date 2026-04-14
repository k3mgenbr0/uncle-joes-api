from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table


class OrderRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._orders_table = quote_table(settings.resolved_orders_table)
        self._order_items_table = quote_table(settings.resolved_order_items_table)

        self._order_id_column = quote_column(settings.order_id_column)
        self._order_member_id_column = quote_column(settings.order_member_id_column)
        self._order_store_id_column = quote_column(settings.order_store_id_column)
        self._order_date_column = quote_column(settings.order_date_column)
        self._items_subtotal_column = quote_column(settings.order_items_subtotal_column)
        self._order_discount_column = quote_column(settings.order_discount_column)
        self._order_subtotal_column = quote_column(settings.order_subtotal_column)
        self._sales_tax_column = quote_column(settings.order_sales_tax_column)
        self._order_total_column = quote_column(settings.order_total_column)

        self._order_item_id_column = quote_column(settings.order_item_id_column)
        self._order_item_order_id_column = quote_column(settings.order_item_order_id_column)
        self._order_item_menu_item_id_column = quote_column(
            settings.order_item_menu_item_id_column
        )
        self._order_item_name_column = quote_column(settings.order_item_name_column)
        self._order_item_size_column = quote_column(settings.order_item_size_column)
        self._order_item_quantity_column = quote_column(settings.order_item_quantity_column)
        self._order_item_price_column = quote_column(settings.order_item_price_column)

    def list_orders_for_member(
        self,
        member_id: str,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        sort_dir: str = "desc",
    ) -> list[dict]:
        return self._list_orders(
            filter_column=self._order_member_id_column,
            filter_param_name="member_id",
            filter_value=member_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def list_orders_for_store(
        self,
        store_id: str,
        limit: int,
        offset: int,
        sort_by: str | None = None,
        sort_dir: str = "desc",
    ) -> list[dict]:
        return self._list_orders(
            filter_column=self._order_store_id_column,
            filter_param_name="store_id",
            filter_value=store_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

    def list_order_items(self, order_ids: list[str]) -> list[dict]:
        if not order_ids:
            return []
        query = f"""
            SELECT
                CAST({self._order_item_id_column} AS STRING) AS order_item_id,
                CAST({self._order_item_order_id_column} AS STRING) AS order_id,
                CAST({self._order_item_menu_item_id_column} AS STRING) AS menu_item_id,
                CAST({self._order_item_name_column} AS STRING) AS item_name,
                CAST({self._order_item_size_column} AS STRING) AS size,
                SAFE_CAST({self._order_item_quantity_column} AS INT64) AS quantity,
                SAFE_CAST({self._order_item_price_column} AS FLOAT64) AS price
            FROM {self._order_items_table}
            WHERE CAST({self._order_item_order_id_column} AS STRING)
                IN UNNEST(@order_ids)
        """
        params = [
            bigquery.ArrayQueryParameter("order_ids", "STRING", order_ids),
        ]
        return self._runner.fetch_all(query, params)

    def get_member_points(self, member_id: str) -> int:
        query = f"""
            SELECT
                COALESCE(
                    SUM(CAST(FLOOR(SAFE_CAST({self._order_total_column} AS FLOAT64)) AS INT64)),
                    0
                ) AS total_points
            FROM {self._orders_table}
            WHERE CAST({self._order_member_id_column} AS STRING) = @member_id
        """
        params = [bigquery.ScalarQueryParameter("member_id", "STRING", member_id)]
        row = self._runner.fetch_one(query, params) or {"total_points": 0}
        return int(row["total_points"] or 0)

    def get_location_stats(self, store_id: str) -> dict:
        query = f"""
            SELECT
                CAST(@store_id AS STRING) AS store_id,
                COUNT(1) AS total_orders,
                COALESCE(SUM(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS total_revenue,
                COALESCE(AVG(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS avg_order_total
            FROM {self._orders_table}
            WHERE CAST({self._order_store_id_column} AS STRING) = @store_id
        """
        params = [bigquery.ScalarQueryParameter("store_id", "STRING", store_id)]
        return self._runner.fetch_one(query, params) or {
            "store_id": store_id,
            "total_orders": 0,
            "total_revenue": 0.0,
            "avg_order_total": 0.0,
        }

    def get_location_daily_stats(self, store_id: str, limit: int) -> list[dict]:
        query = f"""
            SELECT
                CAST(@store_id AS STRING) AS store_id,
                CAST(DATE({self._order_date_column}) AS STRING) AS order_date,
                COUNT(1) AS total_orders,
                COALESCE(SUM(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS total_revenue
            FROM {self._orders_table}
            WHERE CAST({self._order_store_id_column} AS STRING) = @store_id
            GROUP BY order_date
            ORDER BY order_date DESC
            LIMIT @limit
        """
        params = [
            bigquery.ScalarQueryParameter("store_id", "STRING", store_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._runner.fetch_all(query, params)

    def get_location_weekly_stats(self, store_id: str, limit: int) -> list[dict]:
        query = f"""
            SELECT
                CAST(@store_id AS STRING) AS store_id,
                CAST(DATE_TRUNC(DATE({self._order_date_column}), WEEK(MONDAY)) AS STRING)
                    AS week_start,
                COUNT(1) AS total_orders,
                COALESCE(SUM(SAFE_CAST({self._order_total_column} AS FLOAT64)), 0.0)
                    AS total_revenue
            FROM {self._orders_table}
            WHERE CAST({self._order_store_id_column} AS STRING) = @store_id
            GROUP BY week_start
            ORDER BY week_start DESC
            LIMIT @limit
        """
        params = [
            bigquery.ScalarQueryParameter("store_id", "STRING", store_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._runner.fetch_all(query, params)

    def _resolve_sort(self, sort_by: str | None, sort_dir: str) -> str:
        sort_map = {
            "order_date": self._order_date_column,
            "order_total": f"SAFE_CAST({self._order_total_column} AS FLOAT64)",
            "order_id": self._order_id_column,
        }
        column = sort_map.get((sort_by or "order_date").lower(), self._order_date_column)
        direction = "ASC" if sort_dir.lower() == "asc" else "DESC"
        return f"{column} {direction}, {self._order_id_column} DESC"

    def _list_orders(
        self,
        filter_column: str,
        filter_param_name: str,
        filter_value: str,
        limit: int,
        offset: int,
        sort_by: str | None,
        sort_dir: str,
    ) -> list[dict]:
        order_by = self._resolve_sort(sort_by, sort_dir)
        query = f"""
            SELECT
                CAST({self._order_id_column} AS STRING) AS order_id,
                CAST({self._order_member_id_column} AS STRING) AS member_id,
                CAST({self._order_store_id_column} AS STRING) AS store_id,
                {self._order_date_column} AS order_date,
                SAFE_CAST({self._items_subtotal_column} AS FLOAT64) AS items_subtotal,
                SAFE_CAST({self._order_discount_column} AS FLOAT64) AS order_discount,
                SAFE_CAST({self._order_subtotal_column} AS FLOAT64) AS order_subtotal,
                SAFE_CAST({self._sales_tax_column} AS FLOAT64) AS sales_tax,
                SAFE_CAST({self._order_total_column} AS FLOAT64) AS order_total
            FROM {self._orders_table}
            WHERE CAST({filter_column} AS STRING) = @{filter_param_name}
            ORDER BY {order_by}
            LIMIT @limit OFFSET @offset
        """
        params = [
            bigquery.ScalarQueryParameter(filter_param_name, "STRING", filter_value),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ]
        return self._runner.fetch_all(query, params)
