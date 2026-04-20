import logging

from app.core.errors import NotFoundError
from app.repositories.menu import MenuRepository
from app.schemas.menu import MenuItem, MenuItemStats, MenuQueryParams, RelatedMenuItem


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
        related_rows = self._repository.list_related_items(
            item_id=item_id,
            category=row.get("category"),
        )
        logger.info("Fetched menu item item_id=%s", item_id)
        return self._enrich(
            MenuItem.model_validate(row),
            related_items=[RelatedMenuItem.model_validate(item) for item in related_rows],
        )

    def list_categories(self) -> list[str]:
        rows = self._repository.list_categories()
        logger.info("Fetched menu categories count=%s", len(rows))
        return rows

    def list_sizes(self) -> list[str]:
        rows = self._repository.list_sizes()
        logger.info("Fetched menu sizes count=%s", len(rows))
        return rows

    def list_menu_items_for_store(
        self,
        params: MenuQueryParams,
        *,
        store_available: bool,
    ) -> list[MenuItem]:
        items = self.list_menu_items(params)
        for item in items:
            item.available_at_store = store_available
            item.store_availability_status = "available" if store_available else "unavailable"
        return items

    def get_menu_item_for_store(
        self,
        item_id: str,
        *,
        store_available: bool,
    ) -> MenuItem:
        item = self.get_menu_item(item_id)
        item.available_at_store = store_available
        item.store_availability_status = "available" if store_available else "unavailable"
        return item

    def get_menu_item_stats(self, item_id: str, window_days: int | None = None) -> MenuItemStats:
        if self._repository.get_menu_item(item_id) is None:
            raise NotFoundError(f"Menu item '{item_id}' was not found.")
        row = self._repository.get_menu_item_stats(item_id, window_days=window_days)
        logger.info("Fetched menu item stats item_id=%s window_days=%s", item_id, window_days)
        return MenuItemStats.model_validate(row)

    @staticmethod
    def _enrich(item: MenuItem, related_items: list[RelatedMenuItem] | None = None) -> MenuItem:
        item.price_display = f"${item.price:,.2f}"
        item.description = None
        item.image_url = None
        item.ingredients = []
        item.allergens = []
        item.caffeine_mg = None
        item.availability_status = "available"
        item.seasonal = None
        item.tags = [
            value
            for value in [
                item.category.lower() if item.category else None,
                item.size.lower() if item.size else None,
                "under-200-calories" if item.calories is not None and item.calories < 200 else None,
            ]
            if value
        ]
        item.customization_options = []
        item.related_items = related_items or []
        return item
