from fastapi import APIRouter

from app.api.routes import auth, health, locations, members, menu, search, stats


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(health.router)
api_router.include_router(locations.router)
api_router.include_router(members.router)
api_router.include_router(menu.router)
api_router.include_router(search.router)
api_router.include_router(stats.router)
