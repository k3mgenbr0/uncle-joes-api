import bcrypt
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_auth_service,
    get_location_service,
    get_member_service,
    get_menu_service,
    get_order_service,
    get_search_service,
    get_stats_service,
)
from app.main import create_app
from app.schemas.auth import LoginResponse
from app.schemas.location import Location, LocationQueryParams
from app.schemas.member import Member, MemberPoints
from app.schemas.menu import MenuItem, MenuQueryParams
from app.schemas.order import Order, OrderQueryParams
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
        )


class StubAuthService:
    def login(self, email: str, password: str) -> LoginResponse:
        submitted_bytes = password.encode("utf-8")
        stored_hash = bcrypt.hashpw(b"Coffee123!", bcrypt.gensalt()).decode("utf-8")
        if email != "member@example.com" or not bcrypt.checkpw(
            submitted_bytes,
            stored_hash.encode("utf-8"),
        ):
            raise ValueError("Invalid credentials for stub.")
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


class StubSearchService:
    def search(self, query: str, limit: int, scope: str) -> SearchResponse:
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


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_location_service] = lambda: StubLocationService()
    app.dependency_overrides[get_menu_service] = lambda: StubMenuService()
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
    app.dependency_overrides[get_member_service] = lambda: StubMemberService()
    app.dependency_overrides[get_order_service] = lambda: StubOrderService()
    app.dependency_overrides[get_search_service] = lambda: StubSearchService()
    app.dependency_overrides[get_stats_service] = lambda: StubStatsService()
    return TestClient(app)


def test_docs_endpoint_available() -> None:
    client = build_test_client()
    response = client.get("/docs")
    assert response.status_code == 200


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


def test_location_orders_and_stats_endpoints() -> None:
    client = build_test_client()
    response = client.get("/locations/101/orders")
    assert response.status_code == 200
    assert response.json()[0]["order_id"] == "order-2"
    response = client.get("/locations/101/stats")
    assert response.status_code == 200
    assert response.json()["store_id"] == "101"


def test_stats_endpoints() -> None:
    client = build_test_client()
    response = client.get("/stats/orders")
    assert response.status_code == 200
    response = client.get("/stats/top-items")
    assert response.status_code == 200
    response = client.get("/stats/top-locations")
    assert response.status_code == 200
