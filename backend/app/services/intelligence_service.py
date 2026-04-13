from sqlalchemy.orm import Session
from datetime import datetime
from app.models.system_audit import SystemAudit

class IntelligenceService:
    def log_audit_event(self, db: Session, payload: dict):
        """
        PLATFORM GOVERNANCE: Logs a persistent, non-repudiable audit event.
        Used for monitoring location integrity, role changes, and escrow overrides.
        """
        try:
            event = SystemAudit(
                event_type=payload.get("type", "GENERAL_AUDIT"),
                user_id=payload.get("user_id"),
                severity=payload.get("severity", "INFO"),
                resource_type=payload.get("resource_type", "SYSTEM"),
                details=payload.get("details", ""),
                timestamp=datetime.utcnow()
            )
            db.add(event)
            db.commit()
            print(f"AUDIT LOG | {payload.get('type')} | Severity: {payload.get('severity')}")
        except Exception as e:
            # Fallback to standard logging to avoid stopping the primary transaction
            print(f"FAILED TO PERSIST AUDIT: {str(e)}")

intelligence_service = IntelligenceService()
