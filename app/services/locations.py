import logging

from app.core.errors import NotFoundError
from app.repositories.locations import LocationRepository
from app.schemas.location import Location, LocationQueryParams


logger = logging.getLogger(__name__)


class LocationService:
    def __init__(self, repository: LocationRepository) -> None:
        self._repository = repository

    def list_locations(self, params: LocationQueryParams) -> list[Location]:
        rows = self._repository.list_locations(params)
        logger.info(
            "Fetched locations state=%s city=%s limit=%s offset=%s count=%s",
            params.state,
            params.city,
            params.limit,
            params.offset,
            len(rows),
        )
        return [Location.model_validate(row) for row in rows]

    def get_location(self, location_id: str) -> Location:
        row = self._repository.get_location(location_id)
        if row is None:
            raise NotFoundError(f"Location '{location_id}' was not found.")
        logger.info("Fetched location location_id=%s", location_id)
        return Location.model_validate(row)
