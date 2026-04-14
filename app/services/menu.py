import logging

from app.core.errors import NotFoundError
from app.repositories.menu import MenuRepository
from app.schemas.menu import MenuItem, MenuItemStats, MenuQueryParams


logger = logging.getLogger(__name__)


class MenuService:
    def __init__(self, repository: MenuRepository) -> None:
        self._repository = repository

    def list_menu_items(self, params: MenuQueryParams) -> list[MenuItem]:
        rows = self._repository.list_menu_items(params)
        logger.info(
            "Fetched menu items category=%s limit=%s offset=%s count=%s",
            params.category,
            params.limit,
            params.offset,
            len(rows),
        )
        return [self._enrich(MenuItem.model_validate(row)) for row in rows]

    def get_menu_item(self, item_id: str) -> MenuItem:
        row = self._repository.get_menu_item(item_id)
        if row is None:
            raise NotFoundError(f"Menu item '{item_id}' was not found.")
        logger.info("Fetched menu item item_id=%s", item_id)
        return self._enrich(MenuItem.model_validate(row))

    def list_categories(self) -> list[str]:
        rows = self._repository.list_categories()
        logger.info("Fetched menu categories count=%s", len(rows))
        return rows

    def list_sizes(self) -> list[str]:
        rows = self._repository.list_sizes()
        logger.info("Fetched menu sizes count=%s", len(rows))
        return rows

    def get_menu_item_stats(self, item_id: str, window_days: int | None = None) -> MenuItemStats:
        if self._repository.get_menu_item(item_id) is None:
            raise NotFoundError(f"Menu item '{item_id}' was not found.")
        row = self._repository.get_menu_item_stats(item_id, window_days=window_days)
        logger.info("Fetched menu item stats item_id=%s window_days=%s", item_id, window_days)
        return MenuItemStats.model_validate(row)

    @staticmethod
    def _enrich(item: MenuItem) -> MenuItem:
        item.price_display = f"${item.price:,.2f}"
        return item
