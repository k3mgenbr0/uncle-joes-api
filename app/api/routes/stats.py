from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_stats_service
from app.schemas.common import ErrorResponse
from app.schemas.stats import OrderStats, TopLocation, TopMenuItem
from app.services.stats import StatsService


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get(
    "/orders",
    response_model=OrderStats,
    responses={500: {"model": ErrorResponse}},
    summary="Get overall order statistics",
)
def get_order_stats(
    service: StatsService = Depends(get_stats_service),
) -> OrderStats:
    return service.get_order_stats()


@router.get(
    "/top-items",
    response_model=list[TopMenuItem],
    responses={500: {"model": ErrorResponse}},
    summary="Get top-selling menu items",
)
def get_top_items(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: StatsService = Depends(get_stats_service),
) -> list[TopMenuItem]:
    return service.get_top_menu_items(limit)


@router.get(
    "/top-locations",
    response_model=list[TopLocation],
    responses={500: {"model": ErrorResponse}},
    summary="Get top-performing store locations",
)
def get_top_locations(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    service: StatsService = Depends(get_stats_service),
) -> list[TopLocation]:
    return service.get_top_locations(limit)
