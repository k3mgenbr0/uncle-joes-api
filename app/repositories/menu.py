from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table
from app.schemas.menu import MenuQueryParams


class MenuRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._table = quote_table(settings.resolved_menu_table)
        self._id_column = quote_column(settings.menu_item_id_column)
        self._name_column = quote_column(settings.menu_name_column)
        self._category_column = quote_column(settings.menu_category_column)
        self._size_column = quote_column(settings.menu_size_column)
        self._calories_column = quote_column(settings.menu_calories_column)
        self._price_column = quote_column(settings.menu_price_column)

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

        query_params.extend(
            [
                bigquery.ScalarQueryParameter("limit", "INT64", params.limit),
                bigquery.ScalarQueryParameter("offset", "INT64", params.offset),
            ]
        )

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
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
            ORDER BY {self._category_column}, {self._name_column}
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
