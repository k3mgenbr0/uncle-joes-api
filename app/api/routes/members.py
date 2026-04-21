from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_current_member,
    get_location_service,
    get_member_service,
    get_order_service,
)
from app.core.errors import UnauthorizedError
from app.schemas.common import ErrorResponse
from app.schemas.member import (
    Member,
    MemberFavoriteItem,
    MemberFavoriteTrendPoint,
    MemberPoints,
    MemberSummary,
)
from app.schemas.order import Order, OrderQueryParams
from app.services.members import MemberService
from app.services.locations import LocationService
from app.services.orders import OrderService


router = APIRouter(prefix="/members", tags=["members"])


@router.get(
    "/{member_id}",
    response_model=Member,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a Coffee Club member",
)
def get_member(
    member_id: str,
    current_member: Member = Depends(get_current_member),
    service: MemberService = Depends(get_member_service),
) -> Member:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    return service.get_member(member_id)


@router.get(
    "/{member_id}/orders",
    response_model=list[Order],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a member's order history",
)
def get_member_orders(
    member_id: str,
    include_items: Annotated[bool, Query()] = False,
    sort_by: Annotated[str | None, Query()] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member_service.get_member(member_id)
    params = OrderQueryParams(
        limit=limit,
        offset=offset,
        include_items=include_items,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return order_service.list_member_orders(member_id, params)


@router.get(
    "/{member_id}/points",
    response_model=MemberPoints,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a member's loyalty points",
)
def get_member_points(
    member_id: str,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberPoints:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member_service.get_member(member_id)
    points = order_service.calculate_points(member_id)
    return member_service.get_points(member_id, points)


@router.get(
    "/{member_id}/recent",
    response_model=list[Order],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a member's recent orders",
)
def get_member_recent_orders(
    member_id: str,
    include_items: Annotated[bool, Query()] = True,
    limit: Annotated[int, Query(ge=1, le=25)] = 5,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member_service.get_member(member_id)
    params = OrderQueryParams(
        limit=limit,
        offset=0,
        include_items=include_items,
        sort_by="order_date",
        sort_dir="desc",
    )
    return order_service.list_member_orders(member_id, params)


@router.get(
    "/{member_id}/favorites",
    response_model=list[MemberFavoriteItem],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a member's favorite menu items",
)
def get_member_favorites(
    member_id: str,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    store_id: Annotated[str | None, Query(min_length=1)] = None,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
    location_service: LocationService = Depends(get_location_service),
) -> list[MemberFavoriteItem]:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member_service.get_member(member_id)
    store_available = None
    if store_id:
        store_available = location_service.get_location(store_id).ordering_available
    return order_service.list_member_favorites(
        member_id,
        limit,
        window_days=window_days,
        store_available=store_available,
    )


@router.get(
    "/{member_id}/favorites/trends",
    response_model=list[MemberFavoriteTrendPoint],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get weekly trends for a member's favorite items",
)
def get_member_favorite_trends(
    member_id: str,
    window_days: Annotated[int, Query(ge=7, le=365)] = 90,
    limit_items: Annotated[int, Query(ge=1, le=10)] = 5,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[MemberFavoriteTrendPoint]:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member_service.get_member(member_id)
    return order_service.list_member_favorite_trends(
        member_id,
        limit_items=limit_items,
        window_days=window_days,
    )


@router.get(
    "/{member_id}/summary",
    response_model=MemberSummary,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get a member summary (profile, points, recents, favorites)",
)
def get_member_summary(
    member_id: str,
    include_items: Annotated[bool, Query()] = True,
    recent_limit: Annotated[int, Query(ge=1, le=25)] = 5,
    favorites_limit: Annotated[int, Query(ge=1, le=50)] = 10,
    favorites_window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    store_id: Annotated[str | None, Query(min_length=1)] = None,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
    location_service: LocationService = Depends(get_location_service),
) -> MemberSummary:
    if current_member.member_id != member_id:
        raise UnauthorizedError("Access denied.")
    member = member_service.get_member(member_id)
    points = member_service.get_points(member_id, order_service.calculate_points(member_id))
    recent_params = OrderQueryParams(
        limit=recent_limit,
        offset=0,
        include_items=include_items,
        sort_by="order_date",
        sort_dir="desc",
    )
    recent_orders = order_service.list_member_orders(member_id, recent_params)
    store_available = None
    if store_id:
        store_available = location_service.get_location(store_id).ordering_available
    favorites = order_service.list_member_favorites(
        member_id,
        favorites_limit,
        window_days=favorites_window_days,
        store_available=store_available,
    )
    return MemberSummary(
        member=member,
        points=points,
        recent_orders=recent_orders,
        favorites=favorites,
    )
