from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table
from app.schemas.menu import MenuQueryParams


class MenuRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._table = quote_table(settings.resolved_menu_table)
        self._orders_table = quote_table(settings.resolved_orders_table)
        self._order_items_table = quote_table(settings.resolved_order_items_table)
        self._id_column = quote_column(settings.menu_item_id_column)
        self._name_column = quote_column(settings.menu_name_column)
        self._category_column = quote_column(settings.menu_category_column)
        self._size_column = quote_column(settings.menu_size_column)
        self._calories_column = quote_column(settings.menu_calories_column)
        self._price_column = quote_column(settings.menu_price_column)
        self._order_id_column = quote_column(settings.order_id_column)
        self._order_date_column = quote_column(settings.order_date_column)
        self._order_item_order_id_column = quote_column(settings.order_item_order_id_column)
        self._order_item_menu_item_id_column = quote_column(
            settings.order_item_menu_item_id_column
        )
        self._order_item_name_column = quote_column(settings.order_item_name_column)
        self._order_item_quantity_column = quote_column(settings.order_item_quantity_column)
        self._order_item_price_column = quote_column(settings.order_item_price_column)

    def list_menu_items(self, params: MenuQueryParams) -> list[dict]:
        where_clauses: list[str] = []
        query_params: list[bigquery.ScalarQueryParameter] = []

        if params.category:
            where_clauses.append(
                f"LOWER({self._category_column}) = LOWER(@category)"
            )
            query_params.append(
                bigquery.ScalarQueryParameter("category", "STRING", params.category)
            )

        if params.min_price is not None:
            where_clauses.append(
                f"SAFE_CAST({self._price_column} AS FLOAT64) >= @min_price"
            )
            query_params.append(
                bigquery.ScalarQueryParameter("min_price", "FLOAT64", params.min_price)
            )

        if params.max_price is not None:
            where_clauses.append(
                f"SAFE_CAST({self._price_column} AS FLOAT64) <= @max_price"
            )
            query_params.append(
                bigquery.ScalarQueryParameter("max_price", "FLOAT64", params.max_price)
            )

        query_params.extend(
            [
                bigquery.ScalarQueryParameter("limit", "INT64", params.limit),
                bigquery.ScalarQueryParameter("offset", "INT64", params.offset),
            ]
        )

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        order_by = self._resolve_sort(params.sort_by, params.sort_dir)
        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS item_id,
                CAST({self._name_column} AS STRING) AS name,
                CAST({self._category_column} AS STRING) AS category,
                CAST({self._size_column} AS STRING) AS size,
                SAFE_CAST({self._calories_column} AS INT64) AS calories,
                COALESCE(SAFE_CAST({self._price_column} AS FLOAT64), 0.0) AS price
            FROM {self._table}
            {where_sql}
            ORDER BY {order_by}
            LIMIT @limit OFFSET @offset
        """
        return self._runner.fetch_all(query, query_params)

    def get_menu_item(self, item_id: str) -> dict | None:
        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS item_id,
                CAST({self._name_column} AS STRING) AS name,
                CAST({self._category_column} AS STRING) AS category,
                CAST({self._size_column} AS STRING) AS size,
                SAFE_CAST({self._calories_column} AS INT64) AS calories,
                COALESCE(SAFE_CAST({self._price_column} AS FLOAT64), 0.0) AS price
            FROM {self._table}
            WHERE CAST({self._id_column} AS STRING) = @item_id
            LIMIT 1
        """
        params = [bigquery.ScalarQueryParameter("item_id", "STRING", item_id)]
        return self._runner.fetch_one(query, params)

    def list_categories(self) -> list[str]:
        query = f"""
            SELECT DISTINCT CAST({self._category_column} AS STRING) AS category
            FROM {self._table}
            WHERE {self._category_column} IS NOT NULL
            ORDER BY category
        """
        rows = self._runner.fetch_all(query, [])
        return [row["category"] for row in rows if row.get("category")]

    def list_sizes(self) -> list[str]:
        query = f"""
            SELECT DISTINCT CAST({self._size_column} AS STRING) AS size
            FROM {self._table}
            WHERE {self._size_column} IS NOT NULL
            ORDER BY size
        """
        rows = self._runner.fetch_all(query, [])
        return [row["size"] for row in rows if row.get("size")]

    def get_menu_item_stats(self, item_id: str, window_days: int | None = None) -> dict:
        date_filter = ""
        params = [bigquery.ScalarQueryParameter("item_id", "STRING", item_id)]
        if window_days is not None:
            date_filter = (
                f"AND DATE(o.{self._order_date_column}) >= "
                "DATE_SUB(CURRENT_DATE(), INTERVAL @window_days DAY)"
            )
            params.append(
                bigquery.ScalarQueryParameter("window_days", "INT64", window_days)
            )
        query = f"""
            SELECT
                CAST(@item_id AS STRING) AS item_id,
                COUNT(DISTINCT CAST(oi.{self._order_item_order_id_column} AS STRING))
                    AS total_orders,
                COALESCE(
                    SUM(SAFE_CAST(oi.{self._order_item_quantity_column} AS INT64)),
                    0
                ) AS total_quantity,
                COALESCE(
                    SUM(
                        SAFE_CAST(oi.{self._order_item_quantity_column} AS FLOAT64)
                        * SAFE_CAST(oi.{self._order_item_price_column} AS FLOAT64)
                    ),
                    0.0
                ) AS total_revenue,
                CAST(MAX(DATE(o.{self._order_date_column})) AS STRING) AS last_order_date
            FROM {self._order_items_table} AS oi
            LEFT JOIN {self._orders_table} AS o
                ON CAST(oi.{self._order_item_order_id_column} AS STRING)
                    = CAST(o.{self._order_id_column} AS STRING)
            WHERE CAST(oi.{self._order_item_menu_item_id_column} AS STRING) = @item_id
            {date_filter}
        """
        return self._runner.fetch_one(query, params) or {
            "item_id": item_id,
            "total_orders": 0,
            "total_quantity": 0,
            "total_revenue": 0.0,
            "last_order_date": None,
        }

    def _resolve_sort(self, sort_by: str | None, sort_dir: str) -> str:
        sort_map = {
            "name": self._name_column,
            "category": self._category_column,
            "price": f"SAFE_CAST({self._price_column} AS FLOAT64)",
            "calories": f"SAFE_CAST({self._calories_column} AS INT64)",
        }
        column = sort_map.get((sort_by or "name").lower(), self._name_column)
        direction = "ASC" if sort_dir.lower() == "asc" else "DESC"
        return f"{column} {direction}, {self._name_column} ASC"
