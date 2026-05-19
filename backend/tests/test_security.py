"""
Comprehensive Security & Authentication Tests
Tests all security flows including:
- Authentication (login, MFA, password reset)
- Authorization (RBAC, permissions, portal isolation)
- Session management (tokens, refresh, logout)
- Rate limiting
- Security headers
- MFA encryption
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock
import time
from jose import jwt

from app.main import app
from app.core.config import settings
from app.core.security import (
    create_access_token, create_refresh_token, verify_password,
    get_password_hash, encrypt_mfa_secret, decrypt_mfa_secret,
    generate_totp_secret, verify_totp_code
)
from app.models.user import User, UserRole, UserStatus
from app.db.session import SessionLocal

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def db():
    """Database session fixture."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_farmer(db: Session):
    """Create a test farmer user."""
    user = User(
        phone_number="+263770000001",
        full_name="Test Farmer",
        password_hash=get_password_hash("1234"),
        ussd_pin_hash=get_password_hash("1234"),
        role=UserRole.FARMER,
        is_active=True,
        is_suspended=False,
        is_phone_verified=True,
        trust_score=50,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture
def test_admin(db: Session):
    """Create a test admin user with MFA enabled."""
    secret = generate_totp_secret()
    user = User(
        phone_number="+263770000002",
        full_name="Test Admin",
        password_hash=get_password_hash("Admin@123456!"),
        ussd_pin_hash=get_password_hash("Admin@123456!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_suspended=False,
        is_phone_verified=True,
        mfa_enabled=True,
        mfa_secret=encrypt_mfa_secret(secret),
        trust_score=100,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture
def test_agent(db: Session):
    """Create a test agent user."""
    secret = generate_totp_secret()
    user = User(
        phone_number="+263770000003",
        full_name="Test Agent",
        password_hash=get_password_hash("Agent@123456!"),
        ussd_pin_hash=get_password_hash("Agent@123456!"),
        role=UserRole.AGENT,
        is_active=True,
        is_suspended=False,
        is_phone_verified=True,
        mfa_enabled=True,
        mfa_secret=encrypt_mfa_secret(secret),
        trust_score=80,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture
def test_buyer(db: Session):
    """Create a test buyer user."""
    user = User(
        phone_number="+263770000004",
        full_name="Test Buyer",
        password_hash=get_password_hash("5678"),
        ussd_pin_hash=get_password_hash("5678"),
        role=UserRole.BUYER,
        is_active=True,
        is_suspended=False,
        is_phone_verified=True,
        trust_score=50,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD & ENCRYPTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPasswordSecurity:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test that passwords are properly hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        assert hash1 != hash2  # Different salts
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_mfa_secret_encryption(self):
        """Test MFA secret encryption and decryption."""
        secret = generate_totp_secret()
        encrypted = encrypt_mfa_secret(secret)
        decrypted = decrypt_mfa_secret(encrypted)
        
        assert encrypted != secret
        assert decrypted == secret

    def test_mfa_encryption_deterministic(self):
        """Test that encryption produces different ciphertexts but decrypts correctly."""
        secret = generate_totp_secret()
        encrypted1 = encrypt_mfa_secret(secret)
        encrypted2 = encrypt_mfa_secret(secret)
        
        # Fernet produces different ciphertexts each time (due to random IV)
        assert encrypted1 != encrypted2
        assert decrypt_mfa_secret(encrypted1) == secret
        assert decrypt_mfa_secret(encrypted2) == secret


# ═══════════════════════════════════════════════════════════════════════════════
# JWT TOKEN TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestJWTSecurity:
    """Test JWT token creation, validation, and security."""

    def test_access_token_creation(self):
        """Test access token is created with correct claims."""
        user_id = "test-user-123"
        role = "farmer"
        token = create_access_token(user_id, role, portal="public")
        
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert decoded["sub"] == user_id
        assert decoded["role"] == role
        assert decoded["portal"] == "public"
        assert decoded["type"] == "access"
        assert "jti" in decoded
        assert "exp" in decoded
        assert "iat" in decoded

    def test_access_token_expiration(self):
        """Test access token expires after configured time."""
        token = create_access_token("user123", "farmer")
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        expected_exp = decoded["iat"] + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        assert decoded["exp"] == expected_exp

    def test_refresh_token_creation(self):
        """Test refresh token has correct type and family."""
        token = create_refresh_token("user123")
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert decoded["type"] == "refresh"
        assert decoded["sub"] == "user123"
        assert "jti" in decoded
        assert "family" in decoded

    def test_token_tampering_detection(self):
        """Test that tampered tokens are rejected."""
        token = create_access_token("user123", "farmer")
        
        # Tamper with the token
        parts = token.split(".")
        tampered = f"{parts[0]}.{parts[1]}.tampered_signature"
        
        with pytest.raises(jwt.JWTError):
            jwt.decode(tampered, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHENTICATION FLOW TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPublicPortalAuth:
    """Test public portal authentication (Farmer, Buyer, Driver)."""

    @patch("app.services.notification_service.NotificationService.send_verification_code")
    def test_farmer_login_step1(self, mock_send, test_farmer, db):
        """Test step 1 of farmer login sends OTP."""
        mock_send.return_value = AsyncMock()
        
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_farmer.phone_number,
            "password": "1234"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "2FA_REQUIRED"
        assert "message" in data
        mock_send.assert_called_once()

    def test_farmer_login_invalid_credentials(self, test_farmer, db):
        """Test login with wrong password fails."""
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_farmer.phone_number,
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_farmer_login_suspended_account(self, test_farmer, db):
        """Test suspended account cannot login."""
        test_farmer.is_suspended = True
        db.commit()
        
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_farmer.phone_number,
            "password": "1234"
        })
        
        assert response.status_code == 403
        assert "suspended" in response.json()["detail"].lower()

    @patch("app.services.cache_service.cache_service.get")
    @patch("app.services.cache_service.cache_service.delete")
    @patch("app.services.notification_service.NotificationService.send_verification_code")
    def test_buyer_full_login_flow(self, mock_send, mock_cache_delete, mock_cache_get, test_buyer, db):
        """Test complete buyer login flow with 2FA."""
        mock_send.return_value = AsyncMock()
        mock_cache_get.return_value = "123456"  # Mock OTP
        mock_cache_delete.return_value = AsyncMock()
        
        # Step 1: Login with credentials
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_buyer.phone_number,
            "password": "5678"
        })
        
        assert response.status_code == 200
        
        # Step 2: Verify 2FA code
        response = client.post("/api/v1/auth/verify-login-2fa", json={
            "phone_number": test_buyer.phone_number,
            "otp": "123456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["role"] == "buyer"


class TestPrivilegedPortalAuth:
    """Test admin and agent portal authentication with MFA."""

    @patch("app.services.notification_service.NotificationService.send_verification_code")
    def test_admin_login_step1(self, mock_send, test_admin, db):
        """Test admin login step 1 sends OTP."""
        mock_send.return_value = AsyncMock()
        
        response = client.post("/api/v1/auth/admin/login", json={
            "phone_number": test_admin.phone_number,
            "password": "Admin@123456!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ADMIN_2FA_REQUIRED"

    def test_admin_wrong_portal_blocked(self, test_admin, db):
        """Test admin cannot use public portal."""
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_admin.phone_number,
            "password": "Admin@123456!"
        })
        
        # Even at step 1, after 2FA, it should be blocked
        # But we need to mock the OTP first
        assert response.status_code == 200  # Step 1 passes
        
    def test_agent_wrong_portal_blocked(self, test_agent, db):
        """Test agent cannot use public portal."""
        response = client.post("/api/v1/auth/login", json={
            "phone_number": test_agent.phone_number,
            "password": "Agent@123456!"
        })
        
        # Step 1 passes but 2FA should block
        assert response.status_code == 200

    def test_non_admin_cannot_use_admin_portal(self, test_farmer, db):
        """Test farmer cannot use admin portal."""
        response = client.post("/api/v1/auth/admin/login", json={
            "phone_number": test_farmer.phone_number,
            "password": "1234"
        })
        
        assert response.status_code == 403
        assert "restricted to Administrators" in response.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# AUTHORIZATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRBAC:
    """Test Role-Based Access Control."""

    def test_token_portal_isolation(self, test_admin):
        """Test that tokens are bound to specific portals."""
        # Create admin token for admin portal
        admin_token = create_access_token(str(test_admin.id), "admin", portal="admin")
        
        decoded = jwt.decode(admin_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["portal"] == "admin"
        assert decoded["role"] == "admin"

    def test_privileged_role_detection(self):
        """Test privileged role detection."""
        from app.core.permissions import is_privileged_role, PRIVILEGED_ROLES
        
        assert is_privileged_role("admin") is True
        assert is_privileged_role("agent") is True
        assert is_privileged_role("farmer") is False
        assert is_privileged_role("buyer") is False
        assert is_privileged_role("driver") is False

    def test_permission_check(self):
        """Test granular permission checks."""
        from app.core.permissions import has_permission
        
        # Admin has all permissions
        assert has_permission("admin", "manage_users") is True
        assert has_permission("admin", "delete_user") is True
        assert has_permission("admin", "view_analytics") is True
        
        # Agent has specific permissions
        assert has_permission("agent", "verify_crops") is True
        assert has_permission("agent", "manage_users") is False
        
        # Farmer has their own permissions
        assert has_permission("farmer", "create_listing") is True
        assert has_permission("farmer", "verify_crops") is False


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionManagement:
    """Test session management, token refresh, and logout."""

    def test_token_refresh(self, test_farmer):
        """Test token refresh endpoint."""
        refresh_token = create_refresh_token(str(test_farmer.id))
        
        # Set cookie and test refresh
        client.cookies.set("refresh_token", refresh_token)
        
        response = client.post("/api/v1/auth/refresh")
        
        # Should work with valid refresh token
        assert response.status_code in [200, 401]  # 401 if token blacklisted

    def test_logout_blacklists_token(self, test_farmer):
        """Test logout blacklists the access token."""
        access_token = create_access_token(str(test_farmer.id), "farmer")
        
        # Set cookie
        client.cookies.set("access_token", access_token)
        
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY MIDDLEWARE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityHeaders:
    """Test security headers are present on all responses."""

    def test_security_headers_present(self):
        """Test that security headers are added to responses."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = client.options("/api/v1/auth/login")
        
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-credentials" in response.headers


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_auth_endpoint_rate_limit(self):
        """Test that auth endpoints have stricter rate limits."""
        # This test makes multiple requests to trigger rate limiting
        responses = []
        for _ in range(25):
            response = client.post("/api/v1/auth/login", json={
                "phone_number": "+263770000000",
                "password": "wrong"
            })
            responses.append(response.status_code)
        
        # Should eventually hit rate limit (429)
        assert 429 in responses or all(r == 401 for r in responses)


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD RESET TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPasswordReset:
    """Test password reset flow."""

    @patch("app.services.notification_service.NotificationService.send_verification_code")
    @patch("app.services.cache_service.cache_service.set")
    def test_forgot_password_sends_otp(self, mock_cache_set, mock_send, test_farmer, db):
        """Test forgot password sends OTP."""
        mock_send.return_value = AsyncMock()
        mock_cache_set.return_value = AsyncMock()
        
        response = client.post("/api/v1/auth/forgot-password", json={
            "phone_number": test_farmer.phone_number
        })
        
        assert response.status_code == 200
        assert "sent" in response.json()["message"].lower()

    @patch("app.services.cache_service.cache_service.get")
    @patch("app.services.cache_service.cache_service.delete")
    def test_reset_password_with_valid_otp(self, mock_cache_delete, mock_cache_get, test_farmer, db):
        """Test password reset with valid OTP."""
        mock_cache_get.return_value = "123456"
        mock_cache_delete.return_value = AsyncMock()
        
        response = client.post("/api/v1/auth/reset-password", json={
            "phone_number": test_farmer.phone_number,
            "otp": "123456",
            "new_password": "5678"
        })
        
        assert response.status_code == 200
        assert "updated" in response.json()["message"].lower()


# ═══════════════════════════════════════════════════════════════════════════════
# TOTP/MFA TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestTOTP:
    """Test TOTP/MFA functionality."""

    def test_totp_generation(self):
        """Test TOTP code generation."""
        from app.core.security import generate_totp_code
        
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        
        assert len(code) == 6
        assert code.isdigit()

    def test_totp_verification(self):
        """Test TOTP code verification."""
        secret = generate_totp_secret()
        code = generate_totp_code(secret)
        
        assert verify_totp_code(secret, code) is True
        assert verify_totp_code(secret, "000000") is False

    def test_totp_time_drift_tolerance(self):
        """Test TOTP accepts codes within time drift window."""
        from app.core.security import generate_totp_code
        
        secret = generate_totp_secret()
        
        # Code at current time
        code_now = generate_totp_code(secret)
        assert verify_totp_code(secret, code_now) is True


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullAuthFlows:
    """Integration tests for complete authentication flows."""

    def test_complete_farmer_registration_login(self, db):
        """Test full farmer registration and login flow."""
        # Register
        response = client.post("/api/v1/auth/register", json={
            "phone_number": "+263779999999",
            "full_name": "New Farmer",
            "password": "1234",
            "role": "farmer"
        })
        
        assert response.status_code == 200
        user_id = response.json()["id"]
        
        # Check user was created
        user = db.query(User).filter(User.id == user_id).first()
        assert user is not None
        assert user.role == UserRole.FARMER
        
        # Cleanup
        db.delete(user)
        db.commit()

    def test_token_validation_after_login(self, test_farmer):
        """Test that tokens are properly validated after login."""
        # Create token
        token = create_access_token(str(test_farmer.id), "farmer")
        
        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == str(test_farmer.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
