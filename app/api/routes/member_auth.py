from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Response

from app.api.dependencies import (
    get_auth_service,
    get_current_member,
    get_location_service,
    get_member_service,
    get_menu_service,
    get_order_service,
)
from app.core.auth import create_session_token
from app.core.config import Settings, get_settings
from app.core.errors import BadRequestError, UnauthorizedError
from app.schemas.auth import LogoutResponse, LoginRequest, SessionResponse
from app.schemas.common import ErrorResponse
from app.schemas.member import (
    Member,
    MemberDashboard,
    MemberFavoriteItem,
    MemberPoints,
    MemberPointsHistoryEntry,
    MemberSummary,
)
from app.schemas.order import CreateOrderRequest, Order, OrderDetail, OrderQueryParams
from app.services.auth import AuthService
from app.services.locations import LocationService
from app.services.members import MemberService
from app.services.menu import MenuService
from app.services.orders import OrderService


router = APIRouter(prefix="/api/member", tags=["member-auth"])

CREATE_ORDER_EXAMPLE = {
    "store_id": "101",
    "items": [
        {
            "menu_item_id": "latte",
            "quantity": 2,
            "size": "Medium",
        }
    ],
    "payment_method": "pay_in_store",
}

ORDER_DETAIL_EXAMPLE = {
    "order_id": "order-123",
    "member_id": "member-1",
    "store_id": "101",
    "store_name": "Uncle Joe's Indianapolis",
    "store_city": "Indianapolis",
    "store_state": "IN",
    "order_date": "2026-04-17T12:30:00Z",
    "subtotal": 9.0,
    "discount": 0.0,
    "tax": 0.63,
    "total": 9.63,
    "points_earned": 9,
    "points_redeemed": 0,
    "items": [
        {
            "order_item_id": "item-1",
            "order_id": "order-123",
            "menu_item_id": "latte",
            "item_name": "Latte",
            "size": "Medium",
            "quantity": 2,
            "price": 4.5,
            "unit_price": 4.5,
            "line_total": 9.0,
        }
    ],
    "payment_summary": {
        "subtotal": 9.0,
        "discount": 0.0,
        "tax": 0.63,
        "total": 9.63,
        "method": "pay_in_store",
        "status": "pending",
    },
}


@router.post(
    "/login",
    response_model=SessionResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Login and start a member session",
)
def member_login(
    body: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    member_service: MemberService = Depends(get_member_service),
    settings: Settings = Depends(get_settings),
) -> SessionResponse:
    member_row = auth_service.authenticate(body.email, body.password)
    member_id = member_row.get("id") or member_row.get("member_id")
    member = member_service.get_member_identity(member_id)
    ttl_seconds = settings.auth_cookie_ttl_minutes * 60
    token = create_session_token(
        member_id=member.member_id,
        email=member.email or "",
        secret=settings.auth_secret_key,
        ttl_seconds=ttl_seconds,
    )
    response.set_cookie(
        settings.auth_cookie_name,
        token,
        max_age=ttl_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )
    return SessionResponse(authenticated=True, member=member)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Logout and clear the member session",
)
def member_logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> LogoutResponse:
    response.delete_cookie(
        settings.auth_cookie_name,
        path="/",
        samesite=settings.auth_cookie_samesite,
    )
    return LogoutResponse(authenticated=False)


@router.get(
    "/session",
    response_model=SessionResponse,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the current member session",
)
def member_session(
    current_member: Member = Depends(get_current_member),
) -> SessionResponse:
    return SessionResponse(authenticated=True, member=current_member)


@router.get(
    "/profile",
    response_model=Member,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member profile",
)
def member_profile(
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
) -> Member:
    return member_service.get_member(current_member.member_id)


@router.get(
    "/points",
    response_model=MemberPoints,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member points",
)
def member_points(
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberPoints:
    points_value = order_service.calculate_points(current_member.member_id)
    return member_service.get_points(current_member.member_id, points_value)


@router.get(
    "/points/history",
    response_model=list[MemberPointsHistoryEntry],
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member points history",
)
def member_points_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
) -> list[MemberPointsHistoryEntry]:
    return order_service.list_member_points_history(current_member.member_id, limit)


@router.get(
    "/favorites",
    response_model=list[MemberFavoriteItem],
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member favorites",
)
def member_favorites(
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
) -> list[MemberFavoriteItem]:
    return order_service.list_member_favorites(
        current_member.member_id,
        limit,
        window_days=window_days,
    )


@router.get(
    "/orders",
    response_model=list[Order],
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member orders",
)
def member_orders(
    include_items: Annotated[bool, Query()] = False,
    sort_by: Annotated[str | None, Query()] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
) -> list[Order]:
    params = OrderQueryParams(
        limit=limit,
        offset=offset,
        include_items=include_items,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return order_service.list_member_orders(current_member.member_id, params)


@router.post(
    "/orders",
    response_model=OrderDetail,
    status_code=201,
    responses={
        201: {"content": {"application/json": {"example": ORDER_DETAIL_EXAMPLE}}},
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Create a pickup order for the authenticated member",
)
def create_member_order(
    body: CreateOrderRequest = Body(
        ...,
        examples={
            "pickup_order": {
                "summary": "Pickup order paid in store",
                "value": CREATE_ORDER_EXAMPLE,
            }
        },
    ),
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
    location_service: LocationService = Depends(get_location_service),
    menu_service: MenuService = Depends(get_menu_service),
    settings: Settings = Depends(get_settings),
) -> OrderDetail:
    store = location_service.get_location(body.store_id)
    if store.pickup_supported is False:
        raise BadRequestError("Pickup is not available at this location.")

    validated_items: list[dict] = []
    for item in body.items:
        menu_item = menu_service.get_menu_item(item.menu_item_id)
        if menu_item.size and menu_item.size.lower() != item.size.strip().lower():
            raise BadRequestError(
                f"Size '{item.size}' is not available for menu item '{item.menu_item_id}'."
            )
        validated_items.append(
            order_service.validate_order_item(
                menu_item,
                requested_size=item.size.strip(),
                quantity=item.quantity,
            )
        )

    return order_service.create_member_order(
        member_id=current_member.member_id,
        store=store,
        items=validated_items,
        payment_method=body.payment_method,
        tax_rate=settings.order_tax_rate,
    )


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetail,
    responses={
        200: {"content": {"application/json": {"example": ORDER_DETAIL_EXAMPLE}}},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get one authenticated member order by ID",
)
def member_order_detail(
    order_id: str,
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
) -> OrderDetail:
    detail = order_service.get_order_detail(order_id)
    if detail.member_id != current_member.member_id:
        raise UnauthorizedError("Access denied.")
    return detail


@router.get(
    "/summary",
    response_model=MemberSummary,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get an authenticated member summary",
)
def member_summary(
    include_items: Annotated[bool, Query()] = True,
    recent_limit: Annotated[int, Query(ge=1, le=25)] = 5,
    favorites_limit: Annotated[int, Query(ge=1, le=50)] = 10,
    favorites_window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberSummary:
    member = member_service.get_member(current_member.member_id)
    points = member_service.get_points(
        current_member.member_id,
        order_service.calculate_points(current_member.member_id),
    )
    recent_params = OrderQueryParams(
        limit=recent_limit,
        offset=0,
        include_items=include_items,
        sort_by="order_date",
        sort_dir="desc",
    )
    recent_orders = order_service.list_member_orders(current_member.member_id, recent_params)
    favorites = order_service.list_member_favorites(
        current_member.member_id,
        favorites_limit,
        window_days=favorites_window_days,
    )
    return MemberSummary(
        member=member,
        points=points,
        recent_orders=recent_orders,
        favorites=favorites,
    )


@router.get(
    "/dashboard",
    response_model=MemberDashboard,
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get the authenticated member dashboard data",
)
def member_dashboard(
    include_items: Annotated[bool, Query()] = True,
    limit: Annotated[int, Query(ge=1, le=50)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_member: Member = Depends(get_current_member),
    member_service: MemberService = Depends(get_member_service),
    order_service: OrderService = Depends(get_order_service),
) -> MemberDashboard:
    member = member_service.get_member(current_member.member_id)
    points_value = order_service.calculate_points(current_member.member_id)
    points = member_service.get_points(current_member.member_id, points_value)
    favorites = order_service.list_member_favorites(current_member.member_id, limit=10)
    points_history = order_service.list_member_points_history(
        current_member.member_id,
        limit=min(limit, 25),
    )
    orders = order_service.list_member_dashboard_orders(
        member_id=current_member.member_id,
        limit=limit,
        offset=offset,
        include_items=include_items,
    )
    total_orders = order_service.count_member_orders(current_member.member_id)
    pagination = {
        "limit": limit,
        "offset": offset,
        "total": total_orders,
    }
    return MemberDashboard(
        member=member,
        points=points,
        orders=orders,
        favorites=favorites,
        points_history=points_history,
        pagination=pagination,
    )
