import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.listing import TradeSession, TradeMessage, Listing
from app.models.user import User, UserRole
from app.schemas.listing import TradeMessageCreate, TradeMessageResponse, TradeSessionResponse
from app.services.pii_masker import pii_masker

router = APIRouter()

@router.post("/{listing_id}/start", response_model=TradeSessionResponse)
def start_trade_session(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    if listing.seller_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot start a trade with yourself")

    # Check if session already exists
    session = db.query(TradeSession).filter(
        TradeSession.listing_id == listing_id,
        TradeSession.buyer_id == current_user.id
    ).first()

    if not session:
        session = TradeSession(
            listing_id=listing_id,
            buyer_id=current_user.id,
            seller_id=listing.seller_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session

@router.get("/sessions", response_model=List[TradeSessionResponse])
def list_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(TradeSession).filter(
        (TradeSession.buyer_id == current_user.id) | 
        (TradeSession.seller_id == current_user.id)
    ).all()

@router.post("/{session_id}/messages", response_model=TradeMessageResponse)
def send_trade_message(
    session_id: uuid.UUID,
    payload: TradeMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(TradeSession).filter(TradeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if current_user.id not in [session.buyer_id, session.seller_id] and current_user.role not in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized to participate in this trade")

    # Security Masking
    masked_content, was_masked = pii_masker.mask_content(payload.content)
    
    message = TradeMessage(
        session_id=session_id,
        sender_id=current_user.id,
        content=masked_content,
        is_formal_offer=payload.is_formal_offer,
        offer_payload=payload.offer_payload
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # If PII was detected, inject a system warning
    if was_masked:
        warning = TradeMessage(
            session_id=session_id,
            sender_id=uuid.UUID(int=0), # System ID
            content=pii_masker.get_security_warning()
        )
        db.add(warning)
        db.commit()

    return message

@router.get("/{session_id}/messages", response_model=List[TradeMessageResponse])
def get_session_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(TradeSession).filter(TradeSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if current_user.id in [session.buyer_id, session.seller_id]:
        return session.messages
        
    if current_user.role in {UserRole.ADMIN, UserRole.SUPER_ADMIN}:
        return session.messages

    if current_user.role == UserRole.AGENT:
        # AGENT ACCESS PROTOCOL (Module 4):
        # Access is only granted if there is an active dispute for the listing
        # and the agent is assigned to investigate it.
        from app.models.dispute import Dispute, DisputeStatus
        from app.models.transaction import Order
        dispute = db.query(Dispute).join(Order).filter(
            Order.listing_id == session.listing_id,
            Dispute.agent_assigned == current_user.id,
            Dispute.status != DisputeStatus.RESOLVED
        ).first()
        
        if dispute:
            return session.messages
            
    raise HTTPException(status_code=403, detail="Negotiation Hub Privacy: Access restricted to parties or assigned dispute mediators.")
