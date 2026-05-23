from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.broadcast import BroadcastMessage, BroadcastStatus, BroadcastAudience
from app.schemas.broadcast import BroadcastCreate, BroadcastOut
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _process_broadcast_async(broadcast_id: uuid.UUID, db: Session):
    """
    Background task to actually dispatch the broadcast.
    This is a simplified version for now.
    """
    broadcast = db.query(BroadcastMessage).filter(BroadcastMessage.id == broadcast_id).first()
    if not broadcast or broadcast.status != BroadcastStatus.PENDING:
        return

    broadcast.status = BroadcastStatus.SENDING
    db.commit()

    # Determine recipients based on audience
    from app.models.user import User, UserRole
    query = db.query(User).filter(User.is_active == True)
    
    if broadcast.audience == BroadcastAudience.FARMERS:
        query = query.filter(User.role == UserRole.FARMER)
    elif broadcast.audience == BroadcastAudience.BUYERS:
        query = query.filter(User.role == UserRole.BUYER)
    elif broadcast.audience == BroadcastAudience.AGENTS:
        query = query.filter(User.role == UserRole.AGENT)
    elif broadcast.audience == BroadcastAudience.DRIVERS:
        query = query.filter(User.role == UserRole.DRIVER)
    elif broadcast.audience == BroadcastAudience.REGIONAL:
        if broadcast.audience_filter and "region" in broadcast.audience_filter:
            query = query.filter(User.province == broadcast.audience_filter["region"])

    recipients = query.all()
    broadcast.sent_count = len(recipients)
    
    for user in recipients:
        try:
            # Dispatch to selected channels
            if "sms" in broadcast.channels:
                NotificationService._send_sms(user.phone_number, broadcast.message)
            if "whatsapp" in broadcast.channels:
                await NotificationService._send_whatsapp(user.phone_number, broadcast.message)
            if "email" in broadcast.channels and user.email:
                await NotificationService._send_email(user.email, broadcast.subject or "ZimAgriTrust Broadcast", broadcast.message)
            
            broadcast.delivered_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast {broadcast_id} to {user.phone_number}: {e}")
            broadcast.failed_count += 1
    
    broadcast.status = BroadcastStatus.SENT
    broadcast.sent_at = datetime.utcnow()
    db.commit()


@router.post("", response_model=BroadcastOut, summary="Create + dispatch broadcast message")
async def create_broadcast(
    payload: BroadcastCreate,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    """
    Broadcasting is restricted to Super Admins and System Admins.
    """
    # Create the record
    broadcast = BroadcastMessage(
        subject=payload.subject,
        message=payload.message,
        audience=payload.audience,
        audience_filter=payload.audience_filter,
        channels=payload.channels,
        scheduled_for=payload.scheduled_for,
        status=BroadcastStatus.PENDING,
        created_by=None # actor.id is a UUID, but created_by expects int (AdminUser). 
                        # This is the conflict I noted earlier. 
                        # For now, I'll allow NULL or implement AdminUser login.
    )
    
    # Try to link to AdminUser if exists
    from app.models.admin import AdminUser
    admin = db.query(AdminUser).filter(AdminUser.email == actor.email).first()
    if admin:
        broadcast.created_by = admin.id

    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)

    if not payload.scheduled_for or payload.scheduled_for <= datetime.utcnow():
        background.add_task(_process_broadcast_async, broadcast.id, db)
    else:
        broadcast.status = BroadcastStatus.SCHEDULED
        db.commit()

    return broadcast


@router.get("/history", response_model=List[BroadcastOut])
def get_broadcast_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)),
):
    return db.query(BroadcastMessage).order_by(BroadcastMessage.created_at.desc()).limit(limit).all()
