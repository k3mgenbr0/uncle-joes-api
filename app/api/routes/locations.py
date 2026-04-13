from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_location_service
from app.schemas.common import ErrorResponse
from app.schemas.location import Location, LocationQueryParams
from app.services.locations import LocationService


router = APIRouter(prefix="/locations", tags=["locations"])


@router.get(
    "",
    response_model=list[Location],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="List coffee shop locations",
)
def list_locations(
    state: Annotated[str | None, Query(min_length=2, max_length=64)] = None,
    city: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
    offset: Annotated[int, Query(ge=0)] = 0,
    service: LocationService = Depends(get_location_service),
) -> list[Location]:
    params = LocationQueryParams(state=state, city=city, limit=limit, offset=offset)
    return service.list_locations(params)


@router.get(
    "/{location_id}",
    response_model=Location,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get one location by ID",
)
def get_location(
    location_id: str,
    service: LocationService = Depends(get_location_service),
) -> Location:
    return service.get_location(location_id)
