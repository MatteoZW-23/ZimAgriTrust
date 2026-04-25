"""
ID Verification Upload & Review System
- Users upload ID documents (front, back, selfie)
- Creates a pending verification record
- Admin/Agent reviews and approves or rejects
- User notified via WhatsApp + SMS on every status change
"""
import uuid
import os
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.api.deps import get_db, get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.system_audit import SystemAudit
from app.services.notification_service import NotificationService
from app.db.base import Base

router = APIRouter()

UPLOAD_DIR = "uploads/id_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE_MB = 10


# ── Model ────────────────────────────────────────────────────────────────────

class IDVerificationRequest(Base):
    __tablename__ = "id_verification_requests"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Uploaded file paths (relative to UPLOAD_DIR)
    front_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    back_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    selfie_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    national_id_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Review state
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | approved | rejected
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = __import__('sqlalchemy.orm', fromlist=['relationship']).relationship("User", foreign_keys=[user_id])


# ── Helpers ──────────────────────────────────────────────────────────────────

def _save_file(file: UploadFile, user_id: str, slot: str) -> str:
    """Save uploaded file and return relative path."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use JPEG, PNG, WebP or PDF.")

    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{user_id}_{slot}_{uuid.uuid4().hex[:8]}.{ext}"
    dest = os.path.join(UPLOAD_DIR, filename)

    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Size check after write
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    if size_mb > MAX_SIZE_MB:
        os.remove(dest)
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f} MB). Max {MAX_SIZE_MB} MB.")

    return dest


async def _notify_admin_new_submission(user: User, request_id: str):
    """Ping admins that a new ID submission is waiting for review."""
    try:
        from app.services.whatsapp_service import WhatsAppService
        # In production you'd query admin phones; here we log it
        import logging
        logging.info(f"[ID_VERIFY] New submission from {user.full_name} ({user.phone_number}) — request {request_id}")
    except Exception:
        pass


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/submit")
async def submit_id_documents(
    background_tasks: BackgroundTasks,
    front: UploadFile = File(..., description="National ID front photo"),
    back: UploadFile = File(None, description="National ID back photo (optional)"),
    selfie: UploadFile = File(None, description="Selfie holding ID (optional)"),
    national_id_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    User submits ID documents for verification.
    Creates or updates a pending verification request.
    """
    uid = str(current_user.id)

    # Cancel any existing pending request so user can resubmit
    existing = db.query(IDVerificationRequest).filter(
        IDVerificationRequest.user_id == current_user.id,
        IDVerificationRequest.status == "pending"
    ).first()
    if existing:
        db.delete(existing)
        db.flush()

    front_path = _save_file(front, uid, "front")
    back_path = _save_file(back, uid, "back") if back and back.filename else None
    selfie_path = _save_file(selfie, uid, "selfie") if selfie and selfie.filename else None

    req = IDVerificationRequest(
        user_id=current_user.id,
        front_url=front_path,
        back_url=back_path,
        selfie_url=selfie_path,
        national_id_number=national_id_number,
        status="pending",
    )
    db.add(req)

    # Store front URL on user record for quick access
    current_user.id_document_url = front_path
    if national_id_number:
        current_user.national_id = national_id_number

    db.commit()
    db.refresh(req)

    background_tasks.add_task(_notify_admin_new_submission, current_user, str(req.id))

    return {
        "request_id": str(req.id),
        "status": "pending",
        "message": "Documents submitted. An agent will review within 24 hours.",
    }


@router.get("/my-status")
def get_my_verification_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """User checks the status of their latest verification request."""
    req = (
        db.query(IDVerificationRequest)
        .filter(IDVerificationRequest.user_id == current_user.id)
        .order_by(IDVerificationRequest.submitted_at.desc())
        .first()
    )
    if not req:
        return {"status": "not_submitted", "id_verified": current_user.id_verified}

    return {
        "request_id": str(req.id),
        "status": req.status,
        "submitted_at": req.submitted_at,
        "reviewed_at": req.reviewed_at,
        "reviewer_note": req.reviewer_note,
        "id_verified": current_user.id_verified,
        "has_front": bool(req.front_url),
        "has_back": bool(req.back_url),
        "has_selfie": bool(req.selfie_url),
    }


@router.get("/queue", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def get_verification_queue(
    status: str = "pending",
    db: Session = Depends(get_db),
):
    """Admin/Agent: list all verification requests by status."""
    requests = (
        db.query(IDVerificationRequest)
        .filter(IDVerificationRequest.status == status)
        .order_by(IDVerificationRequest.submitted_at.asc())
        .all()
    )

    result = []
    for r in requests:
        user = db.query(User).filter(User.id == r.user_id).first()
        result.append({
            "request_id": str(r.id),
            "user_id": str(r.user_id),
            "user_name": user.full_name if user else "Unknown",
            "user_phone": user.phone_number if user else "",
            "user_role": user.role.value if user else "",
            "national_id_number": r.national_id_number,
            "status": r.status,
            "submitted_at": r.submitted_at,
            "reviewed_at": r.reviewed_at,
            "reviewer_note": r.reviewer_note,
            "has_front": bool(r.front_url),
            "has_back": bool(r.back_url),
            "has_selfie": bool(r.selfie_url),
            "front_url": f"/api/v1/verification/document/{r.id}/front" if r.front_url else None,
            "back_url": f"/api/v1/verification/document/{r.id}/back" if r.back_url else None,
            "selfie_url": f"/api/v1/verification/document/{r.id}/selfie" if r.selfie_url else None,
        })
    return result


@router.get("/document/{request_id}/{slot}", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def get_document_file(
    request_id: uuid.UUID,
    slot: str,
    db: Session = Depends(get_db),
):
    """Serve the actual document file to admin/agent reviewers."""
    if slot not in ("front", "back", "selfie"):
        raise HTTPException(status_code=400, detail="Invalid slot")

    req = db.query(IDVerificationRequest).filter(IDVerificationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    path = getattr(req, f"{slot}_url")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Document not found")

    return FileResponse(path)


@router.post("/{request_id}/approve")
async def approve_verification(
    request_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    note: str = "Identity documents verified and approved.",
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Admin/Agent approves an ID verification request."""
    req = db.query(IDVerificationRequest).filter(IDVerificationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.status}")

    req.status = "approved"
    req.reviewer_id = admin.id
    req.reviewer_note = note
    req.reviewed_at = datetime.utcnow()

    user = db.query(User).filter(User.id == req.user_id).first()
    if user:
        user.id_verified = True
        user.id_verified_at = datetime.utcnow()
        user.trust_score = min(100, user.trust_score + 15)

    audit = SystemAudit(
        admin_id=admin.id,
        action="ID_VERIFY_APPROVED",
        target_type="USER",
        target_id=req.user_id,
        note=note,
    )
    db.add(audit)
    db.commit()

    if user:
        background_tasks.add_task(
            NotificationService._notify_both_channels,
            user.phone_number,
            f"✅ *Identity Verified*\n\n"
            f"Hello {user.full_name}, your ID documents have been reviewed and approved.\n\n"
            f"🏆 Trust Score +15 — you now have full platform access.\n\n"
            f"Thank you for verifying with AgriTrust!"
        )

    return {"status": "approved", "request_id": str(request_id)}


@router.post("/{request_id}/reject")
async def reject_verification(
    request_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    note: str = Form(..., description="Reason for rejection — sent to user"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Admin/Agent rejects an ID verification request with a reason."""
    req = db.query(IDVerificationRequest).filter(IDVerificationRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.status}")

    req.status = "rejected"
    req.reviewer_id = admin.id
    req.reviewer_note = note
    req.reviewed_at = datetime.utcnow()

    user = db.query(User).filter(User.id == req.user_id).first()

    audit = SystemAudit(
        admin_id=admin.id,
        action="ID_VERIFY_REJECTED",
        target_type="USER",
        target_id=req.user_id,
        note=note,
    )
    db.add(audit)
    db.commit()

    if user:
        background_tasks.add_task(
            NotificationService._notify_both_channels,
            user.phone_number,
            f"❌ *Verification Rejected*\n\n"
            f"Hello {user.full_name}, your ID verification was not approved.\n\n"
            f"*Reason:* {note}\n\n"
            f"Please resubmit with clearer documents. Reply 'verify' to try again."
        )

    return {"status": "rejected", "request_id": str(request_id)}
