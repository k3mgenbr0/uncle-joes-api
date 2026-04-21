from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_location_service, get_menu_service, get_order_service
from app.schemas.common import ErrorResponse
from app.schemas.location import Location, LocationQueryParams, NearbyLocationQueryParams
from app.schemas.menu import MenuItem, MenuQueryParams
from app.schemas.order import Order, OrderQueryParams
from app.schemas.stats import LocationDailyStats, LocationOrderStats, LocationWeeklyStats
from app.services.locations import LocationService
from app.services.menu import MenuService
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
    orderable_only: Annotated[bool, Query()] = False,
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
        orderable_only=orderable_only,
        wifi=wifi,
        drive_thru=drive_thru,
        door_dash=door_dash,
        limit=limit,
        offset=offset,
    )
    return service.list_locations(params)


@router.get(
    "/nearby",
    response_model=list[Location],
    responses={500: {"model": ErrorResponse}},
    summary="List nearby locations sorted by distance",
)
def list_nearby_locations(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    orderable_only: Annotated[bool, Query()] = False,
    open_for_business: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    service: LocationService = Depends(get_location_service),
) -> list[Location]:
    params = NearbyLocationQueryParams(
        lat=lat,
        lng=lng,
        orderable_only=orderable_only,
        open_for_business=open_for_business,
        limit=limit,
    )
    return service.list_nearby_locations(params)


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
    "/{location_id}/menu",
    response_model=list[MenuItem],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="List menu items for a specific pickup location",
)
def get_location_menu(
    location_id: str,
    category: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    sort_by: Annotated[str | None, Query()] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    location_service: LocationService = Depends(get_location_service),
    menu_service: MenuService = Depends(get_menu_service),
) -> list[MenuItem]:
    location = location_service.get_location(location_id)
    params = MenuQueryParams(
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
    store_available = location.ordering_available
    return menu_service.list_menu_items_for_store(params, store_available=store_available)


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


@router.get(
    "/{location_id}/stats/daily",
    response_model=list[LocationDailyStats],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get daily order stats for a location",
)
def get_location_daily_stats(
    location_id: str,
    limit: Annotated[int, Query(ge=1, le=366)] = 30,
    location_service: LocationService = Depends(get_location_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[LocationDailyStats]:
    location_service.get_location(location_id)
    rows = order_service.list_location_daily_stats(location_id, limit)
    return [LocationDailyStats.model_validate(row) for row in rows]


@router.get(
    "/{location_id}/stats/weekly",
    response_model=list[LocationWeeklyStats],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get weekly order stats for a location",
)
def get_location_weekly_stats(
    location_id: str,
    limit: Annotated[int, Query(ge=1, le=260)] = 12,
    location_service: LocationService = Depends(get_location_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[LocationWeeklyStats]:
    location_service.get_location(location_id)
    rows = order_service.list_location_weekly_stats(location_id, limit)
    return [LocationWeeklyStats.model_validate(row) for row in rows]
