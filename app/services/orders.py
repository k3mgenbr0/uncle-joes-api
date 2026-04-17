import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.core.errors import NotFoundError
from app.repositories.orders import OrderRepository
from app.schemas.member import MemberFavoriteItem, MemberFavoriteTrendPoint, MemberPointsHistoryEntry
from app.schemas.location import Location
from app.schemas.menu import MenuItem
from app.schemas.order import DashboardOrder, Order, OrderDetail, OrderItem, OrderQueryParams, PaymentSummary


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
                    self._enrich_order_item(OrderItem.model_validate(item_row))
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

    def list_member_points_history(
        self,
        member_id: str,
        limit: int,
    ) -> list[MemberPointsHistoryEntry]:
        rows = self._repository.list_member_points_history(member_id, limit)
        return [MemberPointsHistoryEntry.model_validate(row) for row in rows]

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
                    self._enrich_order_item(OrderItem.model_validate(item_row))
                )
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        return orders

    def list_member_dashboard_orders(
        self,
        member_id: str,
        limit: int,
        offset: int,
        include_items: bool,
    ) -> list[DashboardOrder]:
        rows = self._repository.list_member_orders_with_location(
            member_id=member_id,
            limit=limit,
            offset=offset,
        )
        orders = [DashboardOrder.model_validate(row) for row in rows]
        if include_items:
            order_ids = [order.order_id for order in orders]
            items_rows = self._repository.list_order_items(order_ids)
            items_by_order: dict[str, list[OrderItem]] = {}
            for item_row in items_rows:
                order_id = item_row.get("order_id")
                if order_id is None:
                    continue
                items_by_order.setdefault(order_id, []).append(
                    self._enrich_order_item(OrderItem.model_validate(item_row))
                )
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        for order in orders:
            if order.order_total is None:
                order.points_earned = 0
            else:
                order.points_earned = int(order.order_total // 1)
        return orders

    def count_member_orders(self, member_id: str) -> int:
        return self._repository.count_member_orders(member_id)

    def create_member_order(
        self,
        *,
        member_id: str,
        store: Location,
        items: list[dict],
        payment_method: str,
        tax_rate: float,
    ) -> OrderDetail:
        order_id = str(uuid4())
        order_date = datetime.now(timezone.utc)
        items_subtotal = round(
            sum(item["quantity"] * item["unit_price"] for item in items),
            2,
        )
        order_discount = 0.0
        order_subtotal = round(items_subtotal - order_discount, 2)
        sales_tax = round(order_subtotal * tax_rate, 2)
        order_total = round(order_subtotal + sales_tax, 2)

        self._repository.create_order(
            order_id=order_id,
            member_id=member_id,
            store_id=store.location_id,
            order_date=order_date,
            items_subtotal=items_subtotal,
            order_discount=order_discount,
            order_subtotal=order_subtotal,
            sales_tax=sales_tax,
            order_total=order_total,
        )
        self._repository.create_order_items(
            [
                {
                    "order_item_id": str(uuid4()),
                    "order_id": order_id,
                    "menu_item_id": item["menu_item_id"],
                    "item_name": item["item_name"],
                    "size": item["size"],
                    "quantity": item["quantity"],
                    "price": item["unit_price"],
                }
                for item in items
            ]
        )

        detail = self.get_order_detail(order_id)
        detail.payment_summary = PaymentSummary(
            subtotal=detail.subtotal,
            discount=detail.discount,
            tax=detail.tax,
            total=detail.total,
            method=payment_method,
            status="pending",
        )
        detail.points_redeemed = 0
        detail.store_name = store.store_name
        return detail

    def get_order_detail(self, order_id: str) -> OrderDetail:
        row = self._repository.get_order_detail(order_id)
        if row is None:
            raise NotFoundError(f"Order '{order_id}' was not found.")
        detail = OrderDetail.model_validate(row)
        item_rows = self._repository.list_order_items([order_id])
        detail.items = [
            self._enrich_order_item(OrderItem.model_validate(item_row))
            for item_row in item_rows
        ]
        detail.points_earned = int(detail.total // 1) if detail.total is not None else 0
        detail.points_redeemed = 0
        detail.store_name = f"Uncle Joe's {detail.store_city}" if detail.store_city else None
        detail.payment_summary = PaymentSummary(
            subtotal=detail.subtotal,
            discount=detail.discount,
            tax=detail.tax,
            total=detail.total,
            method="pay_in_store",
            status="pending",
        )
        return detail

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

    @staticmethod
    def _enrich_order_item(item: OrderItem) -> OrderItem:
        item.unit_price = item.price
        if item.price is not None and item.quantity is not None:
            item.line_total = round(item.price * item.quantity, 2)
        else:
            item.line_total = None
        return item

    @staticmethod
    def validate_order_item(
        menu_item: MenuItem,
        *,
        requested_size: str,
        quantity: int,
    ) -> dict:
        canonical_size = menu_item.size or requested_size
        return {
            "menu_item_id": menu_item.item_id,
            "item_name": menu_item.name,
            "size": canonical_size,
            "quantity": quantity,
            "unit_price": menu_item.price,
        }
