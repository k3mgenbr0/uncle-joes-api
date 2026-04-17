from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table


class OrderRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._orders_table = quote_table(settings.resolved_orders_table)
        self._order_items_table = quote_table(settings.resolved_order_items_table)
        self._locations_table = quote_table(settings.resolved_locations_table)

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
        self._location_id_column = quote_column(settings.location_id_column)
        self._location_city_column = quote_column(settings.location_city_column)
        self._location_state_column = quote_column(settings.location_state_column)

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

    def list_member_orders_with_location(
        self,
        member_id: str,
        limit: int,
        offset: int,
    ) -> list[dict]:
        query = f"""
            SELECT
                CAST(o.{self._order_id_column} AS STRING) AS order_id,
                CAST(o.{self._order_store_id_column} AS STRING) AS store_id,
                CAST(l.{self._location_city_column} AS STRING) AS store_city,
                CAST(l.{self._location_state_column} AS STRING) AS store_state,
                o.{self._order_date_column} AS order_date,
                SAFE_CAST(o.{self._order_total_column} AS FLOAT64) AS order_total
            FROM {self._orders_table} AS o
            LEFT JOIN {self._locations_table} AS l
                ON CAST(o.{self._order_store_id_column} AS STRING)
                    = CAST(l.{self._location_id_column} AS STRING)
            WHERE CAST(o.{self._order_member_id_column} AS STRING) = @member_id
            ORDER BY o.{self._order_date_column} DESC
            LIMIT @limit OFFSET @offset
        """
        params = [
            bigquery.ScalarQueryParameter("member_id", "STRING", member_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
            bigquery.ScalarQueryParameter("offset", "INT64", offset),
        ]
        return self._runner.fetch_all(query, params)

    def count_member_orders(self, member_id: str) -> int:
        query = f"""
            SELECT COUNT(1) AS total_orders
            FROM {self._orders_table}
            WHERE CAST({self._order_member_id_column} AS STRING) = @member_id
        """
        params = [bigquery.ScalarQueryParameter("member_id", "STRING", member_id)]
        row = self._runner.fetch_one(query, params) or {"total_orders": 0}
        return int(row["total_orders"] or 0)

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

    def list_member_points_history(self, member_id: str, limit: int) -> list[dict]:
        query = f"""
            SELECT
                CAST(o.{self._order_id_column} AS STRING) AS order_id,
                CAST(o.{self._order_store_id_column} AS STRING) AS store_id,
                CAST(l.{self._location_city_column} AS STRING) AS store_city,
                CAST(l.{self._location_state_column} AS STRING) AS store_state,
                CAST(o.{self._order_date_column} AS STRING) AS order_date,
                SAFE_CAST(o.{self._order_total_column} AS FLOAT64) AS order_total,
                CAST(
                    COALESCE(
                        FLOOR(SAFE_CAST(o.{self._order_total_column} AS FLOAT64)),
                        0
                    ) AS INT64
                ) AS points_earned
            FROM {self._orders_table} AS o
            LEFT JOIN {self._locations_table} AS l
                ON CAST(o.{self._order_store_id_column} AS STRING)
                    = CAST(l.{self._location_id_column} AS STRING)
            WHERE CAST(o.{self._order_member_id_column} AS STRING) = @member_id
            ORDER BY o.{self._order_date_column} DESC
            LIMIT @limit
        """
        params = [
            bigquery.ScalarQueryParameter("member_id", "STRING", member_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
        return self._runner.fetch_all(query, params)

    def get_member_first_order_date(self, member_id: str) -> str | None:
        query = f"""
            SELECT CAST(MIN(DATE({self._order_date_column})) AS STRING) AS join_date
            FROM {self._orders_table}
            WHERE CAST({self._order_member_id_column} AS STRING) = @member_id
        """
        params = [bigquery.ScalarQueryParameter("member_id", "STRING", member_id)]
        row = self._runner.fetch_one(query, params) or {}
        return row.get("join_date")

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

    def list_member_favorites(
        self,
        member_id: str,
        limit: int,
        window_days: int | None = None,
    ) -> list[dict]:
        date_filter = ""
        params = [
            bigquery.ScalarQueryParameter("member_id", "STRING", member_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ]
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
                CAST(oi.{self._order_item_menu_item_id_column} AS STRING) AS menu_item_id,
                CAST(oi.{self._order_item_name_column} AS STRING) AS item_name,
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
                ) AS total_revenue
            FROM {self._order_items_table} AS oi
            INNER JOIN {self._orders_table} AS o
                ON CAST(oi.{self._order_item_order_id_column} AS STRING)
                    = CAST(o.{self._order_id_column} AS STRING)
            WHERE CAST(o.{self._order_member_id_column} AS STRING) = @member_id
            {date_filter}
            GROUP BY menu_item_id, item_name
            ORDER BY total_quantity DESC, total_revenue DESC
            LIMIT @limit
        """
        return self._runner.fetch_all(query, params)

    def list_member_favorite_trends(
        self,
        member_id: str,
        limit_items: int,
        window_days: int,
    ) -> list[dict]:
        query = f"""
            WITH member_items AS (
                SELECT
                    CAST(oi.{self._order_item_menu_item_id_column} AS STRING)
                        AS menu_item_id,
                    CAST(oi.{self._order_item_name_column} AS STRING) AS item_name,
                    CAST(o.{self._order_id_column} AS STRING) AS order_id,
                    DATE(o.{self._order_date_column}) AS order_date,
                    SAFE_CAST(oi.{self._order_item_quantity_column} AS INT64) AS quantity,
                    SAFE_CAST(oi.{self._order_item_price_column} AS FLOAT64) AS price
                FROM {self._order_items_table} AS oi
                INNER JOIN {self._orders_table} AS o
                    ON CAST(oi.{self._order_item_order_id_column} AS STRING)
                        = CAST(o.{self._order_id_column} AS STRING)
                WHERE CAST(o.{self._order_member_id_column} AS STRING) = @member_id
                  AND DATE(o.{self._order_date_column}) >= DATE_SUB(
                        CURRENT_DATE(), INTERVAL @window_days DAY
                  )
            ),
            top_items AS (
                SELECT
                    menu_item_id,
                    item_name,
                    SUM(quantity) AS total_quantity
                FROM member_items
                GROUP BY menu_item_id, item_name
                ORDER BY total_quantity DESC
                LIMIT @limit_items
            )
            SELECT
                mi.menu_item_id,
                mi.item_name,
                CAST(DATE_TRUNC(mi.order_date, WEEK(MONDAY)) AS STRING) AS week_start,
                COUNT(DISTINCT mi.order_id) AS total_orders,
                COALESCE(SUM(mi.quantity), 0) AS total_quantity,
                COALESCE(SUM(mi.quantity * mi.price), 0.0) AS total_revenue
            FROM member_items AS mi
            INNER JOIN top_items AS ti
                ON mi.menu_item_id = ti.menu_item_id
            GROUP BY menu_item_id, item_name, week_start
            ORDER BY week_start DESC, total_quantity DESC
        """
        params = [
            bigquery.ScalarQueryParameter("member_id", "STRING", member_id),
            bigquery.ScalarQueryParameter("limit_items", "INT64", limit_items),
            bigquery.ScalarQueryParameter("window_days", "INT64", window_days),
        ]
        return self._runner.fetch_all(query, params)

    def get_order_detail(self, order_id: str) -> dict | None:
        query = f"""
            SELECT
                CAST(o.{self._order_id_column} AS STRING) AS order_id,
                CAST(o.{self._order_member_id_column} AS STRING) AS member_id,
                CAST(o.{self._order_store_id_column} AS STRING) AS store_id,
                CAST(l.{self._location_city_column} AS STRING) AS store_city,
                CAST(l.{self._location_state_column} AS STRING) AS store_state,
                o.{self._order_date_column} AS order_date,
                SAFE_CAST(o.{self._items_subtotal_column} AS FLOAT64) AS subtotal,
                SAFE_CAST(o.{self._order_discount_column} AS FLOAT64) AS discount,
                SAFE_CAST(o.{self._sales_tax_column} AS FLOAT64) AS tax,
                SAFE_CAST(o.{self._order_total_column} AS FLOAT64) AS total
            FROM {self._orders_table} AS o
            LEFT JOIN {self._locations_table} AS l
                ON CAST(o.{self._order_store_id_column} AS STRING)
                    = CAST(l.{self._location_id_column} AS STRING)
            WHERE CAST(o.{self._order_id_column} AS STRING) = @order_id
            LIMIT 1
        """
        params = [bigquery.ScalarQueryParameter("order_id", "STRING", order_id)]
        return self._runner.fetch_one(query, params)

    def create_order(
        self,
        *,
        order_id: str,
        member_id: str,
        store_id: str,
        order_date,
        items_subtotal: float,
        order_discount: float,
        order_subtotal: float,
        sales_tax: float,
        order_total: float,
    ) -> None:
        query = f"""
            INSERT INTO {self._orders_table} (
                {self._order_id_column},
                {self._order_member_id_column},
                {self._order_store_id_column},
                {self._order_date_column},
                {self._items_subtotal_column},
                {self._order_discount_column},
                {self._order_subtotal_column},
                {self._sales_tax_column},
                {self._order_total_column}
            )
            VALUES (
                @order_id,
                @member_id,
                @store_id,
                @order_date,
                @items_subtotal,
                @order_discount,
                @order_subtotal,
                @sales_tax,
                @order_total
            )
        """
        params = [
            bigquery.ScalarQueryParameter("order_id", "STRING", order_id),
            bigquery.ScalarQueryParameter("member_id", "STRING", member_id),
            bigquery.ScalarQueryParameter("store_id", "STRING", store_id),
            bigquery.ScalarQueryParameter("order_date", "TIMESTAMP", order_date),
            bigquery.ScalarQueryParameter("items_subtotal", "FLOAT64", items_subtotal),
            bigquery.ScalarQueryParameter("order_discount", "FLOAT64", order_discount),
            bigquery.ScalarQueryParameter("order_subtotal", "FLOAT64", order_subtotal),
            bigquery.ScalarQueryParameter("sales_tax", "FLOAT64", sales_tax),
            bigquery.ScalarQueryParameter("order_total", "FLOAT64", order_total),
        ]
        self._runner.execute(query, params)

    def create_order_items(self, items: list[dict]) -> None:
        for item in items:
            query = f"""
                INSERT INTO {self._order_items_table} (
                    {self._order_item_id_column},
                    {self._order_item_order_id_column},
                    {self._order_item_menu_item_id_column},
                    {self._order_item_name_column},
                    {self._order_item_size_column},
                    {self._order_item_quantity_column},
                    {self._order_item_price_column}
                )
                VALUES (
                    @order_item_id,
                    @order_id,
                    @menu_item_id,
                    @item_name,
                    @size,
                    @quantity,
                    @price
                )
            """
            params = [
                bigquery.ScalarQueryParameter("order_item_id", "STRING", item["order_item_id"]),
                bigquery.ScalarQueryParameter("order_id", "STRING", item["order_id"]),
                bigquery.ScalarQueryParameter("menu_item_id", "STRING", item["menu_item_id"]),
                bigquery.ScalarQueryParameter("item_name", "STRING", item["item_name"]),
                bigquery.ScalarQueryParameter("size", "STRING", item["size"]),
                bigquery.ScalarQueryParameter("quantity", "INT64", item["quantity"]),
                bigquery.ScalarQueryParameter("price", "FLOAT64", item["price"]),
            ]
            self._runner.execute(query, params)

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
