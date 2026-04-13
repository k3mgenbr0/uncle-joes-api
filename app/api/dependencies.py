from collections.abc import Iterator

from fastapi import Depends
from google.cloud import bigquery

from app.core.config import Settings, get_settings
from app.db.bigquery import BigQueryRunner
from app.repositories.locations import LocationRepository
from app.repositories.menu import MenuRepository
from app.services.locations import LocationService
from app.services.menu import MenuService


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


def get_location_service(
    repository: LocationRepository = Depends(get_location_repository),
) -> LocationService:
    return LocationService(repository)


def get_menu_service(
    repository: MenuRepository = Depends(get_menu_repository),
) -> MenuService:
    return MenuService(repository)
