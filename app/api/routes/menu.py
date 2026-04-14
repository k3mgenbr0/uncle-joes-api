from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_menu_service, get_recommendations_service
from app.schemas.common import ErrorResponse
from app.schemas.menu import MenuItem, MenuItemStats, MenuQueryParams, MenuRecommendation
from app.services.menu import MenuService
from app.services.recommendations import RecommendationsService


router = APIRouter(prefix="/menu", tags=["menu"])


@router.get(
    "",
    response_model=list[MenuItem],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="List menu items",
)
def list_menu_items(
    category: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    sort_by: Annotated[str | None, Query()] = None,
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: MenuService = Depends(get_menu_service),
) -> list[MenuItem]:
    params = MenuQueryParams(
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )
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


@router.get(
    "/recommendations",
    response_model=list[MenuRecommendation],
    responses={500: {"model": ErrorResponse}},
    summary="Get recommended menu items",
)
def get_menu_recommendations(
    kind: Annotated[str, Query(pattern="^(all_time|seasonal)$")] = "all_time",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    service: RecommendationsService = Depends(get_recommendations_service),
) -> list[MenuRecommendation]:
    return service.get_recommendations(kind, limit, window_days)


@router.get(
    "/categories",
    response_model=list[str],
    responses={500: {"model": ErrorResponse}},
    summary="List menu categories",
)
def list_menu_categories(
    service: MenuService = Depends(get_menu_service),
) -> list[str]:
    return service.list_categories()


@router.get(
    "/sizes",
    response_model=list[str],
    responses={500: {"model": ErrorResponse}},
    summary="List menu sizes",
)
def list_menu_sizes(
    service: MenuService = Depends(get_menu_service),
) -> list[str]:
    return service.list_sizes()


@router.get(
    "/{item_id}/stats",
    response_model=MenuItemStats,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get menu item stats",
)
def get_menu_item_stats(
    item_id: str,
    window_days: Annotated[int | None, Query(ge=1, le=365)] = None,
    service: MenuService = Depends(get_menu_service),
) -> MenuItemStats:
    return service.get_menu_item_stats(item_id, window_days=window_days)
