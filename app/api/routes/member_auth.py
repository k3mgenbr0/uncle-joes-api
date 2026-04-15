from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import (
    get_auth_service,
    get_current_member,
    get_member_service,
    get_order_service,
)
from app.core.auth import create_session_token
from app.core.config import Settings, get_settings
from app.schemas.auth import LogoutResponse, LoginRequest, SessionResponse
from app.schemas.common import ErrorResponse
from app.schemas.member import Member, MemberDashboard
from app.services.auth import AuthService
from app.services.members import MemberService
from app.services.orders import OrderService


router = APIRouter(prefix="/api/member", tags=["member-auth"])


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
    member = member_service.get_member(member_row["member_id"])
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
    response.delete_cookie(settings.auth_cookie_name)
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
        pagination=pagination,
    )
