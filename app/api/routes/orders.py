from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_member, get_order_service
from app.core.errors import UnauthorizedError
from app.schemas.common import ErrorResponse
from app.schemas.member import Member
from app.schemas.order import OrderDetail
from app.services.orders import OrderService


router = APIRouter(prefix="/orders", tags=["orders"])


@router.get(
    "/{order_id}",
    response_model=OrderDetail,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get one order by ID for the authenticated member",
)
def get_order_detail(
    order_id: str,
    current_member: Member = Depends(get_current_member),
    order_service: OrderService = Depends(get_order_service),
) -> OrderDetail:
    detail = order_service.get_order_detail(order_id)
    if detail.member_id != current_member.member_id:
        raise UnauthorizedError("Access denied.")
    return detail
