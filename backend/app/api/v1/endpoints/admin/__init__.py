from fastapi import APIRouter
from . import (
    overview,
    users,
    agents,
    transactions,
    listings,
    analytics,
    system,
    disputes,
    config,
    ai,
    notifications,
    permissions,
    academy,
    scraping,
    command_center,
)

router = APIRouter()

router.include_router(overview.router, tags=["admin-overview"])
router.include_router(users.router, prefix="/users", tags=["admin-users"])
router.include_router(agents.router, prefix="/agents", tags=["admin-agents"])
router.include_router(academy.router, prefix="/academy", tags=["admin-academy"])
router.include_router(transactions.router, prefix="/transactions", tags=["admin-transactions"])
router.include_router(listings.router, prefix="/listings", tags=["admin-listings"])
router.include_router(analytics.router, prefix="/analytics", tags=["admin-analytics"])
router.include_router(system.router, prefix="/system", tags=["admin-system"])
router.include_router(disputes.router, prefix="/disputes", tags=["admin-disputes"])
router.include_router(config.router, prefix="/config", tags=["admin-config"])
router.include_router(ai.router, prefix="/ai", tags=["admin-ai"])
router.include_router(notifications.router, prefix="/notifications", tags=["admin-notifications"])
router.include_router(permissions.router, prefix="/permissions", tags=["admin-permissions"])
router.include_router(scraping.router, prefix="/scraping", tags=["admin-scraping"])
router.include_router(command_center.router, prefix="/command-center", tags=["admin-command-center"])

