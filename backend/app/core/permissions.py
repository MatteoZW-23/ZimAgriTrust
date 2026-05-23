from enum import Enum
from typing import List, Dict

class Role(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    AUDITOR = "auditor"
    SUPPORT = "support"
    AGENT = "agent"
    FARMER = "farmer"
    BUYER = "buyer"
    DRIVER = "driver"

# Role-Based Access Control (RBAC) mapping
PERMISSIONS: Dict[Role, List[str]] = {
    Role.SUPERADMIN: ["*"],
    Role.ADMIN: [
        "view_analytics",
        "manage_agents",
        "manage_listings",
        "override_disputes",
        "view_system_health",
        "manage_users"
    ],
    Role.AUDITOR: [
        "view_audit_logs",
        "view_transactions",
        "view_model_performance"
    ],
    Role.SUPPORT: [
        "view_help_tickets",
        "message_users",
        "view_user_profiles"
    ],
    Role.AGENT: [
        "verify_crops",
        "manage_assigned_disputes",
        "view_training"
    ],
    Role.FARMER: [
        "create_listing",
        "manage_listings",
        "view_market_data",
        "respond_to_offers",
        "manage_wallet"
    ],
    Role.BUYER: [
        "browse_marketplace",
        "make_offers",
        "view_orders",
        "manage_wallet",
        "rate_sellers"
    ],
    Role.DRIVER: [
        "view_delivery_jobs",
        "accept_delivery_jobs",
        "update_delivery_status",
        "view_earnings",
        "manage_vehicle_info"
    ]
}

def has_permission(role: Role, required_permission: str) -> bool:
    if role == Role.SUPERADMIN:
        return True
    return required_permission in PERMISSIONS.get(role, [])
