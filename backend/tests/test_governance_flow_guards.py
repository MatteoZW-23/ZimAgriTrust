import uuid

import pytest
from fastapi import HTTPException

from app.models.user import User, UserRole, UserStatus
from app.services.governance_service import GovernanceService


def _admin_user(db):
    user = User(
        full_name="Admin User",
        phone_number=f"+26379{uuid.uuid4().int % 10000000:07d}",
        password_hash="hash",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_policy_upsert_requires_key(db):
    user = _admin_user(db)
    with pytest.raises(HTTPException) as exc:
        GovernanceService.create_or_update_policy(
            db,
            user,
            {"category": "legal", "title": "Terms", "content": {"body": "x"}},
        )
    assert exc.value.status_code == 400
    assert "Policy key is required" == exc.value.detail


def test_policy_upsert_requires_core_fields(db):
    user = _admin_user(db)
    with pytest.raises(HTTPException) as exc:
        GovernanceService.create_or_update_policy(
            db,
            user,
            {"key": "terms_of_service", "title": "Terms"},
        )
    assert exc.value.status_code == 400
    assert "Missing required policy fields" in str(exc.value.detail)
