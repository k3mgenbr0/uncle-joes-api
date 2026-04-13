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
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return service.search(query, limit, scope)
