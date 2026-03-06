from fastapi import APIRouter

from app.api.v2.endpoints import items, users

api_router_v2 = APIRouter()
api_router_v2.include_router(users.router, prefix="/users", tags=["users-v2"])
api_router_v2.include_router(items.router, prefix="/items", tags=["items-v2"])
