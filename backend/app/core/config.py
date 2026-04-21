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
