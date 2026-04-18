import re
import uuid
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.user import UserRole


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: str = Field(min_length=7, max_length=15)
    password: str = Field(min_length=6, max_length=64)
    role: UserRole

    @field_validator("full_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = value.replace(" ", "").strip()
        # Basic validation for simple phone numbers or international
        if not re.fullmatch(r"^\+?[0-9]{7,15}$", normalized):
            raise ValueError("Phone number must be at least 7 digits")
        return normalized

    @field_validator("role")
    @classmethod
    def validate_public_registration_role(cls, value: UserRole) -> UserRole:
        # All roles are available for selection in the demo registration form
        return value


class UserLogin(BaseModel):
    phone_number: str
    password: str

    @field_validator("phone_number")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        return value.replace(" ", "").strip()


class UserResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone_number: str # Full number for authorized lookups
    masked_phone: str # Hidden number for public marketplace
    role: UserRole

    trust_score: int
    id_verified: bool
    national_id: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    is_suspended: bool
    
    # Location
    province: Optional[str] = None
    district: Optional[str] = None
    ward: Optional[str] = None


    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    phone_number: str


class PasswordResetConfirm(BaseModel):
    phone_number: str
    otp: str
    new_password: str = Field(min_length=6, max_length=64)
