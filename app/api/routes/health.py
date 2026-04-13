import logging

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import get_bigquery_runner
from app.db.bigquery import BigQueryRunner


logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/healthz", response_model=HealthResponse, summary="Liveness probe")
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/readyz",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
)
def readiness_check(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
) -> HealthResponse:
    runner.ping()
    logger.info("BigQuery readiness check succeeded")
    return HealthResponse(status="ready")
