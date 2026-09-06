from fastapi import APIRouter

from app.routes.blacklist import router as blacklist_router
from app.routes.demo import router as demo_router
from app.routes.health import router as health_router
from app.routes.screening import router as screening_router
from app.routes.audit import router as audit_router
from app.routes.cases import router as cases_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="", tags=["health"])
api_router.include_router(screening_router, prefix="", tags=["screening"])
api_router.include_router(audit_router, prefix="", tags=["audit"])
api_router.include_router(cases_router, prefix="", tags=["cases"])
api_router.include_router(blacklist_router, prefix="", tags=["blacklist"])
api_router.include_router(demo_router, prefix="", tags=["demo"])

__all__ = ["api_router"]
