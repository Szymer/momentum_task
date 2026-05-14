from fastapi import APIRouter

from app.api.v1.endpoints.books import router as books_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.readers import router as readers_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(books_router, tags=["books"])
api_router.include_router(readers_router, tags=["readers"])
api_router.include_router(health_router, tags=["health"])


