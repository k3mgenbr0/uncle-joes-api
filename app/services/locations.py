import logging
import math
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.errors import BadRequestError, NotFoundError
from app.repositories.locations import LocationRepository
from app.schemas.location import (
    Location,
    LocationHoursDay,
    LocationQueryParams,
    NearbyLocationQueryParams,
)


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
        locations = [self._enrich(Location.model_validate(row)) for row in rows]
        self._decorate_nearby_metadata(locations)
        if params.orderable_only:
            locations = [location for location in locations if location.ordering_available]
        return locations

    def get_location(self, location_id: str) -> Location:
        row = self._repository.get_location(location_id)
        if row is None:
            raise NotFoundError(f"Location '{location_id}' was not found.")
        logger.info("Fetched location location_id=%s", location_id)
        location = self._enrich(Location.model_validate(row))
        pool = self.list_locations(LocationQueryParams(limit=500, offset=0))
        self._decorate_nearby_metadata([location], pool=pool)
        return location

    def list_nearby_locations(self, params: NearbyLocationQueryParams) -> list[Location]:
        locations = self.list_locations(LocationQueryParams(limit=500, offset=0))
        enriched: list[Location] = []
        for location in locations:
            if location.latitude is None or location.longitude is None:
                continue
            location.distance_miles = round(
                self._distance_miles(params.lat, params.lng, location.latitude, location.longitude),
                2,
            )
            if params.open_for_business is not None and location.open_for_business is not params.open_for_business:
                continue
            if params.orderable_only and not location.ordering_available:
                continue
            enriched.append(location)
        enriched.sort(key=lambda location: (location.distance_miles is None, location.distance_miles or math.inf, location.state, location.city))
        return enriched[: params.limit]

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
        location.address = location.full_address
        location.hours_today = self._today_hours(location)
        location.open_now = self._is_open_now(location.hours_today)
        location.store_name = f"Uncle Joe's {location.city}" if location.city else None
        location.display_name = self._display_name(location)
        location.services = self._services(location)
        location.holiday_hours = []
        # `open_for_business` is the single source of truth for whether a store can
        # be surfaced as orderable in both backend validation and frontend UX.
        location.pickup_supported = self._is_orderable(location)
        location.dine_in_supported = None
        location.ordering_available = self._is_orderable(location)
        if location.ordering_available:
            location.availability_status = "open"
            location.availability_message = None
        else:
            location.availability_status = "coming_soon"
            location.availability_message = "Coming Soon!"
        location.region = location.state
        location.metro_area = location.city
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
        normalized = value.strip()
        if normalized.isdigit():
            if len(normalized) == 3:
                normalized = f"0{normalized}"
            if len(normalized) == 4:
                normalized = f"{normalized[:2]}:{normalized[2:]}"
        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(normalized, fmt).time()
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
    def _is_orderable(location: Location) -> bool:
        # Treat null, missing, or invalid values as unavailable. Only an explicit
        # boolean True allows ordering.
        return location.open_for_business is True

    @staticmethod
    def _display_name(location: Location) -> str | None:
        if not location.city:
            return location.store_name
        street_source = location.address_one or location.near_by
        street_label = LocationService._street_label(street_source)
        if street_label:
            return f"{location.city} - {street_label}"
        return location.city

    @staticmethod
    def _street_label(value: str | None) -> str | None:
        if not value:
            return None
        street = value.split(";")[-1].strip()
        street = re.sub(r"^\d+\s+", "", street).strip()
        street = re.sub(r"\s+Suite\s+.+$", "", street, flags=re.IGNORECASE).strip()
        street = re.sub(r"\s+#.+$", "", street).strip()
        return street or None

    def _decorate_nearby_metadata(
        self,
        locations: list[Location],
        *,
        pool: list[Location] | None = None,
    ) -> None:
        comparison_pool = pool or locations
        orderable_pool = [
            candidate
            for candidate in comparison_pool
            if candidate.location_id
            and candidate.ordering_available
            and candidate.latitude is not None
            and candidate.longitude is not None
        ]
        for location in locations:
            location.nearby_store_ids = self._nearest_store_ids(location, orderable_pool)

    def _nearest_store_ids(
        self,
        location: Location,
        candidates: list[Location],
        *,
        limit: int = 3,
    ) -> list[str]:
        if location.latitude is None or location.longitude is None:
            return []
        ranked = [
            (
                self._distance_miles(
                    location.latitude,
                    location.longitude,
                    candidate.latitude,
                    candidate.longitude,
                ),
                candidate.location_id,
            )
            for candidate in candidates
            if candidate.location_id != location.location_id
        ]
        ranked.sort(key=lambda item: item[0])
        return [location_id for _, location_id in ranked[:limit]]

    @staticmethod
    def _distance_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        radius_miles = 3958.8
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        haversine = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
        )
        arc = 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))
        return radius_miles * arc
