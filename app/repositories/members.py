from google.cloud import bigquery

from app.core.config import Settings
from app.db.bigquery import BigQueryRunner, quote_column, quote_table


class MemberRepository:
    def __init__(self, runner: BigQueryRunner, settings: Settings) -> None:
        self._runner = runner
        self._table = quote_table(settings.resolved_members_table)
        self._id_column = quote_column(settings.member_id_column)
        self._first_name_column = quote_column(settings.member_first_name_column)
        self._last_name_column = quote_column(settings.member_last_name_column)
        self._email_column = quote_column(settings.member_email_column)
        self._password_column = quote_column(settings.member_password_column)

    def get_member_by_email(self, email: str) -> dict | None:
        query = f"""
            SELECT
                CAST({self._id_column} AS STRING) AS member_id,
                CAST({self._first_name_column} AS STRING) AS first_name,
                CAST({self._last_name_column} AS STRING) AS last_name,
                CAST({self._email_column} AS STRING) AS email,
                CAST({self._password_column} AS STRING) AS password_hash
            FROM {self._table}
            WHERE LOWER({self._email_column}) = LOWER(@email)
            LIMIT 1
        """
        params = [bigquery.ScalarQueryParameter("email", "STRING", email)]
        return self._runner.fetch_one(query, params)
