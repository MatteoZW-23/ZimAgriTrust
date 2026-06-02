import uuid

from app.models.user import User, UserRole, UserStatus
from app.services.wallet_service import WalletService


class _DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_external_payment_supports_non_ecocash_providers(db, monkeypatch):
    user = User(
        full_name="Wallet User",
        phone_number=f"+26370{uuid.uuid4().int % 10000000:07d}",
        password_hash="hash",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    def _fake_post(*args, **kwargs):
        return _DummyResponse(
            200,
            {"poll_url": "https://provider/status/123", "instructions": "Approve on device"},
        )

    monkeypatch.setattr("requests.post", _fake_post)

    result = WalletService.initiate_external_payment(
        db=db,
        user_id=user.id,
        amount=15.0,
        currency="USD",
        provider="onemoney",
    )

    assert result["status"] == "processing"
    assert result["provider"] == "ONEMONEY"
    assert "poll_url" in result
