import os
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    APP_NAME: str = "Agri Trust Marketplace API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/zimagritrust"
    ADMIN_BOOTSTRAP_TOKEN: str = "secret-bootstrap-token"
    
    # --- AUTHENTICATION CONFIG ---
    # Farmers, buyers, and drivers use numeric PINs. Staff use password + MFA.
    
    # Bootstrap settings are now managed via environment variables or scripts.


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("SECRET_KEY", "REFRESH_SECRET_KEY", "PIN_PEPPER")
    @classmethod
    def validate_secrets(cls, v: str, info: ValidationInfo) -> str:
        """Ensure secrets are properly configured and not default/placeholder values."""
        field_name = info.field_name
        
        # Check for default/placeholder values
        placeholders = [
            "CHANGE_ME", "CHANGE-ME", "CHANGE ME",
            "default", "secret", "password", "admin",
            "123456", "12345678", "qwerty", "abc123"
        ]
        
        v_lower = v.lower()
        if any(p in v_lower for p in placeholders):
            raise ValueError(f"{field_name} cannot contain placeholder/default values. Set a secure secret via environment variable.")
        
        # Minimum length requirements
        min_lengths = {
            "SECRET_KEY": 32,
            "REFRESH_SECRET_KEY": 32,
            "PIN_PEPPER": 16,
        }
        
        if len(v) < min_lengths.get(field_name, 16):
            raise ValueError(f"{field_name} must be at least {min_lengths.get(field_name, 16)} characters for security")
        
        return v

    @field_validator("MASTER_TEST_LOGIN_ENABLED")
    @classmethod
    def validate_master_test(cls, v: bool) -> bool:
        """Prevent master test account in production."""
        app_env = os.getenv("APP_ENV", "development")
        if v and app_env == "production":
            raise ValueError("MASTER_TEST_LOGIN_ENABLED cannot be True in production environment")
        return v

    @field_validator("ADMIN_BOOTSTRAP_TOKEN")
    @classmethod
    def validate_bootstrap_token(cls, v: str) -> str:
        """Ensure bootstrap token is not a default value."""
        if v.lower() in ["secret-bootstrap-token", "admin", "password", "123456"]:
            raise ValueError("ADMIN_BOOTSTRAP_TOKEN must be changed from default value")
        return v

    # --- AWS SES CONFIG ---
    AWS_SES_REGION: str = "us-east-1"
    AWS_SES_ACCESS_KEY_ID: str = ""
    AWS_SES_SECRET_ACCESS_KEY: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True

    EMAIL_TEMPLATE_DIR: str = "app/templates/email"

    # --- SENTRY CONFIG ---
    SENTRY_DSN: str = ""

    REDIS_URL: str = "redis://redis:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:3004"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,host.docker.internal"
    FORCE_HTTPS: bool = False

    # ============================================================================
    # AUTHENTICATION & SESSION SECURITY
    # ============================================================================
    
    # JWT Configuration
    REFRESH_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"
    TOKEN_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRY_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRY_DAYS: int = 30
    RESET_TOKEN_EXPIRY_MINUTES: int = 60
    INVITATION_TOKEN_EXPIRY_HOURS: int = 72
    
    # Unified PIN System (USSD + App)
    PIN_MIN_LENGTH: int = 4
    PIN_MAX_LENGTH: int = 6
    PIN_PEPPER: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR_OR_VAULT"
    PIN_LOCKOUT_ATTEMPTS: int = 3
    PIN_LOCKOUT_DURATION_MINUTES: int = 15
    PIN_HISTORY_COUNT: int = 3  # Prevent reuse of last 3 PINs
    
    # Password Requirements (Admins & Staff)
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_COUNT: int = 5  # Prevent reuse of last 5 passwords
    PASSWORD_EXPIRY_DAYS: int = 90  # Force password change after 90 days
    PASSWORD_BREACH_CHECK: bool = True  # Check against HaveIBeenPwned
    
    # Rate Limiting by Endpoint
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # per hour
    RATE_LIMIT_PASSWORD_RESET: int = 3  # per hour
    RATE_LIMIT_PIN_ATTEMPTS: int = 5  # per hour (locked after 3)
    RATE_LIMIT_MFA_ATTEMPTS: int = 10  # per hour
    RATE_LIMIT_OTP_REQUESTS: int = 3  # per hour
    RATE_LIMIT_API_GENERAL: int = 100  # per minute
    RATE_LIMIT_GENERAL_WINDOW_MINUTES: int = 1
    
    # Account Lockout & Security
    ACCOUNT_LOCKOUT_ENABLED: bool = True
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5  # Failed login attempts
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    
    # Session Management
    SESSION_ABSOLUTE_TIMEOUT_MINUTES: int = 480  # Maximum session lifetime (8 hours)
    SESSION_IDLE_TIMEOUT_MINUTES: int = 60  # Logout after inactivity
    MAX_CONCURRENT_SESSIONS: int = 5  # Default for most roles
    CONCURRENT_SESSIONS_BY_ROLE: dict = {
        'SUPER_ADMIN': 1,
        'SYSTEM_ADMIN': 2,
        'FINANCE_ADMIN': 2,
        'REGIONAL_ADMIN': 3,
        'SUPPORT_ADMIN': 5,
        'BRANCH_ADMIN': 5,
        'AGENT': 1,
        'STAFF': 3,
        'FARMER': None,  # Unlimited
        'BUYER': None,
        'DRIVER': 1,
    }
    
    # Multi-Factor Authentication (MFA)
    MFA_REQUIRED_ROLES: list = ['SUPER_ADMIN', 'ADMIN', 'SYSTEM_ADMIN', 'FINANCE_ADMIN', 'REGIONAL_ADMIN', 'REGIONAL_MANAGER']
    MFA_OPTIONAL_ROLES: list = ['SUPPORT_ADMIN', 'BRANCH_ADMIN', 'STAFF']
    TOTP_WINDOW: int = 1  # Time step window for TOTP (30 seconds)
    BACKUP_CODES_COUNT: int = 10
    
    # Device & IP Security
    SESSION_FINGERPRINTING_ENABLED: bool = True
    IP_CHANGE_ALERT: bool = True
    NEW_DEVICE_ALERT: bool = True
    DEVICE_FINGERPRINT_ENFORCEMENT: bool = False  # Strict mode: reject if fingerprint changes
    
    # Advanced Threat Detection
    ANOMALY_DETECTION_ENABLED: bool = True
    BRUTE_FORCE_DETECTION_ENABLED: bool = True
    LOCATION_CHANGE_DETECTION_ENABLED: bool = True
    DEVICE_CHANGE_DETECTION_ENABLED: bool = True
    
    # Audit Logging
    ADMIN_AUDIT_LOGGING: bool = False
    AUDIT_LOGGING_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 365
    AUDIT_LOG_SENSITIVE_ENDPOINTS: list = [
        '/api/v1/auth/',
        '/api/v1/admin/',
        '/api/v1/transactions/',
        '/api/v1/payments/',
    ]
    
    # ============================================================================
    # NOTIFICATION CONFIGURATION (Multi-Channel)
    # ============================================================================
    
    # All notifications sent via SMS + WhatsApp + Email
    NOTIFICATION_CHANNELS_ENABLED: dict = {
        'sms': True,
        'whatsapp': True,
        'email': True,
    }
    
    # SMS Configuration (Africa's Talking)
    SMS_API_KEY: str = ""
    SMS_USERNAME: str = "sandbox"
    SMS_SENDER_ID: str = "ZimAgriTrust"
    SMS_ENABLE: bool = True
    
    # WhatsApp Configuration (WhatsApp Business API)
    WHATSAPP_API_KEY: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_ENABLE: bool = True
    
    # Email Configuration
    EMAIL_PROVIDER: str = "sendgrid"  # sendgrid, ses, smtp, console
    EMAIL_FROM_ADDRESS: str = "security@zimagritrust.co.zw"
    EMAIL_FROM_NAME: str = "ZimAgriTrust Security"
    EMAIL_REPLY_TO: str = "support@zimagritrust.co.zw"
    SENDGRID_API_KEY: str = ""
    EMAIL_ENABLE: bool = True
    
    # Notification Template Settings
    NOTIFICATION_RETRY_ATTEMPTS: int = 3
    NOTIFICATION_RETRY_DELAY_SECONDS: int = 5
    
    # ============================================================================
    # ROLE & PERMISSION SECURITY
    # ============================================================================
    
    # Invitation System (for privileged roles)
    INVITATION_ENABLED: bool = True
    INVITATION_EXPIRY_HOURS: int = 72
    PRIVILEGED_ROLES: list = [
        'SYSTEM_ADMIN',
        'FINANCE_ADMIN',
        'REGIONAL_ADMIN',
        'SUPPORT_ADMIN',
        'BRANCH_ADMIN',
        'AGENT',
        'STAFF',
    ]
    
    # Role-Based Access Control (RBAC)
    RBAC_ENABLED: bool = True
    PERMISSION_INHERITANCE_ENABLED: bool = True  # Lower roles inherit permissions
    
    # ============================================================================
    # FRONTEND CONFIGURATION
    # ============================================================================
    
    FRONTEND_URL: str = "http://localhost:3000"
    ADMIN_DASHBOARD_URL: str = "http://localhost:3001"
    AGENT_PORTAL_URL: str = "http://localhost:3002"
    APP_PORTAL_URL: str = "http://localhost:3003"
    SUPPLIER_PORTAL_URL: str = "http://localhost:3004"
    
    # ============================================================================
    # SECURITY HEADERS & CORS
    # ============================================================================
    
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list = [
        "Authorization",
        "Content-Type",
        "X-CSRF-Token",
        "X-Request-ID",
        "Idempotency-Key",
        "Accept",
        "Origin",
        "Cache-Control",
    ]
    
    # Security Headers
    SECURE_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CSP_ENABLED: bool = True
    CSP_POLICY: str = "default-src 'self'"
    SECURE_UPLOAD_DIR: str = "/tmp/agritrust-uploads"  # outside web root

    # --- SUPER ADMIN (highest privilege, separate everything) ---
    SUPER_ADMIN_SECRET_KEY: str = ""  # MUST differ from SECRET_KEY in prod
    SUPER_ADMIN_TOKEN_EXPIRE_MINUTES: int = 30  # stricter expiry
    SUPER_ADMIN_IP_WHITELIST: str = ""  # comma-separated; empty = disabled
    SUPER_ADMIN_HARDWARE_MFA_REQUIRED: bool = True  # YubiKey/TOTP
    SUPER_ADMIN_PATH_PREFIX: str = "/api/v1/super-admin"
    SUPER_ADMIN_ALERT_PHONE: str = ""  # SMS target for critical alerts
    SUPER_ADMIN_ALERT_EMAIL: str = ""  # email target for daily reports

    # --- ADMIN IP WHITELIST ---
    ADMIN_IP_WHITELIST: str = ""  # comma-separated; empty = disabled

    # --- TRANSACTION SIGNING (financial integrity) ---
    TRANSACTION_SIGNING_KEY: str = ""  # HMAC key for signing every fund movement
    AUDIT_CHAIN_KEY: str = ""  # HMAC key for tamper-proof audit checksum chain

    # --- WITHDRAWAL LIMITS / FEES ---
    WITHDRAWAL_FEE_PERCENT: float = 0.01  # 1%
    WITHDRAWAL_FEE_CAP: float = 5.0
    WITHDRAWAL_MIN_AMOUNT: float = 5.0
    WITHDRAWALS_PER_DAY_MAX: int = 3
    DEPOSIT_ATTEMPTS_PER_HOUR_MAX: int = 10
    PAYMENT_ATTEMPTS_PER_TRANSACTION_MAX: int = 5

    # Tier daily/weekly caps (override via withdrawal_limits table at runtime)
    TIER_UNVERIFIED_DAILY: float = 50.0
    TIER_UNVERIFIED_WEEKLY: float = 200.0
    TIER_VERIFIED_DAILY: float = 500.0
    TIER_VERIFIED_WEEKLY: float = 2000.0
    TIER_TRUSTED_DAILY: float = 1000.0
    TIER_TRUSTED_WEEKLY: float = 5000.0
    TIER_TRUSTED_MIN_TRUST_SCORE: int = 80

    # --- DUAL / MULTI APPROVAL ---
    DUAL_APPROVAL_REFUND_THRESHOLD_USD: float = 100.0
    MULTI_APPROVAL_TXN_THRESHOLD_USD: float = 2000.0
    SENIOR_ADMIN_APPROVAL_LIMIT_USD: float = 2000.0
    FINANCE_ADMIN_APPROVAL_LIMIT_USD: float = 500.0

    # --- TIME-BASED ACCESS CONTROL (Zimbabwe local time, UTC+2) ---
    FINANCIAL_APPROVAL_HOURS_START: int = 8   # 08:00
    FINANCIAL_APPROVAL_HOURS_END: int = 17    # 17:00
    FINANCIAL_APPROVAL_TZ_OFFSET_HOURS: int = 2  # CAT
    FINANCIAL_APPROVAL_TIME_WINDOW_ENABLED: bool = True

    # --- ESCROW TWO-KEY RELEASE ---
    ESCROW_TWO_KEY_REQUIRED_THRESHOLD_USD: float = 0.0  # 0 = required for ALL escrow releases
    ESCROW_ADMIN_OTP_TTL_SECONDS: int = 300  # 5 min

    # --- FRAUD DETECTION ---
    FRAUD_VELOCITY_WINDOW_SECONDS: int = 3600  # multiple withdrawals in <1h
    FRAUD_VELOCITY_THRESHOLD: int = 2  # >=2 withdrawals in window flagged
    FRAUD_STRUCTURING_GAP_PERCENT: float = 0.05  # within 5% of limit = structuring
    FRAUD_NEW_USER_DAYS: int = 7
    FRAUD_NEW_USER_LARGE_WITHDRAWAL_USD: float = 100.0
    FRAUD_TRUST_SCORE_SPIKE_THRESHOLD: int = 30  # +30 without txns

    # --- BUYER DEPOSITS ---
    DEPOSIT_MIN_AMOUNT: float = 5.0
    DEPOSIT_REFUND_WINDOW_DAYS: int = 7
    DEPOSIT_REFUND_FEE_PERCENT: float = 0.02
    DEPOSIT_REFUND_FEE_CAP: float = 10.0
    DEPOSIT_INSURANCE_PER_USER_USD: float = 500.0
    PARTNER_BANK_NAME: str = "CABS Bank"
    PARTNER_BANK_ACCOUNT_NAME: str = "ZimAgriTrust Trust Account"
    PARTNER_BANK_ACCOUNT_NUMBER: str = "1000000000"
    PARTNER_BANK_BRANCH_CODE: str = "CABSZWHA"

    # --- INPUT MARKETPLACE ---
    INPUT_PLATFORM_FEE_PERCENT: float = 0.025
    INPUT_ESCROW_FEE_PERCENT: float = 0.005
    INPUT_BOOST_FEE_USD: float = 2.0
    INPUT_VERIFICATION_FEE_REGULATED_USD: float = 2.0
    INPUT_VERIFICATION_FEE_BASIC_USD: float = 1.0
    INPUT_SELLER_MIN_TRUST_SCORE: int = 40
    INPUT_BULK_ORDER_MIN_USD: float = 500.0
    INPUT_EXPIRY_WARNING_DAYS: int = 7

    # --- EMERGENCY SHUTDOWN ---
    PLATFORM_SHUTDOWN: bool = False  # toggled by super-admin emergency endpoint

    # --- PAYMENT SAFETY ---
    # CRITICAL: Must be False in production. True only for local dev/test.
    AUTO_CONFIRM_PAYMENTS: bool = False

    # --- DEVELOPMENT TOOLING ---
    # Debug/simulator endpoints must stay off unless explicitly enabled.
    ENABLE_USSD_DEBUG_TOOLS: bool = False
    ENABLE_WHATSAPP_TEST_ENDPOINTS: bool = False

    # --- MASTER TEST ACCOUNT (MUST be False in production) ---
    MASTER_TEST_LOGIN_ENABLED: bool = False
    MASTER_TEST_PHONE: str = ""
    MASTER_TEST_PASSWORD: str = ""

    # --- DATABASE POOL ---
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_STATEMENT_TIMEOUT_MS: int = 30000

    @property
    def super_admin_ip_whitelist_list(self) -> list[str]:
        if not self.SUPER_ADMIN_IP_WHITELIST:
            return []
        return [ip.strip() for ip in self.SUPER_ADMIN_IP_WHITELIST.split(",") if ip.strip()]

    @property
    def effective_super_admin_secret(self) -> str:
        return self.SUPER_ADMIN_SECRET_KEY or (self.SECRET_KEY + "::super-admin")

    @property
    def effective_transaction_signing_key(self) -> str:
        return self.TRANSACTION_SIGNING_KEY or (self.SECRET_KEY + "::txn-signing")

    @property
    def effective_audit_chain_key(self) -> str:
        return self.AUDIT_CHAIN_KEY or (self.SECRET_KEY + "::audit-chain")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        hosts = [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
        # If wildcard is present, return just ["*"] — TrustedHostMiddleware treats this as allow-all
        if "*" in hosts:
            return ["*"]
        return hosts

    @property
    def admin_ip_whitelist_list(self) -> list[str]:
        """Parse admin IP whitelist from comma-separated string"""
        if not self.ADMIN_IP_WHITELIST:
            return []
        return [ip.strip() for ip in self.ADMIN_IP_WHITELIST.split(",") if ip.strip()]


settings = Settings()
