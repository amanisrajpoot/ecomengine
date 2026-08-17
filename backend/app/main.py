"""Commerce Engine FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.identity import service as identity_service
from app.identity.router import router as auth_router
from app.identity.router import users_router
from app.businesses.router import router as businesses_router
from app.locations.router import router as locations_router
from app.catalog.router import router as catalog_router
from app.inventory.router import router as inventory_router
from app.cart.router import router as carts_router
from app.taxation.router import router as taxation_router
from app.orders.router import router as orders_router
from app.payments.router import router as payments_router
from app.ledger.router import router as ledger_router
from app.settlements.router import router as settlements_router
from app.tenants.router import platform_router
from app.tenants.router import router as tenants_router

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with SessionLocal() as db:
        await identity_service.create_bootstrap_super_admin(
            db,
            email=settings.bootstrap_super_admin_email,
            password=settings.bootstrap_super_admin_password,
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


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


for r in (auth_router, users_router, tenants_router, platform_router, businesses_router, locations_router, catalog_router, inventory_router, carts_router, taxation_router, orders_router, payments_router, ledger_router, settlements_router):
    app.include_router(r, prefix="/api/v1")
