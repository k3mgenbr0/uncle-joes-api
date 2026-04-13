import logging
import re
from decimal import Decimal
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.cloud import bigquery

from app.core.errors import DatabaseError


logger = logging.getLogger(__name__)

_COLUMN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_TABLE_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def quote_column(identifier: str) -> str:
    if not _COLUMN_RE.fullmatch(identifier):
        msg = f"Unsafe BigQuery column identifier: {identifier}"
        raise ValueError(msg)
    return f"`{identifier}`"


def quote_table(identifier: str) -> str:
    if not _TABLE_RE.fullmatch(identifier):
        msg = f"Unsafe BigQuery table identifier: {identifier}"
        raise ValueError(msg)
    return f"`{identifier}`"


class BigQueryRunner:
    def __init__(self, client: bigquery.Client) -> None:
        self._client = client

    def fetch_all(
        self,
        query: str,
        parameters: list[bigquery.ScalarQueryParameter] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            job_config = bigquery.QueryJobConfig(query_parameters=parameters or [])
            rows = self._client.query(query, job_config=job_config).result()
            return [self._normalize_row(dict(row)) for row in rows]
        except GoogleAPIError as exc:
            logger.exception("BigQuery request failed")
            raise DatabaseError() from exc
        except Exception as exc:
            logger.exception("Unexpected BigQuery failure")
            raise DatabaseError() from exc

    def fetch_one(
        self,
        query: str,
        parameters: list[bigquery.ScalarQueryParameter] | None = None,
    ) -> dict[str, Any] | None:
        rows = self.fetch_all(query, parameters)
        return rows[0] if rows else None

    def ping(self) -> None:
        self.fetch_one("SELECT 1 AS ok")

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                normalized[key] = float(value)
            else:
                normalized[key] = value
        return normalized
