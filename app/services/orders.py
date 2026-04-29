import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.core.errors import DatabaseError, NotFoundError
from app.schemas.location import LocationSummary
from app.repositories.orders import OrderRepository
from app.schemas.member import MemberFavoriteItem, MemberFavoriteTrendPoint, MemberPointsHistoryEntry
from app.schemas.location import Location
from app.schemas.menu import MenuItem
from app.schemas.order import (
    DashboardOrder,
    Order,
    OrderDetail,
    OrderItem,
    OrderPreview,
    OrderQueryParams,
    PaymentSummary,
)
from app.services.locations import STORE_TIMEZONE


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
            items_by_order = self._load_order_items([order.order_id for order in orders])
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        self._hydrate_orders(orders)

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
            items_by_order = self._load_order_items([order.order_id for order in orders])
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        self._hydrate_orders(orders)
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
            items_by_order = self._load_order_items([order.order_id for order in orders])
            for order in orders:
                order.items = items_by_order.get(order.order_id, [])
        for order in orders:
            if order.order_total is None:
                order.points_earned = 0
            else:
                order.points_earned = int(order.order_total // 1)
            if order.order_status not in {"completed", "cancelled"}:
                order.order_status = self._progress_status(
                    order.submitted_at,
                    order.ready_by_estimate,
                )
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
        pickup_time,
        special_instructions: str | None,
        estimated_prep_minutes: int,
    ) -> OrderDetail:
        order_id = str(uuid4())
        submitted_at = datetime.now(timezone.utc)
        order_date = submitted_at
        items_subtotal = round(
            sum(item["quantity"] * item["unit_price"] for item in items),
            2,
        )
        order_discount = 0.0
        order_subtotal = round(items_subtotal - order_discount, 2)
        sales_tax = round(order_subtotal * tax_rate, 2)
        order_total = round(order_subtotal + sales_tax, 2)
        ready_by_estimate = pickup_time or (submitted_at + timedelta(minutes=estimated_prep_minutes))

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
        self._repository.create_order_metadata(
            order_id=order_id,
            pickup_time=pickup_time,
            ready_by_estimate=ready_by_estimate,
            submitted_at=submitted_at,
            order_status="order_received",
            estimated_prep_minutes=estimated_prep_minutes,
            payment_method=payment_method,
            payment_status="pending",
            special_instructions=special_instructions,
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
        detail.store_phone = store.phone
        detail.location = LocationSummary(
            location_id=store.location_id,
            store_name=store.store_name,
            display_name=store.display_name,
            city=store.city,
            state=store.state,
            full_address=store.full_address,
            address=store.address,
            phone=store.phone,
        )
        return detail

    def preview_member_order(
        self,
        *,
        member_id: str,
        store: Location,
        items: list[dict],
        payment_method: str,
        tax_rate: float,
        pickup_time,
        special_instructions: str | None,
        estimated_prep_minutes: int,
        source_order_id: str | None = None,
    ) -> OrderPreview:
        submitted_at = datetime.now(timezone.utc)
        subtotal = round(sum(item["quantity"] * item["unit_price"] for item in items), 2)
        discount = 0.0
        tax = round((subtotal - discount) * tax_rate, 2)
        total = round(subtotal - discount + tax, 2)
        ready_by_estimate = pickup_time or (submitted_at + timedelta(minutes=estimated_prep_minutes))
        order_id = f"preview-{uuid4()}"
        preview_items = [
            {
                "order_item_id": f"preview-item-{index}",
                "order_id": order_id,
                "menu_item_id": item["menu_item_id"],
                "item_name": item["item_name"],
                "size": item["size"],
                "quantity": item["quantity"],
                "price": item["unit_price"],
                "unit_price": item["unit_price"],
                "line_total": round(item["quantity"] * item["unit_price"], 2),
            }
            for index, item in enumerate(items, start=1)
        ]
        preview = OrderPreview(
            order_id=order_id,
            member_id=member_id,
            store_id=store.location_id,
            store_name=store.store_name,
            store_city=store.city,
            store_state=store.state,
            store_phone=store.phone,
            location=LocationSummary(
                location_id=store.location_id,
                store_name=store.store_name,
                display_name=store.display_name,
                city=store.city,
                state=store.state,
                full_address=store.full_address,
                address=store.address,
                phone=store.phone,
            ),
            order_date=submitted_at,
            pickup_time=pickup_time,
            ready_by_estimate=ready_by_estimate,
            submitted_at=submitted_at,
            order_status="order_received",
            estimated_prep_minutes=estimated_prep_minutes,
            special_instructions=special_instructions,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=total,
            points_earned=int(total // 1),
            points_redeemed=0,
            items=preview_items,
            payment_summary=PaymentSummary(
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                method=payment_method,
                status="pending",
            ),
            source_order_id=source_order_id,
            warnings=[],
        )
        return self._localize_order_datetimes(preview)

    def build_reorder_items(self, source_order: OrderDetail) -> list[dict]:
        return [
            {
                "menu_item_id": item.menu_item_id,
                "item_name": item.item_name,
                "size": item.size,
                "quantity": item.quantity,
                "unit_price": item.unit_price or item.price,
            }
            for item in source_order.items
            if item.menu_item_id and item.item_name and item.size and item.quantity and (item.unit_price is not None or item.price is not None)
        ]

    def get_order_detail(self, order_id: str) -> OrderDetail:
        row = self._repository.get_order_detail(order_id)
        if row is None:
            raise NotFoundError(f"Order '{order_id}' was not found.")
        detail = self._localize_order_datetimes(OrderDetail.model_validate(row))
        detail.items = self._load_order_items([order_id]).get(order_id, [])
        detail.points_earned = int(detail.total // 1) if detail.total is not None else 0
        detail.points_redeemed = 0
        detail.store_name = f"Uncle Joe's {detail.store_city}" if detail.store_city else None
        if detail.order_status not in {"completed", "cancelled"}:
            detail.order_status = self._progress_status(
                detail.submitted_at,
                detail.ready_by_estimate,
            )
        detail.payment_summary = PaymentSummary(
            subtotal=detail.subtotal,
            discount=detail.discount,
            tax=detail.tax,
            total=detail.total,
            method=row.get("payment_method") or "pay_in_store",
            status=row.get("payment_status") or "pending",
        )
        detail.location = LocationSummary(
            location_id=detail.store_id or "",
            store_name=detail.store_name,
            display_name=self._display_name_from_row(row),
            city=detail.store_city,
            state=detail.store_state,
            full_address=self._build_full_address(row),
            address=self._build_full_address(row),
            phone=detail.store_phone,
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
        *,
        store_available: bool | None = None,
    ) -> list[MemberFavoriteItem]:
        inferred_rows = self._repository.list_member_favorites(
            member_id,
            limit,
            window_days=window_days,
        )
        explicit_rows = self._repository.list_member_saved_favorites(member_id)
        merged: dict[str, dict] = {
            row["menu_item_id"]: {**row, "is_explicit": row.get("is_explicit", False)}
            for row in inferred_rows
        }
        for row in explicit_rows:
            existing = merged.get(row["menu_item_id"])
            if existing:
                existing["is_explicit"] = True
                existing.setdefault("category", row.get("category"))
                existing.setdefault("size", row.get("size"))
                existing.setdefault("current_price", row.get("current_price"))
                existing.setdefault("image_url", row.get("image_url"))
            else:
                merged[row["menu_item_id"]] = row
        rows = list(merged.values())[:limit]
        for row in rows:
            row["available_sizes"] = [row["size"]] if row.get("size") else []
            row["default_size"] = row.get("size")
            if store_available is not None:
                row["available_at_store"] = store_available
                row["store_availability_status"] = (
                    "available" if store_available else "unavailable"
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

    def add_member_favorite(self, member_id: str, menu_item: MenuItem) -> MemberFavoriteItem:
        self._repository.add_member_favorite(member_id, menu_item.item_id)
        return MemberFavoriteItem(
            menu_item_id=menu_item.item_id,
            item_name=menu_item.name,
            category=menu_item.category,
            size=menu_item.size,
            available_sizes=[menu_item.size] if menu_item.size else [],
            default_size=menu_item.size,
            current_price=menu_item.price,
            image_url=menu_item.image_url,
            is_explicit=True,
            total_orders=0,
            total_quantity=0,
            total_revenue=0.0,
        )

    def delete_member_favorite(self, member_id: str, menu_item_id: str) -> None:
        self._repository.delete_member_favorite(member_id, menu_item_id)

    @staticmethod
    def _progress_status(submitted_at, ready_by_estimate) -> str:
        if not submitted_at or not ready_by_estimate:
            return "order_received"
        now = datetime.now(timezone.utc)
        if now >= ready_by_estimate:
            return "ready_for_pickup"
        total_window = max((ready_by_estimate - submitted_at).total_seconds(), 1)
        elapsed = max((now - submitted_at).total_seconds(), 0)
        ratio = elapsed / total_window
        if ratio >= 0.66:
            return "finishing_touches"
        if ratio >= 0.33:
            return "brewing"
        return "order_received"

    @staticmethod
    def _build_full_address(row: dict) -> str | None:
        parts = [
            row.get("store_address_one"),
            row.get("store_address_two"),
            row.get("store_city"),
            row.get("store_state"),
            row.get("store_postal_code"),
        ]
        cleaned = [part for part in parts if part]
        return ", ".join(cleaned) if cleaned else None

    @staticmethod
    def _display_name_from_row(row: dict) -> str | None:
        city = row.get("store_city")
        if not city:
            return None
        address_one = row.get("store_address_one")
        if not address_one:
            return city
        street = str(address_one).lstrip("0123456789 ").strip()
        return f"{city} - {street}" if street else city

    def _load_order_items(self, order_ids: list[str]) -> dict[str, list[OrderItem]]:
        items_by_order: dict[str, list[OrderItem]] = {order_id: [] for order_id in order_ids if order_id}
        if not order_ids:
            return items_by_order
        try:
            item_rows = self._repository.list_order_items(order_ids)
        except DatabaseError:
            logger.warning("Bulk order-item lookup failed; falling back to per-order fetch.")
            item_rows = []
            for order_id in order_ids:
                try:
                    item_rows.extend(self._repository.list_order_items([order_id]))
                except DatabaseError:
                    logger.warning("Order-item lookup failed for order_id=%s; returning empty items.", order_id)
        for item_row in item_rows:
            order_id = item_row.get("order_id")
            if order_id is None:
                continue
            item = self._safe_order_item(item_row)
            if item:
                items_by_order.setdefault(order_id, []).append(item)
        return items_by_order

    def _hydrate_orders(self, orders: list[Order]) -> None:
        for order in orders:
            self._localize_order_datetimes(order)
            order.points_earned = int(order.order_total // 1) if order.order_total is not None else 0
            order.points_redeemed = 0
            if not order.store_name and order.store_city:
                order.store_name = f"Uncle Joe's {order.store_city}"
            if order.order_status not in {"completed", "cancelled"}:
                order.order_status = self._progress_status(
                    order.submitted_at,
                    order.ready_by_estimate,
                )

    def _safe_order_item(self, item_row: dict) -> OrderItem | None:
        try:
            return self._enrich_order_item(OrderItem.model_validate(item_row))
        except Exception:
            logger.warning("Skipping malformed order item row=%s", item_row)
            return None

    @staticmethod
    def _localize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(STORE_TIMEZONE)

    def _localize_order_datetimes(self, order):
        order.order_date = self._localize_datetime(order.order_date)
        order.pickup_time = self._localize_datetime(order.pickup_time)
        order.ready_by_estimate = self._localize_datetime(order.ready_by_estimate)
        order.submitted_at = self._localize_datetime(order.submitted_at)
        return order
