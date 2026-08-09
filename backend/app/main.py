"""Commerce Engine FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.businesses.router import router as businesses_router
from app.cart.router import router as cart_router
from app.catalog.router import router as catalog_router
from app.core.config import cors_origin_list, get_settings
from app.core.errors import AppError, app_error_handler, http_error_handler
from app.courier.router import router as courier_router
from app.delivery.router import router as delivery_router
from app.fulfillment.router import router as fulfillment_router
from app.identity.router import router as auth_router
from app.identity.router import users_router
from app.inventory.router import router as inventory_router
from app.ledger.router import router as ledger_router
from app.locations.router import router as locations_router
from app.orders.router import router as orders_router
from app.partners.router import router as partners_router
from app.payments.router import router as payments_router
from app.pricing.router import router as pricing_router
from app.settlements.router import router as settlements_router
from app.taxation.router import router as tax_router
from app.tenants.router import router as tenants_router
from app.integrations.ondc.handlers import register_ondc_handlers
from app.integrations.ondc.router import router as ondc_router
from app.delivery.handlers import register_dispatch_handlers
from app.notifications.handlers import register_notification_handlers
from app.notifications.router import router as notifications_router

# Import models so metadata is registered for Alembic / create_all.
import app.businesses.models  # noqa: F401
import app.cart.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.delivery.models  # noqa: F401
import app.fulfillment.models  # noqa: F401
import app.identity.models  # noqa: F401
import app.inventory.models  # noqa: F401
import app.ledger.models  # noqa: F401
import app.locations.models  # noqa: F401
import app.orders.models  # noqa: F401
import app.partners.models  # noqa: F401
import app.payments.models  # noqa: F401
import app.settlements.models  # noqa: F401
import app.taxation.models  # noqa: F401
import app.tenants.models  # noqa: F401
import app.integrations.ondc.models  # noqa: F401
import app.notifications.models  # noqa: F401

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origin_list(settings),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(businesses_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(cart_router, prefix="/api/v1")
app.include_router(pricing_router, prefix="/api/v1")
app.include_router(tax_router, prefix="/api/v1")
app.include_router(orders_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(ledger_router, prefix="/api/v1")
app.include_router(settlements_router, prefix="/api/v1")
app.include_router(fulfillment_router, prefix="/api/v1")
app.include_router(partners_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(courier_router, prefix="/api/v1")
app.include_router(ondc_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")

register_ondc_handlers()
register_notification_handlers()
register_dispatch_handlers()


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
