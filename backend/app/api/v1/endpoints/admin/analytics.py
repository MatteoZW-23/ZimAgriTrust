from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db, require_roles
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType, Order
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
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
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
