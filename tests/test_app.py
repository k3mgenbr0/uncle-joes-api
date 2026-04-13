import bcrypt
from fastapi.testclient import TestClient

from app.api.dependencies import get_auth_service, get_location_service, get_menu_service
from app.main import create_app
from app.schemas.auth import LoginResponse
from app.schemas.location import Location, LocationQueryParams
from app.schemas.menu import MenuItem, MenuQueryParams


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


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_location_service] = lambda: StubLocationService()
    app.dependency_overrides[get_menu_service] = lambda: StubMenuService()
    app.dependency_overrides[get_auth_service] = lambda: StubAuthService()
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
