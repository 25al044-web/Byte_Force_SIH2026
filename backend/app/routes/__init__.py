from fastapi import APIRouter

from app.routes.blacklist import router as blacklist_router
from app.routes.health import router as health_router
from app.routes.screening import router as screening_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(screening_router, prefix="", tags=["screening"])
api_router.include_router(blacklist_router, prefix="", tags=["blacklist"])

__all__ = ["api_router"]
