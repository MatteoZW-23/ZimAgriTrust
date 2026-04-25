from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.system_config import SystemConfig, ConfigGroup
from app.models.system_audit import SystemAudit
from app.schemas.admin import ConfigResponse, ConfigUpdate

router = APIRouter()

# Default config definitions — used for upsert on first write
_CONFIG_DEFAULTS: dict[str, dict] = {
    # Feature toggles
    "ai_grading_enabled":       {"value": "false", "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Enable AI-powered crop grading"},
    "fraud_detection_enabled":  {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Enable real-time fraud detection"},
    "auto_agent_assignment":    {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Automatically assign nearest agent to orders"},
    "usd_secondary_market":     {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Allow USD secondary market trading"},
    "zig_settlement":           {"value": "false", "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Enable ZiG currency settlement"},
    "whatsapp_notifications":   {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Send WhatsApp notifications"},
    "sms_notifications":        {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Send SMS notifications"},
    "ussd_enabled":             {"value": "true",  "group": ConfigGroup.FEATURES, "config_type": "bool", "description": "Enable USSD interface"},
    # Finance
    "platform_fee_pct":         {"value": "2.5",   "group": ConfigGroup.FINANCE,  "config_type": "float", "description": "Platform transaction fee percentage"},
    "escrow_hold_hours":        {"value": "48",    "group": ConfigGroup.FINANCE,  "config_type": "int",   "description": "Hours escrow is held after delivery"},
    "min_withdrawal_usd":       {"value": "5.0",   "group": ConfigGroup.FINANCE,  "config_type": "float", "description": "Minimum withdrawal amount in USD"},
    # Risk
    "max_daily_transactions":   {"value": "50",    "group": ConfigGroup.RISK,     "config_type": "int",   "description": "Max transactions per user per day"},
    "trust_score_threshold":    {"value": "60",    "group": ConfigGroup.RISK,     "config_type": "int",   "description": "Minimum trust score to transact"},
    # System
    "SYSTEM_LOCKDOWN":          {"value": "false", "group": ConfigGroup.GENERAL,  "config_type": "bool",  "description": "Platform-wide lockdown mode"},
    "BACKUP_RETENTION_DAYS":    {"value": "30",    "group": ConfigGroup.GENERAL,  "config_type": "int",   "description": "Number of days to retain backups"},
}


@router.get("", response_model=list[ConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    group: ConfigGroup = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Module 5: Fetch all platform configurations and feature toggles.
    Returns seeded defaults merged with any DB overrides.
    """
    # Ensure all known defaults exist in DB
    _ensure_defaults(db)

    query = db.query(SystemConfig)
    if group:
        query = query.filter(SystemConfig.group == group)
    return query.all()


@router.patch("/{key}", response_model=ConfigResponse)
def update_config(
    key: str,
    payload: ConfigUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Module 5.1: Update dynamic platform settings (Currency, Escrow, etc.)
    Module 5.2: Manage Feature Toggles.
    Creates the config key if it doesn't exist yet (upsert).
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if not config:
        # Upsert: create from defaults or as a generic string config
        defaults = _CONFIG_DEFAULTS.get(key, {})
        config = SystemConfig(
            key=key,
            value=payload.value,
            is_active=payload.is_active,
            group=defaults.get("group", ConfigGroup.GENERAL),
            config_type=defaults.get("config_type", "string"),
            description=defaults.get("description"),
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    old_value = config.value
    config.value = payload.value
    config.is_active = payload.is_active

    audit = SystemAudit(
        admin_id=admin.id,
        action="CONFIG_UPDATE",
        target_type="SYSTEM_CONFIG",
        target_id=None,
        note=f"Update {key} from {old_value} to {payload.value}",
        details={"key": key, "old": old_value, "new": payload.value},
    )
    db.add(audit)
    db.commit()
    db.refresh(config)
    return config


def _ensure_defaults(db: Session):
    """Insert any missing default config keys into the DB."""
    existing_keys = {row.key for row in db.query(SystemConfig.key).all()}
    new_rows = []
    for key, meta in _CONFIG_DEFAULTS.items():
        if key not in existing_keys:
            new_rows.append(SystemConfig(
                key=key,
                value=meta["value"],
                group=meta["group"],
                config_type=meta["config_type"],
                description=meta.get("description"),
                is_active=True,
            ))
    if new_rows:
        db.add_all(new_rows)
        db.commit()
