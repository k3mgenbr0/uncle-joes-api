import logging

from app.repositories.stats import StatsRepository
from app.schemas.stats import OrderStats, TopLocation, TopMenuItem


logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self, repository: StatsRepository) -> None:
        self._repository = repository

    def get_order_stats(self) -> OrderStats:
        row = self._repository.get_order_stats()
        return OrderStats.model_validate(row)

    def get_top_menu_items(self, limit: int) -> list[TopMenuItem]:
        rows = self._repository.get_top_menu_items(limit)
        logger.info("Fetched top menu items count=%s", len(rows))
        return [TopMenuItem.model_validate(row) for row in rows]

    def get_top_locations(self, limit: int) -> list[TopLocation]:
        rows = self._repository.get_top_locations(limit)
        logger.info("Fetched top locations count=%s", len(rows))
        return [TopLocation.model_validate(row) for row in rows]
