from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction, TransactionType, Order
from app.models.listing import Listing

class AdminRevenueService:
    """
    Financial engine for the ZimAgritrust Founders/Admins.
    Aggregates all system-level inflows including royalties, boosts, and surcharges.
    """

    @staticmethod
    def get_national_revenue_summary(db: Session):
        """
        Calculates the 3 main revenue streams for platform owners.
        """
        # 1. Platform Royalties (Allocated 0.5% from settlements)
        royalties = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.FEE
        ).scalar() or 0.0

        # 2. Premium Listing Revenue (Boosts)
        boost_revenue = db.query(func.sum(Listing.boost_fee)).filter(
            Listing.is_boosted == True
        ).scalar() or 0.0

        # 3. Gross Merchandise Volume (GMV) - For context
        gmv = db.query(func.sum(Order.total_amount)).scalar() or 0.0

        return {
            "total_earnings": royalties + boost_revenue,
            "stream_royalties": royalties,
            "stream_boosts": boost_revenue,
            "gross_volume": gmv,
            "platform_yield_pct": ((royalties + boost_revenue) / gmv * 100) if gmv > 0 else 0.0
        }

    @staticmethod
    def record_boost_payment(db: Session, listing: Listing, amount: float = 1.0):
        """
        Processes a visibility boost purchase ($1 standard premium)
        """
        listing.is_boosted = True
        listing.boost_fee = amount
        
        # Log the revenue event
        # (This would be another transaction entry in a production environment)
        db.commit()
