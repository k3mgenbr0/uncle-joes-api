import logging
import re

from app.core.errors import DatabaseError, NotFoundError
from app.repositories.locations import LocationRepository
from app.repositories.members import MemberRepository
from app.repositories.orders import OrderRepository
from app.schemas.member import Member, MemberPoints
from app.schemas.location import LocationSummary
from app.schemas.rewards import MemberRewardsSummary, BonusProgram, RewardThreshold, RewardTier


logger = logging.getLogger(__name__)

REWARD_TIERS: tuple[tuple[str, int], ...] = (
    ("bronze", 0),
    ("silver", 100),
    ("gold", 250),
    ("platinum", 500),
)


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

    def get_rewards_summary(self, member_id: str) -> MemberRewardsSummary:
        current_points = self._order_repository.get_member_points(member_id)
        lifetime_points = current_points
        summary = self._build_rewards_summary(
            member_id=member_id,
            current_points=current_points,
            lifetime_points=lifetime_points,
            points_last_30=self._order_repository.get_member_points_in_window(member_id, 30),
            points_last_90=self._order_repository.get_member_points_in_window(member_id, 90),
        )
        logger.info(
            "Calculated rewards summary member_id=%s tier=%s current_points=%s",
            member_id,
            summary.rewards_tier,
            summary.current_points,
        )
        return summary

    def get_rewards_program(self) -> dict:
        tiers = [RewardTier(name=name, min_points=min_points) for name, min_points in REWARD_TIERS]
        reward_thresholds = [
            RewardThreshold(name=f"{name.title()} Tier", points_required=min_points)
            for name, min_points in REWARD_TIERS
            if min_points > 0
        ]
        return {
            "points_rule": "1 point per whole dollar spent",
            "tiers": tiers,
            "reward_thresholds": reward_thresholds,
            "bonus_programs": [],
        }

    def _enrich(self, member: Member) -> Member:
        member.preferred_store_id = member.home_store
        member.birthday_month_day = None
        member.marketing_opt_in = None
        member.profile_photo_url = None
        try:
            total_points = self._order_repository.get_member_points(member.member_id)
            rewards = self._build_rewards_summary(
                member_id=member.member_id,
                current_points=total_points,
                lifetime_points=total_points,
                points_last_30=self._order_repository.get_member_points_in_window(
                    member.member_id,
                    30,
                ),
                points_last_90=self._order_repository.get_member_points_in_window(
                    member.member_id,
                    90,
                ),
            )
            member.rewards_tier = rewards.rewards_tier
            member.current_points = rewards.current_points
            member.lifetime_points = rewards.lifetime_points
            member.points_to_next_reward = rewards.points_to_next_reward
            member.next_tier_name = rewards.next_tier_name
            member.current_tier_min_points = rewards.current_tier_min_points
            member.next_tier_min_points = rewards.next_tier_min_points
            member.next_reward_threshold = rewards.next_reward_threshold
            member.current_reward_progress = rewards.current_reward_progress
            member.join_date = self._order_repository.get_member_first_order_date(member.member_id)
        except DatabaseError:
            logger.warning("Skipping order-based member enrichment member_id=%s", member.member_id)
            member.rewards_tier = None
            member.current_points = None
            member.lifetime_points = None
            member.points_to_next_reward = None
            member.next_tier_name = None
            member.current_tier_min_points = None
            member.next_tier_min_points = None
            member.next_reward_threshold = None
            member.current_reward_progress = None
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

    def _build_rewards_summary(
        self,
        *,
        member_id: str,
        current_points: int,
        lifetime_points: int,
        points_last_30: int,
        points_last_90: int,
    ) -> MemberRewardsSummary:
        tier_index = 0
        for index, (_, min_points) in enumerate(REWARD_TIERS):
            if current_points >= min_points:
                tier_index = index
        current_tier_name, current_tier_min = REWARD_TIERS[tier_index]
        if tier_index + 1 < len(REWARD_TIERS):
            next_tier_name, next_tier_min = REWARD_TIERS[tier_index + 1]
            points_to_next = max(next_tier_min - current_points, 0)
            next_reward_threshold = next_tier_min
        else:
            next_tier_name = None
            next_tier_min = None
            points_to_next = 0
            next_reward_threshold = current_points
        return MemberRewardsSummary(
            member_id=member_id,
            current_points=current_points,
            lifetime_points=lifetime_points,
            rewards_tier=current_tier_name,
            points_to_next_reward=points_to_next,
            next_tier_name=next_tier_name,
            current_tier_min_points=current_tier_min,
            next_tier_min_points=next_tier_min,
            next_reward_threshold=next_reward_threshold,
            current_reward_progress=current_points,
            points_earned_last_30_days=points_last_30,
            points_earned_last_90_days=points_last_90,
            bonus_programs=[],
        )
