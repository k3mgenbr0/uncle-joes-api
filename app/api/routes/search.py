from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_search_service
from app.schemas.common import ErrorResponse
from app.schemas.search import SearchResponse
from app.services.search import SearchService


router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Search locations and menu items",
)
def search(
    query: Annotated[str, Query(min_length=2, max_length=100)],
    scope: Annotated[str, Query(pattern="^(all|locations|menu)$")] = "all",
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    fuzzy: Annotated[bool, Query(description="Enable fuzzy matching and ranking.")] = True,
    min_score: Annotated[
        float,
        Query(ge=0, le=5, description="Minimum score (0-5) to include in results."),
    ] = 0,
    location_state: Annotated[str | None, Query()] = None,
    location_city: Annotated[str | None, Query()] = None,
    location_open_for_business: Annotated[bool | None, Query()] = None,
    location_wifi: Annotated[bool | None, Query()] = None,
    location_drive_thru: Annotated[bool | None, Query()] = None,
    location_door_dash: Annotated[bool | None, Query()] = None,
    menu_category: Annotated[str | None, Query()] = None,
    menu_size: Annotated[str | None, Query()] = None,
    menu_min_price: Annotated[float | None, Query(ge=0)] = None,
    menu_max_price: Annotated[float | None, Query(ge=0)] = None,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    location_filters = {
        "state": location_state,
        "city": location_city,
        "open_for_business": location_open_for_business,
        "wifi": location_wifi,
        "drive_thru": location_drive_thru,
        "door_dash": location_door_dash,
    }
    menu_filters = {
        "category": menu_category,
        "size": menu_size,
        "min_price": menu_min_price,
        "max_price": menu_max_price,
    }
    return service.search(
        query,
        limit,
        scope,
        location_filters=location_filters,
        menu_filters=menu_filters,
        fuzzy=fuzzy,
        min_score=min_score,
    )
