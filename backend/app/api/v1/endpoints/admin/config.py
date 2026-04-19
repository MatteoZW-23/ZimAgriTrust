from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.system_config import SystemConfig, ConfigGroup
from app.models.system_audit import SystemAudit
from app.schemas.admin import ConfigResponse, ConfigUpdate

router = APIRouter()

@router.get("", response_model=list[ConfigResponse])
def list_configs(
    db: Session = Depends(get_db),
    group: ConfigGroup = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Module 5: Fetch all platform configurations and feature toggles.
    """
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
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        # Create if not exists for flexibility during implementation? 
        # No, better to have a seed script, but for now we raise 404.
        raise HTTPException(status_code=404, detail=f"Configuration key '{key}' not found.")
        
    old_value = config.value
    config.value = payload.value
    config.is_active = payload.is_active
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="CONFIG_UPDATE",
        target_type="SYSTEM_CONFIG",
        target_id=None,
        note=f"Update {key} from {old_value} to {payload.value}",
        details={"key": key, "old": old_value, "new": payload.value}
    )
    db.add(audit)
    db.commit()
    db.refresh(config)
    return config
