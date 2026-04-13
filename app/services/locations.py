import logging
from datetime import datetime, time

from app.core.errors import NotFoundError
from app.repositories.locations import LocationRepository
from app.schemas.location import Location, LocationHoursDay, LocationQueryParams


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
        return [self._enrich(Location.model_validate(row)) for row in rows]

    def get_location(self, location_id: str) -> Location:
        row = self._repository.get_location(location_id)
        if row is None:
            raise NotFoundError(f"Location '{location_id}' was not found.")
        logger.info("Fetched location location_id=%s", location_id)
        return self._enrich(Location.model_validate(row))

    def _enrich(self, location: Location) -> Location:
        location.full_address = self._build_full_address(location)
        location.hours_today = self._today_hours(location)
        location.open_now = self._is_open_now(location.hours_today)
        return location

    @staticmethod
    def _build_full_address(location: Location) -> str | None:
        parts = [
            location.address_one,
            location.address_two,
            location.city,
            location.state,
            location.postal_code,
        ]
        cleaned = [part for part in parts if part]
        return ", ".join(cleaned) if cleaned else None

    @staticmethod
    def _today_hours(location: Location) -> LocationHoursDay | None:
        weekday = datetime.now().strftime("%A").lower()
        return getattr(location.hours, weekday, None)

    @staticmethod
    def _parse_time(value: str | None) -> time | None:
        if not value:
            return None
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(value.strip(), fmt).time()
            except ValueError:
                continue
        return None

    def _is_open_now(self, hours: LocationHoursDay | None) -> bool | None:
        if not hours:
            return None
        open_time = self._parse_time(hours.open)
        close_time = self._parse_time(hours.close)
        if not open_time or not close_time:
            return None
        now = datetime.now().time()
        if open_time <= close_time:
            return open_time <= now <= close_time
        return now >= open_time or now <= close_time
