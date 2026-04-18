import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.api.deps import get_db, require_roles
from app.models.dispute import Dispute, DisputeStatus
from app.models.listing import Listing, ListingStatus, Offer
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, Order
from app.schemas.admin import AdminOverviewResponse, ListingReviewResponse, RiskWatchResponse
from app.schemas.auth import UserResponse, UserRegister
from app.schemas.listing import ListingResponse
from app.models.system_audit import SystemAudit

router = APIRouter()


@router.get("/overview", response_model=AdminOverviewResponse)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    total_vol = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    platform_rev = total_vol * 0.01  # 1% platform fee logic

    return {
        "users": db.query(User).count(),
        "farmers": db.query(User).filter(User.role == UserRole.FARMER).count(),
        "buyers": db.query(User).filter(User.role == UserRole.BUYER).count(),
        "agents": db.query(User).filter(User.role == UserRole.AGENT).count(),
        "listings": db.query(Listing).count(),
        "total_volume": total_vol,
        "platform_revenue": platform_rev,
        "pending_verifications": db.query(Listing).filter(Listing.verification_status == "PENDING").count(),
        "suspended_listings": db.query(Listing).filter(Listing.status == ListingStatus.SUSPENDED).count(),
        "open_disputes": db.query(Dispute).filter(Dispute.status != DisputeStatus.RESOLVED).count(),
        "resolved_disputes": db.query(Dispute).filter(Dispute.status == DisputeStatus.RESOLVED).count(),
        "system_health": {
            "api": "OPERATIONAL",
            "database": "OPERATIONAL",
            "ecocash": "CONNECTED",
            "ussd": "ACTIVE",
            "Market Analytics": "OPERATIONAL"
        }
    }


@router.get("/listings/review-queue", response_model=list[ListingReviewResponse])
def review_queue(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> list[ListingReviewResponse]:
    listings = (
        db.query(Listing)
        .options(joinedload(Listing.seller), joinedload(Listing.offers))
        .filter(Listing.verification_status.in_(["pending", "PENDING"]))
        .order_by(Listing.created_at.desc())
        .all()
    )
    return [
        ListingReviewResponse(
            id=listing.id,
            farmer_id=listing.seller_id,
            farmer_name=listing.seller.full_name if listing.seller else "N/A",
            farmer_phone=listing.seller.phone_number if listing.seller else "N/A",
            product_type=listing.product_type or "Unknown",
            quantity=listing.quantity or 0,
            grade=listing.grade or "N/A",
            location=f"{listing.location_province or 'N/A'}, {listing.location_district or 'N/A'}",
            price_per_unit=listing.price_per_unit or 0.0,
            status=listing.status.value if hasattr(listing.status, 'value') else str(listing.status),
            verification_status=listing.verification_status or "PENDING",
            notes=listing.notes,
            offer_count=len(listing.offers) if listing.offers else 0
        )
        for listing in listings
    ]


@router.get("/risk-watch", response_model=list[RiskWatchResponse])
def risk_watch(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> list[RiskWatchResponse]:
    users = (
        db.query(User)
        .filter(User.role.in_([UserRole.FARMER, UserRole.BUYER]))
        .order_by(User.trust_score.asc())
        .limit(10)
        .all()
    )
    response_data = []
    for user in users:
        flags = []
        if user.trust_score < 40: flags.append("⚠️ Low Fulfillment Rate")
        if not user.province: flags.append("🛂 Unverified Identity")

        response_data.append(RiskWatchResponse(
            id=user.id,
            full_name=user.full_name,
            phone_number=user.phone_number,
            role=user.role.value if hasattr(user.role, 'value') else str(user.role),
            trust_score=user.trust_score,
            risk_score=user.risk_score if hasattr(user, 'risk_score') else 0.0,
            is_suspended=user.is_suspended,
            status=user.status.value if hasattr(user.status, 'value') else str(user.status),
            flags=flags,
        ))
    return response_data


@router.post("/listings/{listing_id}/verify", response_model=ListingResponse)
def verify_listing(
    listing_id: uuid.UUID,
    approved: bool = True,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
) -> Listing:
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.verification_status = "APPROVED" if approved else "REJECTED"
    if not approved:
        listing.status = ListingStatus.SUSPENDED
    db.commit()
    db.refresh(listing)
    return listing


@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Returns a frequency distribution of trust scores for system-wide health visualization.
    """
    # 10 buckets of 10 points each (0-10, 10-20, ..., 90-100)
    distribution = [0] * 10
    total_users = db.query(User).count()
    if total_users == 0:
        return distribution
    
    # We iterate and count for demo/enterprise scale normally we'd use a grouped query
    users = db.query(User.trust_score).all()
    for (score,) in users:
        safe_score = score if score is not None else 0
        idx = min(9, int(safe_score // 10))
        distribution[idx] += 1
    
    # Return as percentages for better chart scaling
    if total_users == 0:
        return [0] * 10
    return [round((count / total_users) * 100, 1) for count in distribution]

@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: uuid.UUID,
    target_status: str,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = target_status.lower()
    user.is_suspended = (target_status.upper() in ["SUSPENDED", "CLOSED", "FLAGGED"])
    
    # Persistent Governance Audit
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_STATUS_UPDATE",
        target_type="USER",
        target_id=user.id,
        note=reason,
        details={"new_status": target_status}
    )
    db.add(audit)
    db.commit()
    return {"message": "User status adjusted", "audit_ref": str(audit.id)}


@router.post("/users/{user_id}/trust")
def adjust_trust_score(
    user_id: uuid.UUID,
    adjustment: float,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.trust_score = max(0, min(100, user.trust_score + adjustment))
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="TRUST_SCORE_ADJUST",
        target_type="USER",
        target_id=user.id,
        note=reason,
        details={"adjustment": adjustment}
    )
    db.add(audit)
    db.commit()
    return {"new_score": user.trust_score}


@router.post("/escrow/{order_id}/force-release")
def force_escrow_release(
    order_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "DELIVERED" 
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="ESCROW_FORCE_RELEASE",
        target_type="ORDER",
        target_id=order.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"status": "Escrow released by Admin", "audit_ref": str(audit.id)}


@router.post("/escrow/{order_id}/force-refund")
def force_escrow_refund(
    order_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = "REFUNDED"
    
    audit = SystemAudit(
        admin_id=admin.id,
        action="ESCROW_FORCE_REFUND",
        target_type="ORDER",
        target_id=order.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"status": "Escrow refunded by Admin", "audit_ref": str(audit.id)}


@router.get("/audit-log")
def get_audit_log(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    logs = db.query(SystemAudit).order_by(SystemAudit.created_at.desc()).limit(100).all()
    return [
        {
            "ts": log.created_at.strftime("%Y-%m-%d %H:%M"), 
            "admin": log.admin.full_name if hasattr(log, 'admin') and log.admin else "System", 
            "action": log.action, 
            "target": str(log.target_id) if log.target_id else "Global", 
            "note": log.note
        }
        for log in logs
    ]


@router.get("/revenue-stats")
def revenue_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    total_revenue = db.query(func.sum(Transaction.amount)).filter(Transaction.type == TransactionType.FEE).scalar() or 0.0
    active_escrow = db.query(func.sum(Transaction.amount)).filter(Transaction.type == TransactionType.ESCROW_HOLD).scalar() or 0.0
    return {
        "total_revenue": total_revenue,
        "active_escrow": active_escrow
    }


from app.models.listing import Listing, ListingStatus, Offer
from app.models.transaction import Transaction, TransactionType, Order

@router.get("/activities")
def get_all_activities(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """
    Returns a unified set of listings, offers, and deals для the Command Center HUB.
    """
    listings = db.query(Listing).options(joinedload(Listing.seller)).order_by(Listing.created_at.desc()).limit(20).all()
    offers = db.query(Offer).options(joinedload(Offer.buyer), joinedload(Offer.listing)).order_by(Offer.created_at.desc()).limit(20).all()
    orders = db.query(Order).options(joinedload(Order.buyer), joinedload(Order.seller), joinedload(Order.listing)).order_by(Order.created_at.desc()).limit(20).all()

    return {
        "listings": [
            {
                "id": str(l.id), "product": l.product_type, "qty": l.quantity, 
                "price": l.price_per_unit, "seller": l.seller.full_name, "status": l.status
            } for l in listings
        ],
        "offers": [
            {
                "id": str(o.id), "product": o.listing.product_type, "qty": o.quantity,
                "offered_price": o.offered_price, "buyer": o.buyer.full_name, "status": o.status
            } for o in offers
        ],
        "deals": [
            {
                "id": str(d.id), "deal_no": d.order_number, "product": d.listing.product_type,
                "amount": d.total_amount, "status": d.status, "buyer": d.buyer.full_name, "seller": d.seller.full_name
            } for d in orders
        ]
    }

@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.AGENT, UserRole.ADMIN)),
):
    """List all users for the operational directory."""
    return db.query(User).all()

@router.post("/enroll-user", response_model=UserResponse)
def enroll_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Manually enroll a user into the platform governor."""
    from app.services.auth_service import register_user
    # Double check if exists
    existing = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Identity already registered")
    return register_user(db, payload)

@router.delete("/users/{user_id}")
def delete_user(
    user_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Purge a user record for security or compliance protocols."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit before delete
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_PURGE",
        target_type="USER",
        target_id=user_id,
        note=reason
    )
    db.add(audit)
    db.delete(user)
    db.commit()
    return {"status": "User wiped from national database"}

@router.post("/users/{user_id}/verify")
def verify_user_identity(
    user_id: uuid.UUID,
    reason: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Authenticate and verify a user's national identity credentials."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.id_verified = True
    audit = SystemAudit(
        admin_id=admin.id,
        action="USER_VERIFY",
        target_type="USER",
        target_id=user.id,
        note=reason
    )
    db.add(audit)
    db.commit()
    return {"message": "Identity Verified"}

@router.get("/agents/stats")
def agent_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.AGENT)),
):
    """Returns granular performance metrics for field agents."""
    from app.models.agent import Agent
    agents = db.query(Agent).all()
    # If no extended agent profiles exist, return basic user agent data
    if not agents:
        basic_agents = db.query(User).filter(User.role == UserRole.AGENT).all()
        return [
            {
                "id": str(u.id), "full_name": u.full_name, "region": u.province or "Central",
                "resolved": 0, "rating": 5.0
            } for u in basic_agents
        ]

    return [
        {
            "id": str(a.user_id),
            "full_name": a.user.full_name if a.user else "Anonymous Agent",
            "region": a.user.province if a.user else "Verified Zone",
            "resolved": len(a.assignments) if a.assignments else 0,
            "rating": 4.9 # Demo value
        }
        for a in agents
    ]

from app.services.sync_service import sync_system_data

@router.post("/sync-platform")
def sync_platform(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Synchronizes the platform with fresh demo data.
    """
    result = sync_system_data(db)
    return result
