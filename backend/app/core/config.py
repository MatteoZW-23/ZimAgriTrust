from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    APP_NAME: str = "Agri Trust Marketplace API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-to-a-high-entropy-string-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15          # 15 minutes — short-lived
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200       # 30 days
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/agri_trust"
    ADMIN_BOOTSTRAP_TOKEN: str = "secret-bootstrap-token"
    
    # --- AUTHENTICATION CONFIG ---
    # The platform has transitioned to numeric PINs for all roles (Farmer, Buyer, Agent, Admin)
    # to maintain consistency with regional USSD/Banking standards.
    
    # Bootstrap settings are now managed via environment variables or scripts.


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # --- SMS CONFIG (AfricasTalking) ---
    SMS_API_KEY: str = ""
    SMS_USERNAME: str = "sandbox"
    SMS_SENDER_ID: str = "ZimAgritrust"

    # --- SENTRY CONFIG ---
    SENTRY_DSN: str = ""

    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003,http://localhost:19000,http://localhost:19001,http://localhost:19002,http://localhost:19006,http://localhost:5000,http://localhost:5173"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,host.docker.internal"
    FORCE_HTTPS: bool = False

    # --- SECURITY CONFIG ---
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # requests per window
    RATE_LIMIT_WINDOW_SECONDS: int = 60  # window size in seconds
    
    # Admin-specific security
    ADMIN_RATE_LIMIT_REQUESTS: int = 30  # stricter limit for admin
    ADMIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    ADMIN_IP_WHITELIST: str = ""  # comma-separated list of allowed IPs, empty = disabled
    ADMIN_SESSION_TIMEOUT_MINUTES: int = 30  # auto-logout after inactivity
    ADMIN_MFA_ENABLED: bool = False  # enable multi-factor authentication
    ADMIN_AUDIT_LOGGING: bool = True  # log all admin actions
    
    # Account lockout
    ACCOUNT_LOCKOUT_ENABLED: bool = True
    ACCOUNT_LOCKOUT_ATTEMPTS: int = 5  # max failed attempts
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30  # lockout duration
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_HISTORY_COUNT: int = 5  # prevent reuse of last N passwords
    PASSWORD_EXPIRY_DAYS: int = 90   # force password change after N days

    # --- SESSION & DEVICE SECURITY ---
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_FINGERPRINTING: bool = True
    NEW_DEVICE_ALERT: bool = True
    REQUIRE_MFA_ADMIN: bool = True  # enforce 2FA for all admin accounts
    EMAIL_VERIFICATION_REQUIRED: bool = True  # require email verification for buyers/agents

    # --- ADVANCED SECURITY ---
    ANOMALY_DETECTION_ENABLED: bool = True
    ANOMALY_THRESHOLD: int = 3  # suspicious actions before alert
    HMAC_SECRET: str = ""  # for webhook/request signing
    SECURE_UPLOAD_DIR: str = "/tmp/agritrust-uploads"  # outside web root

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
