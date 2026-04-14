import logging

from app.repositories.orders import OrderRepository
from app.schemas.member import MemberFavoriteItem, MemberFavoriteTrendPoint
from app.schemas.order import Order, OrderItem, OrderQueryParams


logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def list_member_orders(self, member_id: str, params: OrderQueryParams) -> list[Order]:
        rows = self._repository.list_orders_for_member(
            member_id=member_id,
            limit=params.limit,
            offset=params.offset,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        orders = [Order.model_validate(row) for row in rows]

        if params.include_items:
            order_ids = [order.order_id for order in orders]
            items_rows = self._repository.list_order_items(order_ids)
            items_by_order: dict[str, list[OrderItem]] = {}
            for item_row in items_rows:
                order_id = item_row.get("order_id")
                if order_id is None:
                    continue
                items_by_order.setdefault(order_id, []).append(
                    OrderItem.model_validate(item_row)
                )
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])

        logger.info(
            "Fetched orders member_id=%s limit=%s offset=%s count=%s include_items=%s",
            member_id,
            params.limit,
            params.offset,
            len(orders),
            params.include_items,
        )
        return orders

    def calculate_points(self, member_id: str) -> int:
        return self._repository.get_member_points(member_id)

    def list_location_orders(self, store_id: str, params: OrderQueryParams) -> list[Order]:
        rows = self._repository.list_orders_for_store(
            store_id=store_id,
            limit=params.limit,
            offset=params.offset,
            sort_by=params.sort_by,
            sort_dir=params.sort_dir,
        )
        orders = [Order.model_validate(row) for row in rows]
        if params.include_items:
            order_ids = [order.order_id for order in orders]
            items_rows = self._repository.list_order_items(order_ids)
            items_by_order: dict[str, list[OrderItem]] = {}
            for item_row in items_rows:
                order_id = item_row.get("order_id")
                if order_id is None:
                    continue
                items_by_order.setdefault(order_id, []).append(
                    OrderItem.model_validate(item_row)
                )
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        return orders

    def calculate_location_stats(self, store_id: str) -> dict:
        return self._repository.get_location_stats(store_id)

    def list_location_daily_stats(self, store_id: str, limit: int) -> list[dict]:
        return self._repository.get_location_daily_stats(store_id, limit)

    def list_location_weekly_stats(self, store_id: str, limit: int) -> list[dict]:
        return self._repository.get_location_weekly_stats(store_id, limit)

    def list_member_favorites(
        self,
        member_id: str,
        limit: int,
        window_days: int | None = None,
    ) -> list[MemberFavoriteItem]:
        rows = self._repository.list_member_favorites(
            member_id,
            limit,
            window_days=window_days,
        )
        return [MemberFavoriteItem.model_validate(row) for row in rows]

    def list_member_favorite_trends(
        self,
        member_id: str,
        limit_items: int,
        window_days: int,
    ) -> list[MemberFavoriteTrendPoint]:
        rows = self._repository.list_member_favorite_trends(
            member_id,
            limit_items,
            window_days,
        )
        return [MemberFavoriteTrendPoint.model_validate(row) for row in rows]
