from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    APP_NAME: str = "Agri Trust Marketplace API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-me-to-a-high-entropy-string-for-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week 
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/agri_trust"
    
    # --- PIN-BASED AUTHENTICATION CONFIG ---
    # The platform has transitioned to numeric PINs for all roles (Farmer, Buyer, Agent, Admin)
    # to maintain consistency with regional USSD/Banking standards.
    
    MASTER_TEST_LOGIN_ENABLED: bool = False

    MASTER_TEST_PHONE: str = "777777777"
    MASTER_TEST_PASSWORD: str = "7777"  # Numeric PIN for System Override
    MASTER_TEST_ALIAS: str = "master"
    MASTER_TEST_NAME: str = "AgriTrust Master System"
    ADMIN_BOOTSTRAP_TOKEN: str = "agritrust-init-secret-2026"


    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:19006,http://localhost:5000,http://localhost:5173"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,host.docker.internal"
    FORCE_HTTPS: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]


settings = Settings()
