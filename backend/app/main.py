"""Commerce Engine FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException

from app.businesses.router import router as businesses_router
from app.catalog.router import router as catalog_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.identity.router import router as auth_router
from app.identity.router import users_router
from app.locations.router import router as locations_router
from app.tenants.router import router as tenants_router

# Import models so metadata is registered for Alembic / create_all.
import app.businesses.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.identity.models  # noqa: F401
import app.locations.models  # noqa: F401
import app.tenants.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(businesses_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/meta")
async def meta() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }
