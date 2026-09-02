from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.screening import router as screening_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(screening_router, prefix="", tags=["screening"])

__all__ = ["api_router"]
