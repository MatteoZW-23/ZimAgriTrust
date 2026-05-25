from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, Order, OrderStatus
from app.models.listing import Listing
from app.schemas.admin import UserGrowthData, ProductTrend, GeoDistribution

router = APIRouter()

@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Returns a frequency distribution of trust scores for system-wide health visualization.
    """
    distribution = [0] * 10
    total_users = db.query(User).count()
    if total_users == 0:
        return distribution
    
    users = db.query(User.trust_score).all()
    for (score,) in users:
        safe_score = score if score is not None else 0
        idx = min(9, int(safe_score // 10))
        distribution[idx] += 1
    
    return [round((count / total_users) * 100, 1) for count in distribution]

@router.get("/revenue/national-summary")
def national_revenue_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Aggregation for the National Command Center Revenue Dashboard.
    """
    total_vol = db.query(func.sum(Order.total_amount)).scalar() or 0.0
    total_earnings = total_vol * 0.01 # 1% royalty
    
    return {
        "total_earnings": total_earnings,
        "stream_royalties": total_earnings * 0.8,
        "stream_boosts": total_earnings * 0.2,
        "gross_volume": total_vol,
        "platform_yield_pct": 1.0
    }

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

@router.get("/user-growth", response_model=list[UserGrowthData])
def get_user_growth(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 156: View active user growth.
    Aggregates user registrations over the last 30 days.
    """
    from datetime import datetime, timedelta, timezone
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    results = db.query(
        func.date(User.created_at).label("date"),
        func.count(User.id).label("count")
    ).filter(User.created_at >= thirty_days_ago).group_by(func.date(User.created_at)).order_by(func.date(User.created_at)).all()
    
    return [UserGrowthData(date=str(r.date), count=r.count) for r in results]

@router.get("/top-products", response_model=list[ProductTrend])
def get_top_products(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Function 163: Top selling crops.
    """
    from app.models.listing import Listing
    
    results = db.query(
        Listing.product_type.label("product"),
        func.sum(Order.total_amount).label("volume"),
        func.count(Order.id).label("order_count")
    ).join(Order, Order.listing_id == Listing.id).group_by(Listing.product_type).order_by(func.sum(Order.total_amount).desc()).limit(10).all()
    
    return [ProductTrend(product=r.product, volume=r.volume, order_count=r.order_count) for r in results]

@router.get("/geographic-distribution", response_model=list[GeoDistribution])
def get_geo_distribution(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Aggregates activity by province.
    """
    # Assuming User model has province
    results = db.query(
        User.province.label("province"),
        func.count(User.id).label("user_count"),
        func.sum(Order.total_amount).label("volume")
    ).join(Order, Order.buyer_id == User.id).group_by(User.province).all()
    
    return [GeoDistribution(province=r.province or "Other", user_count=r.user_count, volume=r.volume or 0.0) for r in results]


@router.get("/revenue-detailed")
def revenue_detailed(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN)),
):
    """
    Comprehensive revenue breakdown across all 10 platform streams.
    Derives values from existing Order, Transaction, and Listing tables.
    """
    # 1. Transaction Fees (platform_fee from completed orders)
    tx_fees = db.query(func.sum(Order.platform_fee)).filter(
        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED])
    ).scalar() or 0.0

    # 2. Escrow Fees (FEE-type transactions not tied to order completion)
    escrow_fees = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.FEE
    ).scalar() or 0.0

    # 3. Agent Commission (transport_commission treated as agent share proxy)
    agent_commission = db.query(func.sum(Order.transport_commission)).filter(
        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED])
    ).scalar() or 0.0

    # 4. Withdrawal Fees (1% assumed on WITHDRAWAL transactions)
    withdrawal_total = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.WITHDRAWAL
    ).scalar() or 0.0
    withdrawal_fees = round(withdrawal_total * 0.01, 2)

    # 5. Agent Registration (approximated via FEE transactions where amount == 10)
    agent_reg = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.FEE,
        Transaction.amount == 10.0
    ).scalar() or 0.0

    # 6. Premium Listing Revenue
    premium_listing = db.query(func.sum(Listing.boost_fee)).filter(
        Listing.is_boosted == True
    ).scalar() or 0.0

    # 7. Transport Commission (platform share from orders)
    transport_commission = db.query(func.sum(Order.transport_commission)).filter(
        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED])
    ).scalar() or 0.0

    # 8. Business Subscription (approximated as $50 recurring FEE transactions)
    business_sub = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.FEE,
        Transaction.amount == 50.0
    ).scalar() or 0.0

    # 9. Loan Origination (approximated from FEE transactions where amount == 15)
    loan_origination = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.FEE,
        Transaction.amount == 15.0
    ).scalar() or 0.0

    # 10. Late Payment Penalty (approximated from FEE transactions where amount == 2.5)
    late_penalty = db.query(func.sum(Transaction.amount)).filter(
        Transaction.type == TransactionType.FEE,
        Transaction.amount == 2.5
    ).scalar() or 0.0

    total_earnings = (
        tx_fees + escrow_fees + agent_commission + withdrawal_fees +
        agent_reg + premium_listing + transport_commission +
        business_sub + loan_origination + late_penalty
    )

    gmv = db.query(func.sum(Order.total_amount)).filter(
        Order.status.in_([OrderStatus.COMPLETED, OrderStatus.SETTLED])
    ).scalar() or 0.0

    return {
        "total_earnings": round(total_earnings, 2),
        "gross_volume": round(gmv, 2),
        "platform_yield_pct": round((total_earnings / gmv * 100), 2) if gmv > 0 else 0.0,
        "streams": {
            "transaction_fees": {
                "label": "Transaction Fees",
                "rate": "Varies 0.5–1.0%",
                "amount": round(tx_fees, 2),
                "payer": "Seller"
            },
            "escrow_fees": {
                "label": "Escrow Fees",
                "rate": "Included in platform fee",
                "amount": round(escrow_fees, 2),
                "payer": "Buyer"
            },
            "agent_commission": {
                "label": "Agent Commission",
                "rate": "From transport pool",
                "amount": round(agent_commission, 2),
                "payer": "Seller"
            },
            "withdrawal_fees": {
                "label": "Withdrawal Fees",
                "rate": "1%",
                "amount": round(withdrawal_fees, 2),
                "payer": "Any User"
            },
            "agent_registration": {
                "label": "Agent Registration",
                "rate": "$10 one-time",
                "amount": round(agent_reg, 2),
                "payer": "Applicant"
            },
            "premium_listing": {
                "label": "Premium Listing",
                "rate": "$2 per listing",
                "amount": round(premium_listing, 2),
                "payer": "Farmer"
            },
            "transport_commission": {
                "label": "Transport Commission",
                "rate": "10% from driver",
                "amount": round(transport_commission, 2),
                "payer": "Driver"
            },
            "business_subscription": {
                "label": "Business Subscription",
                "rate": "$50/month",
                "amount": round(business_sub, 2),
                "payer": "Business"
            },
            "loan_origination": {
                "label": "Loan Origination",
                "rate": "3%",
                "amount": round(loan_origination, 2),
                "payer": "Borrower"
            },
            "late_penalty": {
                "label": "Late Payment Penalty",
                "rate": "5%",
                "amount": round(late_penalty, 2),
                "payer": "Borrower"
            },
        }
    }
