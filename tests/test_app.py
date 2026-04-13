from fastapi.testclient import TestClient

from app.api.dependencies import get_location_service, get_menu_service
from app.main import create_app
from app.schemas.location import Location, LocationQueryParams
from app.schemas.menu import MenuItem, MenuQueryParams


class StubLocationService:
    def list_locations(self, params: LocationQueryParams) -> list[Location]:
        return [
            Location(
                location_id="101",
                name="Downtown",
                address="123 Main St",
                city=params.city or "Indianapolis",
                state=params.state or "IN",
                postal_code="46204",
                phone="317-555-0101",
                hours="6am-6pm",
            )
        ]

    def get_location(self, location_id: str) -> Location:
        return Location(
            location_id=location_id,
            name="Downtown",
            address="123 Main St",
            city="Indianapolis",
            state="IN",
            postal_code="46204",
            phone="317-555-0101",
            hours="6am-6pm",
        )


class StubMenuService:
    def list_menu_items(self, params: MenuQueryParams) -> list[MenuItem]:
        return [
            MenuItem(
                item_id="latte",
                name="Latte",
                category=params.category or "Espresso",
                description="Espresso with steamed milk",
                price=4.5,
                currency="USD",
                is_available=True,
            )
        ]

    def get_menu_item(self, item_id: str) -> MenuItem:
        return MenuItem(
            item_id=item_id,
            name="Latte",
            category="Espresso",
            description="Espresso with steamed milk",
            price=4.5,
            currency="USD",
            is_available=True,
        )


def build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_location_service] = lambda: StubLocationService()
    app.dependency_overrides[get_menu_service] = lambda: StubMenuService()
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
