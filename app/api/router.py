from fastapi import APIRouter

from app.api.routes import health, locations, menu


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(locations.router)
api_router.include_router(menu.router)
