from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_location_service, get_order_service
from app.schemas.common import ErrorResponse
from app.schemas.location import Location, LocationQueryParams
from app.schemas.order import Order, OrderQueryParams
from app.schemas.stats import LocationOrderStats
from app.services.locations import LocationService
from app.services.orders import OrderService


router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "",
    response_model=list[Location],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="List coffee shop locations",
)
def list_locations(
    state: Annotated[str | None, Query(min_length=2, max_length=64)] = None,
    city: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    open_for_business: Annotated[bool | None, Query()] = None,
    wifi: Annotated[bool | None, Query()] = None,
    drive_thru: Annotated[bool | None, Query()] = None,
    door_dash: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: LocationService = Depends(get_location_service),
) -> list[Location]:
    params = LocationQueryParams(
        state=state,
        city=city,
        open_for_business=open_for_business,
        wifi=wifi,
        drive_thru=drive_thru,
        door_dash=door_dash,
        limit=limit,
        offset=offset,
    )
    return service.list_locations(params)


@router.get(
    "/{location_id}",
    response_model=Location,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get one location by ID",
)
def get_location(
    location_id: str,
    service: LocationService = Depends(get_location_service),
) -> Location:
    return service.get_location(location_id)


@router.get(
    "/{location_id}/orders",
    response_model=list[Order],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get orders for a location",
)
def get_location_orders(
    location_id: str,
    include_items: Annotated[bool, Query()] = False,
    sort_by: Annotated[str | None, Query()] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    location_service: LocationService = Depends(get_location_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
    location_service.get_location(location_id)
    params = OrderQueryParams(
        limit=limit,
        offset=offset,
        include_items=include_items,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return order_service.list_location_orders(location_id, params)


@router.get(
    "/{location_id}/stats",
    response_model=LocationOrderStats,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get order stats for a location",
)
def get_location_stats(
    location_id: str,
    location_service: LocationService = Depends(get_location_service),
    order_service: OrderService = Depends(get_order_service),
) -> LocationOrderStats:
    location_service.get_location(location_id)
    stats_row = order_service.calculate_location_stats(location_id)
    return LocationOrderStats.model_validate(stats_row)
