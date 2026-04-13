import logging

from app.core.errors import NotFoundError
from app.repositories.menu import MenuRepository
from app.schemas.menu import MenuItem, MenuQueryParams


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

    @staticmethod
    def _enrich(item: MenuItem) -> MenuItem:
        item.price_display = f"${item.price:,.2f}"
        return item
