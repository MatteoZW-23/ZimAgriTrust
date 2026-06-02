import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import UserResponse

router = APIRouter()
logger = logging.getLogger(__name__)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, min_length=7, max_length=32)
    province: Optional[str] = Field(default=None, max_length=50)
    district: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=200)


class UserSettingsUpdate(BaseModel):
    push_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    email_notifications: Optional[bool] = None
    language: Optional[str] = Field(default=None, pattern="^(en|sn|nd)$")
    data_sharing_consent: Optional[bool] = None
    phone_visibility: Optional[bool] = None
    marketplace_discovery: Optional[bool] = None


class PinChangePayload(BaseModel):
    current_pin: str = Field(min_length=4, max_length=6)
    new_pin: str = Field(min_length=4, max_length=6)


def _settings_for(user: User) -> dict:
    prefs = user.notification_prefs or {}
    return {
        "push_notifications": prefs.get("push_notifications", prefs.get("push", True)),
        "sms_notifications": prefs.get("sms_notifications", prefs.get("sms", True)),
        "email_notifications": prefs.get("email_notifications", prefs.get("email", True)),
        "language": user.preferred_language or "en",
        "data_sharing_consent": prefs.get("data_sharing_consent", True),
        "phone_visibility": prefs.get("phone_visibility", False),
        "marketplace_discovery": prefs.get("marketplace_discovery", True),
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    try:
        return current_user
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user")


@router.put("/me", response_model=UserResponse)
def update_me(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    try:
        updates = payload.model_dump(exclude_unset=True)
        phone = updates.get("phone_number")
        if phone and phone != current_user.phone_number:
            duplicate = db.query(User).filter(User.phone_number == phone, User.id != current_user.id).first()
            if duplicate:
                raise HTTPException(status_code=400, detail="Phone number is already in use.")

        address = updates.pop("address", None)
        for field, value in updates.items():
            setattr(current_user, field, value)
        if address:
            current_user.district = address[:50]

        db.commit()
        db.refresh(current_user)
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update user")


@router.get("/trust-score")
def get_trust_score(current_user: User = Depends(get_current_user)):
    return {
        "trust_score": current_user.trust_score,
        "risk_score": current_user.risk_score,
        "breakdown": {
            "phone_verified": 5 if current_user.is_phone_verified else 0,
            "id_verified": 15 if current_user.id_verified else 0,
            "location_verified": 20 if current_user.is_location_verified else 0,
        },
    }


@router.post("/pin/change", response_model=UserResponse)
def change_user_pin(
    payload: PinChangePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in {UserRole.FARMER, UserRole.BUYER, UserRole.DRIVER}:
        raise HTTPException(status_code=403, detail="Use the staff password flow.")
    if not payload.new_pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must contain digits only.")
    if payload.current_pin == payload.new_pin:
        raise HTTPException(status_code=400, detail="New PIN must be different.")
    if not current_user.ussd_pin_hash or not verify_password(payload.current_pin, current_user.ussd_pin_hash):
        raise HTTPException(status_code=400, detail="Current PIN is incorrect.")

    current_user.ussd_pin_hash = get_password_hash(payload.new_pin)
    current_user.password_hash = current_user.password_hash or current_user.ussd_pin_hash
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/settings")
def get_settings(current_user: User = Depends(get_current_user)):
    return _settings_for(current_user)


@router.put("/settings")
def update_settings(
    payload: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = current_user.notification_prefs or {}
    updates = payload.model_dump(exclude_unset=True)
    language = updates.pop("language", None)
    if language:
        current_user.preferred_language = language
    prefs.update(updates)
    current_user.notification_prefs = prefs
    db.commit()
    return _settings_for(current_user)


@router.delete("/data")
def delete_my_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    suffix = uuid.uuid4().hex[:12]
    current_user.phone_number = f"DEL{suffix}"
    current_user.full_name = "DELETED_USER"
    current_user.email = None
    current_user.national_id = None
    current_user.id_document_url = None
    current_user.ussd_pin_hash = None
    current_user.status = UserStatus.CLOSED
    current_user.is_active = False
    current_user.is_suspended = True
    current_user.status_notes = "User requested account/data deletion"
    db.commit()
    return {"success": True, "message": "Account closed and personal data anonymized."}
