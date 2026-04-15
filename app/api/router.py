from fastapi import APIRouter

from app.api.routes import auth, health, locations, member_auth, members, menu, orders, search, stats


api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(member_auth.router)
api_router.include_router(health.router)
api_router.include_router(locations.router)
api_router.include_router(members.router)
api_router.include_router(menu.router)
api_router.include_router(orders.router)
api_router.include_router(search.router)
api_router.include_router(stats.router)
