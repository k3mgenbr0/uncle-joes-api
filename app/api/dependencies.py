from collections.abc import Iterator

from fastapi import Depends, Request
from google.cloud import bigquery

from app.core.auth import decode_session_token
from app.core.config import Settings, get_settings
from app.core.errors import UnauthorizedError
from app.db.bigquery import BigQueryRunner
from app.repositories.locations import LocationRepository
from app.repositories.members import MemberRepository
from app.repositories.menu import MenuRepository
from app.repositories.orders import OrderRepository
from app.repositories.search import SearchRepository
from app.repositories.stats import StatsRepository
from app.services.auth import AuthService
from app.services.locations import LocationService
from app.services.members import MemberService
from app.schemas.member import Member
from app.services.menu import MenuService
from app.services.orders import OrderService
from app.services.recommendations import RecommendationsService
from app.services.search import SearchService
from app.services.stats import StatsService


def get_bigquery_client(
    settings: Settings = Depends(get_settings),
) -> Iterator[bigquery.Client]:
    client = bigquery.Client(project=settings.bigquery_project_id)
    try:
        yield client
    finally:
        client.close()


def get_bigquery_runner(
    client: bigquery.Client = Depends(get_bigquery_client),
) -> BigQueryRunner:
    return BigQueryRunner(client)


def get_location_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> LocationRepository:
    return LocationRepository(runner=runner, settings=settings)


def get_menu_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> MenuRepository:
    return MenuRepository(runner=runner, settings=settings)


def get_member_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> MemberRepository:
    return MemberRepository(runner=runner, settings=settings)


def get_order_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> OrderRepository:
    return OrderRepository(runner=runner, settings=settings)


def get_search_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> SearchRepository:
    return SearchRepository(runner=runner, settings=settings)


def get_stats_repository(
    runner: BigQueryRunner = Depends(get_bigquery_runner),
    settings: Settings = Depends(get_settings),
) -> StatsRepository:
    return StatsRepository(runner=runner, settings=settings)


def get_location_service(
    repository: LocationRepository = Depends(get_location_repository),
) -> LocationService:
    return LocationService(repository)


def get_menu_service(
    repository: MenuRepository = Depends(get_menu_repository),
) -> MenuService:
    return MenuService(repository)


def get_member_service(
    repository: MemberRepository = Depends(get_member_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    location_repository: LocationRepository = Depends(get_location_repository),
) -> MemberService:
    return MemberService(repository, order_repository, location_repository)


def get_order_service(
    repository: OrderRepository = Depends(get_order_repository),
) -> OrderService:
    return OrderService(repository)


def get_auth_service(
    repository: MemberRepository = Depends(get_member_repository),
) -> AuthService:
    return AuthService(repository)


def get_current_member(
    request: Request,
    settings: Settings = Depends(get_settings),
    member_service: MemberService = Depends(get_member_service),
) -> Member:
    token = request.cookies.get(settings.auth_cookie_name)
    payload = decode_session_token(token, settings.auth_secret_key) if token else None
    if not payload:
        raise UnauthorizedError("Authentication required.")
    member_id = payload.get("member_id")
    if not member_id:
        raise UnauthorizedError("Authentication required.")
    return member_service.get_member_identity(str(member_id))


def get_search_service(
    repository: SearchRepository = Depends(get_search_repository),
) -> SearchService:
    return SearchService(repository)


def get_stats_service(
    repository: StatsRepository = Depends(get_stats_repository),
) -> StatsService:
    return StatsService(repository)


def get_recommendations_service(
    repository: StatsRepository = Depends(get_stats_repository),
) -> RecommendationsService:
    return RecommendationsService(repository)
