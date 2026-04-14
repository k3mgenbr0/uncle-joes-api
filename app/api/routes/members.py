from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_member_service, get_order_service
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
    service: MemberService = Depends(get_member_service),
) -> Member:
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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberPoints:
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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[MemberFavoriteItem]:
    member_service.get_member(member_id)
    return order_service.list_member_favorites(member_id, limit, window_days=window_days)


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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> list[MemberFavoriteTrendPoint]:
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
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberSummary:
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
    favorites = order_service.list_member_favorites(
        member_id,
        favorites_limit,
        window_days=favorites_window_days,
    )
    return MemberSummary(
        member=member,
        points=points,
        recent_orders=recent_orders,
        favorites=favorites,
    )
