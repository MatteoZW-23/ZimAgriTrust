from enum import Enum
from typing import List, Dict

class Role(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    AUDITOR = "auditor"
    SUPPORT = "support"
    AGENT = "agent"
    FARMER = "farmer"

# Role-Based Access Control (RBAC) mapping
PERMISSIONS: Dict[Role, List[str]] = {
    Role.SUPERADMIN: ["*"],
    Role.ADMIN: [
        "view_analytics",
        "manage_agents",
        "manage_listings",
        "override_disputes",
        "view_system_health"
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
        "buy_produce",
        "view_market_data"
    ]
}

def has_permission(role: Role, required_permission: str) -> bool:
    if role == Role.SUPERADMIN:
        return True
    return required_permission in PERMISSIONS.get(role, [])
