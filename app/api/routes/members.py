from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_member_service, get_order_service
from app.schemas.common import ErrorResponse
from app.schemas.member import Member, MemberPoints
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
