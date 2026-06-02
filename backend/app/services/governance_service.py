import uuid
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.governance import (
    ConsentType,
    GovernancePolicy,
    PolicyStatus,
    PrivacyRequest,
    PrivacyRequestType,
    UserCommunicationPreference,
    UserConsentRecord,
)
from app.models.user import User
from app.models.audit_log import AuditLog


class GovernanceService:
    POLICY_REQUIREMENTS = {
        "registration_farmer": ["terms_of_service", "privacy_policy"],
        "registration_buyer": ["terms_of_service", "privacy_policy"],
        "transaction_first": ["escrow_policy", "wallet_payments_policy", "dispute_resolution_policy"],
        "supplier_activation": ["supplier_policy", "acceptable_use_policy", "escrow_policy", "wallet_payments_policy"],
        "agent_academy_access": ["terms_of_service", "privacy_policy"],
        "agent_certification": ["agent_code_of_conduct", "dispute_resolution_policy", "security_policy"],
        "driver_activation": ["delivery_logistics_policy", "acceptable_use_policy", "security_policy"],
        "admin_access": ["administrative_conduct_policy", "confidentiality_agreement", "data_access_policy", "security_policy"],
        "super_admin_access": ["super_admin_conduct_policy", "infrastructure_security_policy", "confidentiality_agreement", "data_governance_policy"],
    }

    @staticmethod
    def get_policies(db: Session, active_only: bool = True):
        q = db.query(GovernancePolicy)
        if active_only:
            q = q.filter(GovernancePolicy.active == True, GovernancePolicy.status == PolicyStatus.PUBLISHED)
        return q.all()

    @staticmethod
    def create_or_update_policy(db: Session, user: User, payload: dict):
        key = payload.get("key")
        if not key:
            raise HTTPException(status_code=400, detail="Policy key is required")
        required_fields = ["category", "title", "content"]
        missing = [field for field in required_fields if payload.get(field) in (None, "")]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required policy fields: {', '.join(missing)}",
            )
        policy_payload = {k: v for k, v in payload.items() if k != "key"}
        policy = db.query(GovernancePolicy).filter(GovernancePolicy.key == key).first()
        if not policy:
            policy = GovernancePolicy(key=key, author_id=user.id, **policy_payload)
            db.add(policy)
        else:
            for k, v in policy_payload.items():
                setattr(policy, k, v)
        GovernanceService._audit(db, user.id, "POLICY_UPSERT", "POLICY", str(policy.id if policy.id else key))
        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def publish_policy(db: Session, user: User, key: str):
        policy = db.query(GovernancePolicy).filter(GovernancePolicy.key == key).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        policy.status = PolicyStatus.PUBLISHED
        policy.active = True
        policy.published_at = datetime.now(timezone.utc)
        policy.approver_id = user.id
        GovernanceService._audit(db, user.id, "POLICY_PUBLISHED", "POLICY", str(policy.id))
        db.commit()
        return policy

    @staticmethod
    def upsert_consent(
        db: Session,
        user: User,
        consent_type: ConsentType,
        policy_version: str,
        accepted: bool,
        ip_address: Optional[str],
        device: Optional[str],
        method: Optional[str],
        platform: Optional[str],
    ):
        digest = hashlib.sha256(
            f"{user.id}:{consent_type.value}:{policy_version}:{accepted}:{ip_address}:{device}:{platform}".encode()
        ).hexdigest()
        rec = UserConsentRecord(
            user_id=user.id,
            consent_type=consent_type,
            policy_version=policy_version,
            accepted=accepted,
            ip_address=ip_address,
            device=device,
            acceptance_method=method,
            platform=platform,
            immutable_hash=digest,
        )
        db.add(rec)
        GovernanceService._audit(db, user.id, "CONSENT_RECORDED", "CONSENT", str(rec.id))
        db.commit()
        db.refresh(rec)
        return rec

    @staticmethod
    def get_consents(db: Session, user: User):
        return db.query(UserConsentRecord).filter(UserConsentRecord.user_id == user.id).all()

    @staticmethod
    def get_or_create_preferences(db: Session, user: User):
        pref = db.query(UserCommunicationPreference).filter(UserCommunicationPreference.user_id == user.id).first()
        if not pref:
            pref = UserCommunicationPreference(user_id=user.id)
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(db: Session, user: User, payload: dict):
        pref = GovernanceService.get_or_create_preferences(db, user)
        for field, value in payload.items():
            if hasattr(pref, field):
                setattr(pref, field, bool(value))
        GovernanceService._audit(db, user.id, "COMM_PREF_UPDATED", "COMMUNICATION", str(pref.id))
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def submit_privacy_request(db: Session, user: User, request_type: PrivacyRequestType, reason: Optional[str]):
        req = PrivacyRequest(user_id=user.id, request_type=request_type, reason=reason)
        db.add(req)
        GovernanceService._audit(db, user.id, "PRIVACY_REQUEST_SUBMITTED", "PRIVACY_REQUEST", str(req.id))
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def enforce_requirements(db: Session, user: User, requirement_key: str):
        policy_keys = GovernanceService.POLICY_REQUIREMENTS.get(requirement_key, [])
        if not policy_keys:
            return True
        accepted_versions = {
            (c.consent_type.value, c.policy_version)
            for c in db.query(UserConsentRecord).filter(UserConsentRecord.user_id == user.id, UserConsentRecord.accepted == True).all()
        }
        required = db.query(GovernancePolicy).filter(
            GovernancePolicy.key.in_(policy_keys),
            GovernancePolicy.status == PolicyStatus.PUBLISHED,
            GovernancePolicy.active == True
        ).all()
        missing = []
        for p in required:
            if (p.key, p.version) not in accepted_versions:
                missing.append({"policy": p.key, "version": p.version})
        if missing:
            raise HTTPException(status_code=403, detail={"code": "POLICY_ACCEPTANCE_REQUIRED", "missing": missing})
        return True

    @staticmethod
    def _audit(db: Session, user_id, action: str, entity_type: str, entity_id: str):
        db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                status="success",
                checksum="governance",
            )
        )


governance_service = GovernanceService()
