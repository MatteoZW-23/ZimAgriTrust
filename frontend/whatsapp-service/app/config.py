"""Configuration for WhatsApp Service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # WhatsApp Bridge
    whatsapp_bridge_url: str = "http://whatsapp-bridge:3006"
    whatsapp_bridge_timeout: float = 2.0

    # Main Backend
    main_backend_url: str = "http://backend:8000"

    # Application
    app_name: str = "whatsapp-service"
    log_level: str = "INFO"
    debug: bool = False

    # Streams
    stream_outbound: str = "whatsapp:outbound"
    stream_inbound: str = "whatsapp:inbound"
    stream_responses: str = "whatsapp:responses"
    stream_notifications: str = "whatsapp:notifications"

    # Consumer Group
    consumer_group: str = "whatsapp-service-group"
    consumer_name: str = "whatsapp-service-1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
