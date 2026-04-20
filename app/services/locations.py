import logging
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.errors import BadRequestError, NotFoundError
from app.repositories.locations import LocationRepository
from app.schemas.location import Location, LocationHoursDay, LocationQueryParams


logger = logging.getLogger(__name__)
STORE_TIMEZONE = ZoneInfo("America/Indiana/Indianapolis")


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

    def validate_pickup_time(
        self,
        location: Location,
        pickup_time: datetime,
    ) -> datetime:
        pickup_local = self._normalize_pickup_time(pickup_time)
        weekday = pickup_local.strftime("%A").lower()
        hours = getattr(location.hours, weekday, None)
        logger.info(
            "Validating pickup time store_id=%s pickup_time_raw=%s pickup_time_local=%s weekday=%s hours=%s",
            location.location_id,
            pickup_time.isoformat(),
            pickup_local.isoformat(),
            weekday,
            hours.model_dump() if hasattr(hours, "model_dump") else hours,
        )
        if not hours:
            raise BadRequestError(f"This store is closed on {pickup_local.strftime('%A')}.")
        open_time = self._parse_time(hours.open)
        close_time = self._parse_time(hours.close)
        if not open_time or not close_time:
            raise BadRequestError(f"This store is closed on {pickup_local.strftime('%A')}.")

        if pickup_local <= datetime.now(STORE_TIMEZONE):
            raise BadRequestError("Pickup time must be in the future.")
        open_at = pickup_local.replace(
            hour=open_time.hour,
            minute=open_time.minute,
            second=open_time.second,
            microsecond=0,
        )
        close_at = pickup_local.replace(
            hour=close_time.hour,
            minute=close_time.minute,
            second=close_time.second,
            microsecond=0,
        )
        if close_at <= open_at:
            close_at += timedelta(days=1)
            if pickup_local < open_at:
                pickup_local += timedelta(days=1)

        if pickup_local < open_at or pickup_local >= close_at:
            raise BadRequestError(
                f"Pickup time must be between {open_at.strftime('%-I:%M %p')} and {close_at.strftime('%-I:%M %p')} for this store."
            )
        return pickup_local

    def _enrich(self, location: Location) -> Location:
        location.full_address = self._build_full_address(location)
        location.hours_today = self._today_hours(location)
        location.open_now = self._is_open_now(location.hours_today)
        location.store_name = f"Uncle Joe's {location.city}" if location.city else None
        location.services = self._services(location)
        location.holiday_hours = []
        location.pickup_supported = self._pickup_supported(location)
        location.dine_in_supported = None
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

    @staticmethod
    def _normalize_pickup_time(pickup_time: datetime) -> datetime:
        if pickup_time.tzinfo is None:
            return pickup_time.replace(tzinfo=STORE_TIMEZONE)
        # Treat the submitted ISO timestamp as a store-local wall-clock selection
        # so the picked date/time stays aligned with the schedule shown in the UI.
        return datetime(
            pickup_time.year,
            pickup_time.month,
            pickup_time.day,
            pickup_time.hour,
            pickup_time.minute,
            pickup_time.second,
            pickup_time.microsecond,
            tzinfo=STORE_TIMEZONE,
        )

    @staticmethod
    def _services(location: Location) -> list[str]:
        services: list[str] = []
        if location.wifi:
            services.append("wifi")
        if location.drive_thru:
            services.append("drive_thru")
        if location.door_dash:
            services.append("door_dash")
        if location.open_for_business:
            services.append("in_store")
        return services

    @staticmethod
    def _pickup_supported(location: Location) -> bool | None:
        if location.open_for_business is None and location.drive_thru is None and location.door_dash is None:
            return None
        return bool(location.open_for_business or location.drive_thru or location.door_dash)
