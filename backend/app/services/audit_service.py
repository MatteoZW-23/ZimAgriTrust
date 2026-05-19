import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Optional, Dict, List

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.audit_log import AuditLog

GENESIS_CHECKSUM = "0" * 64


def _get_chain_key() -> bytes:
    # Use a secret key for the HMAC. Fallback to SECRET_KEY if specific one not set.
    key = getattr(settings, "AUDIT_CHAIN_KEY", settings.SECRET_KEY)
    return key.encode("utf-8")


def _calculate_payload_hash(payload: Dict[str, Any]) -> str:
    # Deterministic JSON representation
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _calculate_checksum(prev_checksum: str, payload_hash: str) -> str:
    msg = f"{prev_checksum}|{payload_hash}".encode("utf-8")
    return hmac.new(_get_chain_key(), msg, hashlib.sha256).hexdigest()


def append_audit_log(
    db: Session,
    *,
    action: str,
    admin_id: Optional[int] = None,
    user_id: Optional[Any] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    details: Optional[Dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
) -> AuditLog:
    """
    Appends a new audit log entry with a tamper-proof checksum.
    """
    # Get the last log's checksum
    last_log = db.query(AuditLog).order_by(desc(AuditLog.id)).first()
    prev_checksum = last_log.checksum if last_log else GENESIS_CHECKSUM
    
    # Calculate payload hash from all fields except id, checksum, created_at
    payload = {
        "admin_id": admin_id,
        "user_id": str(user_id) if user_id else None,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "old_values": old_values,
        "new_values": new_values,
        "details": details,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "request_id": request_id,
        "status": status,
        "error_message": error_message,
    }
    
    p_hash = _calculate_payload_hash(payload)
    checksum = _calculate_checksum(prev_checksum, p_hash)
    
    log_entry = AuditLog(
        admin_id=admin_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        status=status,
        error_message=error_message,
        checksum=checksum
    )
    
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def verify_audit_chain(db: Session, limit: int = 1000) -> Dict[str, Any]:
    """
    Verifies the integrity of the audit log chain.
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).limit(limit).all()
    
    prev_checksum = GENESIS_CHECKSUM
    tampered_ids = []
    
    for log in logs:
        payload = {
            "admin_id": log.admin_id,
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "old_values": log.old_values,
            "new_values": log.new_values,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "request_id": log.request_id,
            "status": log.status,
            "error_message": log.error_message,
        }
        
        p_hash = _calculate_payload_hash(payload)
        expected_checksum = _calculate_checksum(prev_checksum, p_hash)
        
        if not hmac.compare_digest(log.checksum, expected_checksum):
            tampered_ids.append(log.id)
            # Break early or continue to find all? Continuing to find all.
            # But the chain is broken, so subsequent logs will also fail if we don't update prev_checksum correctly.
            # Usually, once the chain is broken, we can't easily verify the rest unless we assume the stored checksum is "correct" for the next link.
            prev_checksum = log.checksum # Assume current is "new" start of chain for next link? 
                                         # No, if it's tampered, it's tampered.
        else:
            prev_checksum = log.checksum
            
    return {
        "total_logs": len(logs),
        "verified_logs": len(logs) - len(tampered_ids),
        "tampered_logs": len(tampered_ids),
        "is_valid": len(tampered_ids) == 0,
        "tampered_ids": tampered_ids,
        "message": "Chain is intact" if len(tampered_ids) == 0 else f"Found {len(tampered_ids)} tampered logs"
    }
