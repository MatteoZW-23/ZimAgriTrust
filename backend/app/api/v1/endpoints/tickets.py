import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.ticket import SupportTicket, TicketStatus
from app.models.user import User, UserRole
from app.services.notification_service import NotificationService

router = APIRouter()


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5)


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    resolution_note: str | None = None
    satisfaction_rating: int | None = Field(default=None, ge=1, le=5)


@router.post("")
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = SupportTicket(created_by=current_user.id, subject=payload.subject, description=payload.description, status=TicketStatus.OPEN)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    try:
        asyncio.run(NotificationService.dispatch_event(db, current_user, "ticket_created", priority="important", TICKET_REF=str(ticket.id)))
    except RuntimeError:
        asyncio.get_event_loop().create_task(NotificationService.dispatch_event(db, current_user, "ticket_created", priority="important", TICKET_REF=str(ticket.id)))
    return {"id": str(ticket.id), "status": ticket.status.value}


@router.post("/{ticket_id}/assign")
def assign_ticket(ticket_id: uuid.UUID, assignee_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPPORT_ADMIN, UserRole.SUPER_ADMIN))):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    ticket.assigned_to = assignee_id
    ticket.status = TicketStatus.ASSIGNED
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    creator = db.query(User).filter(User.id == ticket.created_by).first()
    if creator:
        try:
            asyncio.run(NotificationService.dispatch_event(db, creator, "ticket_assigned", priority="informational", TICKET_REF=str(ticket.id)))
        except RuntimeError:
            asyncio.get_event_loop().create_task(NotificationService.dispatch_event(db, creator, "ticket_assigned", priority="informational", TICKET_REF=str(ticket.id)))
    return {"id": str(ticket.id), "status": ticket.status.value}

