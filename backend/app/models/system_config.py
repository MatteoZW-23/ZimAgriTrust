import enum
from sqlalchemy import Column, String, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ConfigGroup(str, enum.Enum):
    GENERAL = "general"
    FINANCE = "finance"
    RISK = "risk"
    FEATURES = "features"
    REGION = "region"


class SystemConfig(Base):
    """
    Global Platform Configuration (Module 5)
    Stores dynamic settings, feature toggles, and thresholds.
    """
    __tablename__ = "system_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False) # Store as string, parse as needed
    description: Mapped[str | None] = mapped_column(Text)
    group: Mapped[ConfigGroup] = mapped_column(default=ConfigGroup.GENERAL)
    is_active: Mapped[bool] = mapped_column(default=True)
    config_type: Mapped[str] = mapped_column(default="string") # string, int, float, bool, json
