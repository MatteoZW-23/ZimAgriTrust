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
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.api.deps import get_db, get_current_user, require_roles
from app.models import (
    User, UserRole, SystemAudit,
    DocumentVerificationRecord, UserVerificationSummary,
    VerificationStatus, DocumentType
)
from app.services.notification_service import NotificationService
from app.core.config import settings

router = APIRouter()

# For backwards compatibility with migration scripts
IDVerificationRequest = DocumentVerificationRecord

UPLOAD_DIR = settings.SECURE_UPLOAD_DIR if hasattr(settings, "SECURE_UPLOAD_DIR") else "uploads/id_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE_MB = 5

# Magic bytes for deep file type validation
MAGIC_BYTES = {
    b'\xff\xd8\xff': "image/jpeg",
    b'\x89PNG\r\n\x1a\n': "image/png",
    b'RIFF': "image/webp",  # RIFF....WEBP
    b'%PDF': "application/pdf",
}


def _validate_file_magic(file: UploadFile) -> str:
    """Validate actual file content via magic bytes to prevent extension spoofing."""
    header = file.file.read(16)
    file.file.seek(0)
    for magic, mime in MAGIC_BYTES.items():
        if header.startswith(magic):
            # WebP has secondary check
            if mime == "image/webp" and b"WEBP" not in header[:12]:
                continue
            return mime
    return ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _update_user_verification_summary(db: Session, user_id: uuid.UUID):
    """Update UserVerificationSummary based on the user's verification records."""
    # Get all verification records for this user
    records = db.query(DocumentVerificationRecord).filter(
        DocumentVerificationRecord.user_id == user_id
    ).all()
    
    if not records:
        return
        
    summary = db.query(UserVerificationSummary).filter(
        UserVerificationSummary.user_id == user_id
    ).first()
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
        
    if not summary:
        summary = UserVerificationSummary(
            user_id=user_id,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            overall_status=VerificationStatus.PENDING_ADMIN,
            verification_level=0,
        )
        db.add(summary)
        
    # Check if identity is approved (National ID or Passport)
    identity_approved = any(
        r.document_type in (DocumentType.NATIONAL_ID, DocumentType.PASSPORT) and r.status == VerificationStatus.APPROVED
        for r in records
    )
    
    if identity_approved:
        summary.identity_status = VerificationStatus.APPROVED
        summary.identity_verified_at = datetime.now(timezone.utc)
        # Find which document was approved
        approved_doc = next(
            (r for r in records if r.document_type in (DocumentType.NATIONAL_ID, DocumentType.PASSPORT) and r.status == VerificationStatus.APPROVED),
            None
        )
        if approved_doc:
            summary.identity_document_type = approved_doc.document_type.value
            
    # Set verification level based on count of approved documents
    approved_count = sum(1 for r in records if r.status == VerificationStatus.APPROVED)
    summary.verification_level = min(5, approved_count)
    
    # Determine overall status
    if all(r.status == VerificationStatus.APPROVED for r in records):
        summary.overall_status = VerificationStatus.APPROVED
    elif any(r.status == VerificationStatus.REJECTED for r in records):
        summary.overall_status = VerificationStatus.REJECTED
    else:
        summary.overall_status = VerificationStatus.PENDING_ADMIN
        
    # Update user permissions
    summary.can_list_products = identity_approved
    summary.can_make_purchases = identity_approved
    summary.can_receive_payments = identity_approved
    summary.can_access_loans = summary.verification_level >= 3
    summary.can_use_platform_services = identity_approved
    
    summary.updated_at = datetime.now(timezone.utc)


def _save_file(file: UploadFile, user_id: str, slot: str) -> str:
    """Save uploaded file with deep validation (magic bytes, extension, size)."""
    if not file.content_type or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Use JPEG, PNG, WebP or PDF.")

    # Deep magic bytes validation prevents extension spoofing
    detected = _validate_file_magic(file)
    if detected != file.content_type:
        raise HTTPException(status_code=400, detail="File content does not match declared type. Possible spoofing attempt.")

    # Validate extension matches content type
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}
    expected_ext = ext_map.get(file.content_type, "bin")
    actual_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if actual_ext != expected_ext:
        raise HTTPException(status_code=400, detail=f"File extension .{actual_ext} does not match content type.")

    # Check filename for path traversal / null bytes
    safe_name = os.path.basename(file.filename)
    if "\x00" in safe_name or ".." in safe_name or "/" in safe_name or "\\" in safe_name:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    filename = f"{user_id}_{slot}_{uuid.uuid4().hex[:16]}.{expected_ext}"
    dest = os.path.join(UPLOAD_DIR, filename)

    # Ensure destination is within UPLOAD_DIR (path traversal defense)
    real_dest = os.path.realpath(dest)
    real_upload = os.path.realpath(UPLOAD_DIR)
    if not real_dest.startswith(real_upload):
        raise HTTPException(status_code=400, detail="Invalid upload path.")

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
    existing = db.query(DocumentVerificationRecord).filter(
        DocumentVerificationRecord.user_id == current_user.id,
        DocumentVerificationRecord.status == VerificationStatus.PENDING_ADMIN
    ).first()
    if existing:
        db.delete(existing)
        db.flush()

    front_path = _save_file(front, uid, "front")
    back_path = _save_file(back, uid, "back") if back and back.filename else None
    selfie_path = _save_file(selfie, uid, "selfie") if selfie and selfie.filename else None

    req = DocumentVerificationRecord(
        user_id=current_user.id,
        document_type=DocumentType.NATIONAL_ID,
        document_label="National ID",
        file_url=front_path,
        back_file_url=back_path,
        selfie_file_url=selfie_path,
        document_number=national_id_number,
        status=VerificationStatus.PENDING_ADMIN,
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
        db.query(DocumentVerificationRecord)
        .filter(DocumentVerificationRecord.user_id == current_user.id)
        .order_by(DocumentVerificationRecord.submitted_at.desc())
        .first()
    )
    if not req:
        return {"status": "not_submitted", "id_verified": current_user.id_verified}

    # Map status to legacy strings for API compatibility
    status_str = "pending"
    if req.status == VerificationStatus.APPROVED:
        status_str = "approved"
    elif req.status == VerificationStatus.REJECTED:
        status_str = "rejected"

    return {
        "request_id": str(req.id),
        "status": status_str,
        "submitted_at": req.submitted_at,
        "reviewed_at": req.admin_reviewed_at or req.agent_reviewed_at,
        "reviewer_note": req.admin_notes or req.agent_notes,
        "id_verified": current_user.id_verified,
        "has_front": bool(req.file_url),
        "has_back": bool(req.back_file_url),
        "has_selfie": bool(req.selfie_file_url),
    }


@router.get("/queue", dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.AGENT))])
def get_verification_queue(
    status: str = "pending",
    db: Session = Depends(get_db),
):
    """Admin/Agent: list all verification requests by status."""
    # Map incoming status to corresponding new VerificationStatus enums
    if status == "pending":
        statuses = [VerificationStatus.PENDING_ADMIN, VerificationStatus.PENDING_AGENT]
    elif status == "approved":
        statuses = [VerificationStatus.APPROVED]
    elif status == "rejected":
        statuses = [VerificationStatus.REJECTED]
    else:
        try:
            statuses = [VerificationStatus(status)]
        except ValueError:
            statuses = []

    requests = (
        db.query(DocumentVerificationRecord)
        .filter(DocumentVerificationRecord.status.in_(statuses))
        .order_by(DocumentVerificationRecord.submitted_at.asc())
        .all()
    )

    result = []
    for r in requests:
        user = db.query(User).filter(User.id == r.user_id).first()
        
        status_str = "pending"
        if r.status == VerificationStatus.APPROVED:
            status_str = "approved"
        elif r.status == VerificationStatus.REJECTED:
            status_str = "rejected"

        result.append({
            "request_id": str(r.id),
            "user_id": str(r.user_id),
            "user_name": user.full_name if user else "Unknown",
            "user_phone": user.phone_number if user else "",
            "user_role": user.role.value if user else "",
            "national_id_number": r.document_number,
            "status": status_str,
            "submitted_at": r.submitted_at,
            "reviewed_at": r.admin_reviewed_at or r.agent_reviewed_at,
            "reviewer_note": r.admin_notes or r.agent_notes,
            "has_front": bool(r.file_url),
            "has_back": bool(r.back_file_url),
            "has_selfie": bool(r.selfie_file_url),
            "front_url": f"/api/v1/verification/document/{r.id}/front" if r.file_url else None,
            "back_url": f"/api/v1/verification/document/{r.id}/back" if r.back_file_url else None,
            "selfie_url": f"/api/v1/verification/document/{r.id}/selfie" if r.selfie_file_url else None,
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

    req = db.query(DocumentVerificationRecord).filter(DocumentVerificationRecord.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")

    if slot == "front":
        path = req.file_url
    elif slot == "back":
        path = req.back_file_url
    else:
        path = req.selfie_file_url

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
    req = db.query(DocumentVerificationRecord).filter(DocumentVerificationRecord.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in (VerificationStatus.PENDING_ADMIN, VerificationStatus.PENDING_AGENT, VerificationStatus.UNDER_REVIEW):
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    req.status = VerificationStatus.APPROVED
    
    # Record reviewer based on role
    if admin.role == UserRole.AGENT:
        req.agent_reviewer_id = admin.id
        req.agent_notes = note
        req.agent_reviewed_at = datetime.now(timezone.utc)
        req.agent_decision = "approve"
    else:
        req.admin_reviewer_id = admin.id
        req.admin_notes = note
        req.admin_reviewed_at = datetime.now(timezone.utc)
        req.admin_decision = "approve"

    user = db.query(User).filter(User.id == req.user_id).first()
    if user:
        user.id_verified = True
        user.id_verified_at = datetime.now(timezone.utc)
        user.trust_score = min(100, user.trust_score + 15)

    _update_user_verification_summary(db, req.user_id)

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
            f"Thank you for verifying with ZimAgritrust!"
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
    req = db.query(DocumentVerificationRecord).filter(DocumentVerificationRecord.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.status not in (VerificationStatus.PENDING_ADMIN, VerificationStatus.PENDING_AGENT, VerificationStatus.UNDER_REVIEW):
        raise HTTPException(status_code=400, detail=f"Request is already {req.status.value}")

    req.status = VerificationStatus.REJECTED
    
    # Record reviewer based on role
    if admin.role == UserRole.AGENT:
        req.agent_reviewer_id = admin.id
        req.agent_notes = note
        req.agent_reviewed_at = datetime.now(timezone.utc)
        req.agent_decision = "reject"
    else:
        req.admin_reviewer_id = admin.id
        req.admin_notes = note
        req.admin_reviewed_at = datetime.now(timezone.utc)
        req.admin_decision = "reject"

    user = db.query(User).filter(User.id == req.user_id).first()

    _update_user_verification_summary(db, req.user_id)

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
