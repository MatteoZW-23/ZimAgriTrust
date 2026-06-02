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


class TicketReply(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


def _dispatch_notification(coro) -> None:
    try:
        asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(coro)


def _notify_ticket_event(db: Session, user: User | None, event_key: str, ticket_id: uuid.UUID, priority: str) -> None:
    if not user:
        return
    _dispatch_notification(
        NotificationService.dispatch_event(
            db,
            user,
            event_key,
            priority=priority,
            TICKET_REF=str(ticket_id),
        )
    )


@router.post("")
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = SupportTicket(created_by=current_user.id, subject=payload.subject, description=payload.description, status=TicketStatus.OPEN)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    _notify_ticket_event(db, current_user, "ticket_created", ticket.id, "important")
    return {"id": str(ticket.id), "status": ticket.status.value}


@router.get("")
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(SupportTicket)
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPPORT_ADMIN, UserRole.SUPER_ADMIN}:
        query = query.filter(SupportTicket.created_by == current_user.id)
    tickets = query.order_by(SupportTicket.updated_at.desc().nullslast(), SupportTicket.created_at.desc()).all()
    return [
        {
            "id": str(ticket.id),
            "created_by": str(ticket.created_by),
            "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
            "subject": ticket.subject,
            "description": ticket.description,
            "status": ticket.status.value,
            "resolution_note": ticket.resolution_note,
            "satisfaction_rating": ticket.satisfaction_rating,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        }
        for ticket in tickets
    ]


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPPORT_ADMIN, UserRole.SUPER_ADMIN} and ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this ticket")
    return {
        "id": str(ticket.id),
        "created_by": str(ticket.created_by),
        "assigned_to": str(ticket.assigned_to) if ticket.assigned_to else None,
        "subject": ticket.subject,
        "description": ticket.description,
        "status": ticket.status.value,
        "resolution_note": ticket.resolution_note,
        "satisfaction_rating": ticket.satisfaction_rating,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


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
    _notify_ticket_event(db, creator, "ticket_assigned", ticket.id, "informational")
    return {"id": str(ticket.id), "status": ticket.status.value}


@router.post("/{ticket_id}/reply")
def reply_ticket(
    ticket_id: uuid.UUID,
    payload: TicketReply,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user.role not in {UserRole.ADMIN, UserRole.SUPPORT_ADMIN, UserRole.SUPER_ADMIN} and ticket.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to reply to this ticket")

    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] {current_user.role.value}: {payload.message.strip()}"
    existing_note = ticket.resolution_note or ""
    ticket.resolution_note = f"{existing_note}\n{entry}".strip()
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()

    creator = db.query(User).filter(User.id == ticket.created_by).first()
    assignee = db.query(User).filter(User.id == ticket.assigned_to).first() if ticket.assigned_to else None
    recipients = []
    if creator:
        recipients.append(creator)
    if assignee and (not creator or assignee.id != creator.id):
        recipients.append(assignee)
    for recipient in recipients:
        _notify_ticket_event(db, recipient, "ticket_replied", ticket.id, "informational")

    return {"id": str(ticket.id), "status": ticket.status.value, "resolution_note": ticket.resolution_note}


@router.patch("/{ticket_id}")
def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    is_admin = current_user.role in {UserRole.ADMIN, UserRole.SUPPORT_ADMIN, UserRole.SUPER_ADMIN}
    is_owner = ticket.created_by == current_user.id
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Not authorized to update this ticket")

    creator = db.query(User).filter(User.id == ticket.created_by).first()
    assignee = db.query(User).filter(User.id == ticket.assigned_to).first() if ticket.assigned_to else None

    if payload.resolution_note is not None:
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only support staff can set resolution notes")
        ticket.resolution_note = payload.resolution_note.strip()

    if payload.status is not None:
        if payload.status in {TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED} and not is_admin:
            raise HTTPException(status_code=403, detail="Only support staff can set this ticket status")
        if payload.status == TicketStatus.CLOSED and not (is_admin or is_owner):
            raise HTTPException(status_code=403, detail="Not authorized to close this ticket")
        ticket.status = payload.status

    if payload.satisfaction_rating is not None:
        if not is_owner:
            raise HTTPException(status_code=403, detail="Only the ticket owner can submit a satisfaction rating")
        if ticket.status not in {TicketStatus.RESOLVED, TicketStatus.CLOSED}:
            raise HTTPException(status_code=400, detail="Satisfaction rating requires a resolved or closed ticket")
        ticket.satisfaction_rating = payload.satisfaction_rating

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)

    if payload.status == TicketStatus.RESOLVED:
        _notify_ticket_event(db, creator, "ticket_resolved", ticket.id, "important")
        _notify_ticket_event(db, creator, "ticket_satisfaction_request", ticket.id, "informational")
    if payload.status == TicketStatus.CLOSED:
        _notify_ticket_event(db, creator, "ticket_closed", ticket.id, "informational")
    if payload.status == TicketStatus.RESOLVED and assignee and (not creator or assignee.id != creator.id):
        _notify_ticket_event(db, assignee, "ticket_resolved", ticket.id, "informational")

    return {
        "id": str(ticket.id),
        "status": ticket.status.value,
        "resolution_note": ticket.resolution_note,
        "satisfaction_rating": ticket.satisfaction_rating,
    }
