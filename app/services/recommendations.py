import logging

from app.repositories.stats import StatsRepository
from app.schemas.menu import MenuRecommendation


logger = logging.getLogger(__name__)


class RecommendationsService:
    def __init__(self, repository: StatsRepository) -> None:
        self._repository = repository

    def get_recommendations(
        self,
        kind: str,
        limit: int,
        window_days: int | None,
    ) -> list[MenuRecommendation]:
        kind_value = kind.lower()
        if kind_value == "seasonal":
            days = window_days or 30
            rows = self._repository.get_top_menu_items_window(days, limit)
            return [
                MenuRecommendation(
                    item_id=row["menu_item_id"],
                    item_name=row.get("item_name"),
                    total_quantity=int(row.get("total_quantity") or 0),
                    total_revenue=float(row.get("total_revenue") or 0.0),
                    kind="seasonal",
                    window_days=days,
                )
                for row in rows
            ]

        rows = self._repository.get_top_menu_items(limit)
        return [
            MenuRecommendation(
                item_id=row["menu_item_id"],
                item_name=row.get("item_name"),
                total_quantity=int(row.get("total_quantity") or 0),
                total_revenue=float(row.get("total_revenue") or 0.0),
                kind="all_time",
                window_days=None,
            )
            for row in rows
        ]
