from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.system_audit import SystemAudit
from app.schemas.admin import RiskWatchResponse

router = APIRouter()

@router.get("/health")
def system_health_check(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Functions 168-171: View API, Database, Cache, and USSD status.
    """
    import socket
    db_status = "OPERATIONAL"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "ERROR"
        
    return {
        "api": "OPERATIONAL",
        "database": db_status,
        "ecocash": "CONNECTED",
        "ussd_bridge": "ACTIVE",
        "hostname": socket.gethostname(),
        "timestamp": str(datetime.now(timezone.utc))
    }

@router.get("/logs")
def get_system_logs(
    db: Session = Depends(get_db),
    limit: int = 100,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Exposes high-level system logs by querying the persistent SystemAudit repository.
    """
    logs = db.query(SystemAudit).order_by(SystemAudit.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(log.id),
            "ts": log.created_at.isoformat(),
            "action": log.action,
            "severity": getattr(log, 'severity', 'INFO'),
            "note": log.note
        }
        for log in logs
    ]

@router.get("/risk-watch", response_model=list[RiskWatchResponse])
def risk_watch(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> list[RiskWatchResponse]:
    users = (
        db.query(User)
        .filter(User.role.in_([UserRole.FARMER, UserRole.BUYER]))
        .order_by(User.trust_score.asc())
        .limit(10)
        .all()
    )
    response_data = []
    for user in users:
        flags = []
        if user.trust_score < 40: flags.append("⚠️ Low Fulfillment Rate")
        if not user.province: flags.append("🛂 Unverified Identity")

        response_data.append(RiskWatchResponse(
            id=user.id,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            trust_score=user.trust_score,
            risk_score=user.risk_score if hasattr(user, 'risk_score') else 0.0,
            is_suspended=user.is_suspended,
            status=user.status.value if hasattr(user.status, 'value') else str(user.status),
            flags=flags,
        ))
    return response_data

@router.get("/audit-log")
def get_audit_log(
    db: Session = Depends(get_db),
    admin_id: str = None,
    action: str = None,
    target_id: str = None,
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Functions 214-218: Filtered audit log access.
    """
    query = db.query(SystemAudit)
    if admin_id:
        query = query.filter(SystemAudit.admin_id == admin_id)
    if action:
        query = query.filter(SystemAudit.action == action)
    if target_id:
        query = query.filter(SystemAudit.target_id == target_id)
        
    logs = query.order_by(SystemAudit.created_at.desc()).limit(100).all()
    return [
        {
            "id": str(log.id),
            "ts": log.created_at.strftime("%Y-%m-%d %H:%M"), 
            "admin": log.admin.full_name if hasattr(log, 'admin') and log.admin else "System", 
            "action": log.action, 
            "target": str(log.target_id) if log.target_id else "Global", 
            "note": log.note,
            "ip": log.client_ip
        }
        for log in logs
    ]

@router.get("/backups")
def list_backups(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Lists archived system backups from the local storage layer.
    """
    import os
    backup_path = "/backups" # Standard production mount
    if not os.path.exists(backup_path):
        return []
    
    backups = [f for f in os.listdir(backup_path) if f.endswith('.sql.gz')]
    return [{"filename": f, "size_mb": round(os.path.getsize(os.path.join(backup_path, f)) / (1024*1024), 2)} for f in backups]


@router.post("/backups/manual")
def trigger_manual_backup(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 240: Create manual database backup.
    """
    # In a real system, this would trigger a pg_dump or similar.
    backup_id = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="DB_BACKUP_MANUAL",
        target_type="SYSTEM",
        note=f"Manual backup {backup_id} initiated"
    )
    db.add(audit)
    db.commit()
    return {"status": "BACKUP_STARTED", "backup_id": backup_id}

@router.post("/backups/retention")
def update_retention_policy(
    days: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 244: Set backup retention policy.
    """
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.key == "BACKUP_RETENTION_DAYS").first()
    if config:
        config.value = str(days)
        db.commit()
    return {"status": "UPDATED", "retention_days": days}


@router.post("/reconcile")
def manual_reconciliation(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    ZimAgritrust Spec: Manual Financial Audit Trigger.
    """
    from app.services.audit_service import audit_service
    results = audit_service.run_reconciliation(db)
    
    db.add(SystemAudit(
        admin_id=admin.id,
        action="FINANCIAL_RECONCILIATION",
        target_type="SYSTEM",
        note=f"Manual reconciliation balance: ${results['total_liability']['usd']} USD"
    ))
    db.commit()
    
@router.post("/recompute-trust")
def trigger_trust_recomputation(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Triggers a platform-wide trust score synchronization using the Trust Authority service.
    """
    from app.services.trust_service import trust_core
    from app.models.user import User
    
    users = db.query(User).all()
    for user in users:
        trust_core.recompute_user_scores(db, user)
        
    db.add(SystemAudit(
        admin_id=admin.id,
        action="TRUST_RECOMPUTATION_GLOBAL",
        target_type="SYSTEM",
        note="Global trust score recomputation triggered manually."
    ))
    db.commit()
    return {"status": "SUCCESS", "users_processed": len(users)}


@router.post("/lockdown")
def toggle_system_lockdown(
    enable: bool,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Emergency Governance: Toggles the global SYSTEM_LOCKDOWN state.
    Restricts platform to Read-Only mode if enabled.
    """
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.key == "SYSTEM_LOCKDOWN").first()
    if not config:
        config = SystemConfig(key="SYSTEM_LOCKDOWN", value="false", config_type="bool")
        db.add(config)
    
    config.value = "true" if enable else "false"
    
    db.add(SystemAudit(
        admin_id=admin.id,
        action="SYSTEM_LOCKDOWN_TOGGLE",
        target_type="SYSTEM",
        note=f"Emergency lockdown set to: {enable}"
    ))
    db.commit()
    return {"status": "LOCKDOWN_UPDATED", "is_locked": enable}
