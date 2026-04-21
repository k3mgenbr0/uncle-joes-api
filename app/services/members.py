import logging
import re

from app.core.errors import DatabaseError, NotFoundError
from app.repositories.locations import LocationRepository
from app.repositories.members import MemberRepository
from app.repositories.orders import OrderRepository
from app.schemas.member import Member, MemberPoints
from app.schemas.location import LocationSummary


logger = logging.getLogger(__name__)


class MemberService:
    def __init__(
        self,
        repository: MemberRepository,
        order_repository: OrderRepository,
        location_repository: LocationRepository,
    ) -> None:
        self._repository = repository
        self._order_repository = order_repository
        self._location_repository = location_repository

    def get_member(self, member_id: str) -> Member:
        member = self.get_member_identity(member_id)
        return self._enrich(member)

    def get_member_identity(self, member_id: str) -> Member:
        row = self._repository.get_member_by_id(member_id)
        if row is None:
            raise NotFoundError(f"Member '{member_id}' was not found.")
        return Member.model_validate(row)

    def get_points(self, member_id: str, points: int) -> MemberPoints:
        logger.info("Calculated points member_id=%s points=%s", member_id, points)
        return MemberPoints(member_id=member_id, total_points=points)

    def _enrich(self, member: Member) -> Member:
        member.preferred_store_id = member.home_store
        member.birthday_month_day = None
        member.marketing_opt_in = None
        member.profile_photo_url = None
        try:
            total_points = self._order_repository.get_member_points(member.member_id)
            member.rewards_tier = self._rewards_tier(total_points)
            member.points_to_next_reward = self._points_to_next_reward(total_points)
            member.join_date = self._order_repository.get_member_first_order_date(member.member_id)
        except DatabaseError:
            logger.warning("Skipping order-based member enrichment member_id=%s", member.member_id)
            member.rewards_tier = None
            member.points_to_next_reward = None
            member.join_date = None
        try:
            member.preferred_store = self._preferred_store(member.home_store)
        except DatabaseError:
            logger.warning(
                "Skipping preferred-store enrichment member_id=%s home_store=%s",
                member.member_id,
                member.home_store,
            )
            member.preferred_store = None
        return member

    def _preferred_store(self, location_id: str | None) -> LocationSummary | None:
        if not location_id:
            return None
        row = self._location_repository.get_location(location_id)
        if row is None:
            return None
        city = row.get("city")
        store_name = f"Uncle Joe's {city}" if city else None
        address_parts = [
            row.get("address_one"),
            row.get("address_two"),
            row.get("city"),
            row.get("state"),
            row.get("postal_code"),
        ]
        full_address = ", ".join(part for part in address_parts if part) or None
        address_one = row.get("address_one")
        street_label = None
        if address_one:
            street_label = re.sub(r"^\d+\s+", "", str(address_one)).strip()
            street_label = re.sub(r"\s+Suite\s+.+$", "", street_label, flags=re.IGNORECASE).strip()
        display_name = f"{city} - {street_label}" if city and street_label else city
        return LocationSummary(
            location_id=str(row["location_id"]),
            store_name=store_name,
            display_name=display_name,
            city=city,
            state=row.get("state"),
            full_address=full_address,
            address=full_address,
            phone=row.get("phone"),
        )

    @staticmethod
    def _rewards_tier(points: int) -> str:
        if points >= 500:
            return "platinum"
        if points >= 250:
            return "gold"
        if points >= 100:
            return "silver"
        return "bronze"

    @staticmethod
    def _points_to_next_reward(points: int) -> int:
        reward_increment = 25
        remainder = points % reward_increment
        return 0 if remainder == 0 else reward_increment - remainder
