"""Import all ORM models so SQLAlchemy metadata is complete.

Scripts and Alembic need this before flushing rows with foreign keys.
"""

from __future__ import annotations

import app.businesses.models  # noqa: F401
import app.cart.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.delivery.models  # noqa: F401
import app.fulfillment.models  # noqa: F401
import app.identity.models  # noqa: F401
import app.integrations.ondc.models  # noqa: F401
import app.inventory.models  # noqa: F401
import app.ledger.models  # noqa: F401
import app.locations.models  # noqa: F401
import app.notifications.models  # noqa: F401
import app.orders.models  # noqa: F401
import app.partners.models  # noqa: F401
import app.payments.models  # noqa: F401
import app.settlements.models  # noqa: F401
import app.taxation.models  # noqa: F401
import app.tenants.models  # noqa: F401
