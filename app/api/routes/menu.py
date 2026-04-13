from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_menu_service
from app.schemas.common import ErrorResponse
from app.schemas.menu import MenuItem, MenuQueryParams
from app.services.menu import MenuService


router = APIRouter(prefix="/menu", tags=["menu"])


@router.get(
    "",
    response_model=list[MenuItem],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="List menu items",
)
def list_menu_items(
    category: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: MenuService = Depends(get_menu_service),
) -> list[MenuItem]:
    params = MenuQueryParams(category=category, limit=limit, offset=offset)
    return service.list_menu_items(params)


@router.get(
    "/{item_id}",
    response_model=MenuItem,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get one menu item by ID",
)
def get_menu_item(
    item_id: str,
    service: MenuService = Depends(get_menu_service),
) -> MenuItem:
    return service.get_menu_item(item_id)
