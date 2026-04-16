import bcrypt
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_auth_service,
    get_current_member,
    get_location_service,
    get_member_service,
    get_menu_service,
    get_order_service,
    get_recommendations_service,
    get_search_service,
    get_stats_service,
)
from app.main import create_app
from app.schemas.auth import LoginResponse
from app.schemas.location import Location, LocationQueryParams
from app.schemas.member import (
    Member,
    MemberFavoriteItem,
    MemberFavoriteTrendPoint,
    MemberPoints,
)
from app.schemas.menu import MenuItem, MenuItemStats, MenuQueryParams
from app.schemas.order import DashboardOrder, Order, OrderDetail, OrderQueryParams
from app.schemas.search import SearchResponse, SearchResult
from app.schemas.stats import OrderStats, TopLocation, TopMenuItem


class StubLocationService:
    def list_locations(self, params: LocationQueryParams) -> list[Location]:
        return [
            Location(
                location_id="101",
                city=params.city or "Indianapolis",
                state=params.state or "IN",
                postal_code="46204",
                address_one="123 Main St",
                map_address="123 Main St, Indianapolis, IN 46204",
                phone="317-555-0101",
                email="store101@example.com",
                latitude=39.7684,
                longitude=-86.1581,
                near_by="Monument Circle",
                open_for_business=True,
                wifi=True,
                drive_thru=False,
                door_dash=True,
                full_address="123 Main St, Indianapolis, IN, 46204",
                store_name="Uncle Joe's Indianapolis",
                services=["wifi", "door_dash", "in_store"],
                pickup_supported=True,
            )
        ]

    def get_location(self, location_id: str) -> Location:
        return Location(
            location_id=location_id,
            city="Indianapolis",
            state="IN",
            postal_code="46204",
            address_one="123 Main St",
            map_address="123 Main St, Indianapolis, IN 46204",
            phone="317-555-0101",
            email="store101@example.com",
            latitude=39.7684,
            longitude=-86.1581,
            near_by="Monument Circle",
            open_for_business=True,
            wifi=True,
            drive_thru=False,
            door_dash=True,
            full_address="123 Main St, Indianapolis, IN, 46204",
            hours_today={"open": "07:00", "close": "20:00"},
            open_now=True,
            store_name="Uncle Joe's Indianapolis",
            services=["wifi", "door_dash", "in_store"],
            pickup_supported=True,
        )


class StubMenuService:
    def list_menu_items(self, params: MenuQueryParams) -> list[MenuItem]:
        return [
            MenuItem(
                item_id="latte",
                name="Latte",
                category=params.category or "Espresso",
                size="Medium",
                calories=190,
                price=4.5,
            )
        ]

    def get_menu_item(self, item_id: str) -> MenuItem:
        return MenuItem(
            item_id=item_id,
            name="Latte",
            category="Espresso",
            size="Medium",
            calories=190,
            price=4.5,
            ingredients=[],
            allergens=[],
            tags=["espresso", "medium", "under-200-calories"],
            customization_options=[],
            related_items=[],
            availability_status="available",
        )

    def list_categories(self) -> list[str]:
        return ["Coffee", "Tea"]

    def list_sizes(self) -> list[str]:
        return ["Small", "Medium", "Large"]

    def get_menu_item_stats(self, item_id: str, window_days: int | None = None) -> MenuItemStats:
        return MenuItemStats(
            item_id=item_id,
            total_orders=25,
            total_quantity=100,
            total_revenue=450.0,
            last_order_date="2026-04-12",
        )


class StubAuthService:
    def authenticate(self, email: str, password: str) -> dict:
        submitted_bytes = password.encode("utf-8")
        stored_hash = bcrypt.hashpw(b"Coffee123!", bcrypt.gensalt()).decode("utf-8")
        if email != "member@example.com" or not bcrypt.checkpw(
            submitted_bytes,
            stored_hash.encode("utf-8"),
        ):
            raise ValueError("Invalid credentials for stub.")
        return {
            "member_id": "member-1",
            "first_name": "Joe",
            "last_name": "Smith",
            "email": "member@example.com",
        }

    def login(self, email: str, password: str) -> LoginResponse:
        self.authenticate(email, password)
        return LoginResponse(
            authenticated=True,
            member_id="member-1",
            name="Joe Smith",
            email="member@example.com",
        )


class StubMemberService:
    def get_member(self, member_id: str) -> Member:
        return Member(
            member_id=member_id,
            first_name="Joe",
            last_name="Smith",
            email="member@example.com",
            phone_number="317-555-9999",
            home_store="101",
        )

    def get_member_identity(self, member_id: str) -> Member:
        return Member(
            member_id=member_id,
            first_name="Joe",
            last_name="Smith",
            email="member@example.com",
            phone_number="317-555-9999",
            home_store="101",
        )

    def get_points(self, member_id: str, points: int) -> MemberPoints:
        return MemberPoints(member_id=member_id, total_points=points)


class StubOrderService:
    def list_member_orders(self, member_id: str, params: OrderQueryParams) -> list[Order]:
        return [
            Order(
                order_id="order-1",
                member_id=member_id,
                store_id="101",
                order_total=12.5,
            )
        ]

    def calculate_points(self, member_id: str) -> int:
        return 12

    def list_location_orders(self, store_id: str, params: OrderQueryParams) -> list[Order]:
        return [
            Order(
                order_id="order-2",
                member_id="member-1",
                store_id=store_id,
                order_total=8.25,
            )
        ]

    def calculate_location_stats(self, store_id: str) -> dict:
        return {
            "store_id": store_id,
            "total_orders": 3,
            "total_revenue": 25.5,
            "avg_order_total": 8.5,
        }

    def list_location_daily_stats(self, store_id: str, limit: int) -> list[dict]:
        return [
            {
                "store_id": store_id,
                "order_date": "2026-04-12",
                "total_orders": 2,
                "total_revenue": 15.0,
            }
        ]

    def list_location_weekly_stats(self, store_id: str, limit: int) -> list[dict]:
        return [
            {
                "store_id": store_id,
                "week_start": "2026-04-07",
                "total_orders": 5,
                "total_revenue": 40.0,
            }
        ]

    def list_member_dashboard_orders(
        self,
        member_id: str,
        limit: int,
        offset: int,
        include_items: bool,
    ) -> list[DashboardOrder]:
        return [
            DashboardOrder(
                order_id="order-3",
                store_id="101",
                store_city="Indianapolis",
                store_state="IN",
                order_total=9.75,
                points_earned=9,
                items=[],
            )
        ]

    def count_member_orders(self, member_id: str) -> int:
        return 1

    def get_order_detail(self, order_id: str) -> OrderDetail:
        return OrderDetail(
            order_id=order_id,
            member_id="member-1",
            store_id="101",
            store_name="Uncle Joe's Indianapolis",
            store_city="Indianapolis",
            store_state="IN",
            subtotal=10.0,
            discount=0.0,
            tax=0.8,
            total=10.8,
            points_earned=10,
            points_redeemed=None,
            items=[],
            payment_summary={"subtotal": 10.0, "discount": 0.0, "tax": 0.8, "total": 10.8},
        )

    def list_member_favorites(
        self,
        member_id: str,
        limit: int,
        window_days: int | None = None,
    ) -> list[MemberFavoriteItem]:
        return [
            MemberFavoriteItem(
                menu_item_id="latte",
                item_name="Latte",
                total_orders=10,
                total_quantity=25,
                total_revenue=112.5,
            )
        ]

    def list_member_favorite_trends(
        self,
        member_id: str,
        limit_items: int,
        window_days: int,
    ) -> list[MemberFavoriteTrendPoint]:
        return [
            MemberFavoriteTrendPoint(
                menu_item_id="latte",
                item_name="Latte",
                week_start="2026-03-31",
                total_orders=3,
                total_quantity=8,
                total_revenue=36.0,
            )
        ]


class StubSearchService:
    def search(
        self,
        query: str,
        limit: int,
        scope: str,
        location_filters: dict | None = None,
        menu_filters: dict | None = None,
        fuzzy: bool = True,
        min_score: float = 0.0,
    ) -> SearchResponse:
        return SearchResponse(
            query=query,
            results=[
                SearchResult(kind="menu_item", id="latte", label="Latte"),
                SearchResult(kind="location", id="101", label="Indianapolis, IN"),
            ],
        )


class StubStatsService:
    def get_order_stats(self) -> OrderStats:
        return OrderStats(total_orders=100, total_revenue=1234.5, avg_order_total=12.34)

    def get_top_menu_items(self, limit: int) -> list[TopMenuItem]:
        return [
            TopMenuItem(
                menu_item_id="latte",
                item_name="Latte",
                total_quantity=250,
                total_revenue=1000.0,
            )
        ]

    def get_top_locations(self, limit: int) -> list[TopLocation]:
        return [
            TopLocation(
                store_id="101",
                city="Indianapolis",
                state="IN",
                total_orders=500,
                total_revenue=8000.0,
            )
        ]


class StubRecommendationsService:
    def get_recommendations(self, kind: str, limit: int, window_days: int | None):
        return [
            {
                "item_id": "latte",
                "item_name": "Latte",
                "total_quantity": 100,
                "total_revenue": 450.0,
                "kind": kind,
                "window_days": window_days,
            }
        ]


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_location_service] = lambda: StubLocationService()
    app.dependency_overrides[get_menu_service] = lambda: StubMenuService()
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
    app.dependency_overrides[get_member_service] = lambda: StubMemberService()
    app.dependency_overrides[get_order_service] = lambda: StubOrderService()
    app.dependency_overrides[get_search_service] = lambda: StubSearchService()
    app.dependency_overrides[get_stats_service] = lambda: StubStatsService()
    app.dependency_overrides[get_recommendations_service] = lambda: StubRecommendationsService()
    app.dependency_overrides[get_current_member] = lambda: Member(
        member_id="member-1",
        first_name="Joe",
        last_name="Smith",
        email="member@example.com",
    )
    return TestClient(app)


def test_docs_endpoint_available() -> None:
    client = build_test_client()
    response = client.get("/docs")
    assert response.status_code == 200


def test_cors_preflight_for_frontend_origin() -> None:
    client = build_test_client()
    response = client.options(
        "/menu",
        headers={
            "Origin": "https://uncle-joes-frontend-129124698283.us-central1.run.app",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://uncle-joes-frontend-129124698283.us-central1.run.app"
    )


def test_cors_preflight_for_local_dev_origin() -> None:
    client = build_test_client()
    response = client.options(
        "/locations",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_preflight_for_authenticated_routes() -> None:
    client = build_test_client()
    for path in [
        "/api/member/login",
        "/api/member/logout",
        "/api/member/session",
        "/api/member/profile",
        "/api/member/dashboard",
        "/orders/order-1",
    ]:
        response = client.options(
            path,
            headers={
                "Origin": "https://uncle-joes-frontend-129124698283.us-central1.run.app",
                "Access-Control-Request-Method": "POST" if path.endswith("login") or path.endswith("logout") else "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["access-control-allow-origin"]
            == "https://uncle-joes-frontend-129124698283.us-central1.run.app"
        )


def test_list_locations_supports_filters() -> None:
    client = build_test_client()
    response = client.get("/locations", params={"state": "IN", "city": "Indianapolis"})
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["state"] == "IN"
    assert payload[0]["city"] == "Indianapolis"


def test_get_menu_item() -> None:
    client = build_test_client()
    response = client.get("/menu/latte")
    assert response.status_code == 200
    assert response.json()["item_id"] == "latte"
    assert "related_items" in response.json()


def test_login_endpoint() -> None:
    client = build_test_client()
    response = client.post(
        "/login",
        json={"email": "member@example.com", "password": "Coffee123!"},
    )
    assert response.status_code == 200
    assert response.json()["authenticated"] is True


def test_member_profile_endpoint() -> None:
    client = build_test_client()
    response = client.get("/members/member-1")
    assert response.status_code == 200
    assert response.json()["member_id"] == "member-1"
    assert "rewards_tier" in response.json()


def test_member_orders_endpoint() -> None:
    client = build_test_client()
    response = client.get("/members/member-1/orders")
    assert response.status_code == 200
    assert response.json()[0]["order_id"] == "order-1"


def test_member_points_endpoint() -> None:
    client = build_test_client()
    response = client.get("/members/member-1/points")
    assert response.status_code == 200
    assert response.json()["total_points"] == 12


def test_search_endpoint() -> None:
    client = build_test_client()
    response = client.get("/search", params={"query": "latte"})
    assert response.status_code == 200
    assert response.json()["results"][0]["kind"] == "menu_item"


def test_search_endpoint_supports_filters() -> None:
    client = build_test_client()
    response = client.get(
        "/search",
        params={
            "query": "latte",
            "menu_category": "Espresso",
            "fuzzy": True,
            "min_score": 1,
        },
    )
    assert response.status_code == 200


def test_location_orders_and_stats_endpoints() -> None:
    client = build_test_client()
    response = client.get("/locations/101")
    assert response.status_code == 200
    assert "store_name" in response.json()
    response = client.get("/locations/101/orders")
    assert response.status_code == 200
    assert response.json()[0]["order_id"] == "order-2"
    response = client.get("/locations/101/stats")
    assert response.status_code == 200
    assert response.json()["store_id"] == "101"
    response = client.get("/locations/101/stats/daily")
    assert response.status_code == 200
    response = client.get("/locations/101/stats/weekly")
    assert response.status_code == 200


def test_menu_recommendations_endpoint() -> None:
    client = build_test_client()
    response = client.get("/menu/recommendations")
    assert response.status_code == 200


def test_menu_enrichment_endpoints() -> None:
    client = build_test_client()
    response = client.get("/menu/categories")
    assert response.status_code == 200
    response = client.get("/menu/sizes")
    assert response.status_code == 200
    response = client.get("/menu/latte/stats")
    assert response.status_code == 200
    response = client.get("/menu/latte/stats", params={"window_days": 30})
    assert response.status_code == 200


def test_stats_endpoints() -> None:
    client = build_test_client()
    response = client.get("/stats/orders")
    assert response.status_code == 200
    response = client.get("/stats/top-items")
    assert response.status_code == 200
    response = client.get("/stats/top-locations")
    assert response.status_code == 200


def test_member_recent_and_favorites_endpoints() -> None:
    client = build_test_client()
    response = client.get("/members/member-1/recent")
    assert response.status_code == 200
    response = client.get("/members/member-1/favorites")
    assert response.status_code == 200
    response = client.get("/members/member-1/favorites", params={"window_days": 30})
    assert response.status_code == 200
    response = client.get("/members/member-1/favorites/trends")
    assert response.status_code == 200
    response = client.get("/members/member-1/summary")
    assert response.status_code == 200
    response = client.get("/members/member-1/summary", params={"favorites_window_days": 30})
    assert response.status_code == 200


def test_member_auth_session_endpoints() -> None:
    client = build_test_client()
    response = client.post(
        "/api/member/login",
        json={"email": "member@example.com", "password": "Coffee123!"},
    )
    assert response.status_code == 200
    response = client.get("/api/member/session")
    assert response.status_code == 200
    response = client.get("/api/member/profile")
    assert response.status_code == 200
    response = client.get("/api/member/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "pagination" in payload
    assert payload["orders"][0]["points_earned"] >= 0
    response = client.post("/api/member/logout")
    assert response.status_code == 200


def test_order_detail_endpoint() -> None:
    client = build_test_client()
    response = client.get("/orders/order-1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["order_id"] == "order-1"
    assert isinstance(payload["items"], list)
