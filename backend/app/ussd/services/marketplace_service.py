"""USSD Marketplace Service."""
from __future__ import annotations
from typing import Any, List
from sqlalchemy import desc

class USSDMarketplaceService:
    @staticmethod
    async def get_active_listings(db: Any, limit: int = 5) -> List[Any]:
        from app.models.listing import Listing, ListingStatus
        return db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE, Listing.quantity > 0).order_by(desc(Listing.created_at)).limit(limit).all()
    
    @staticmethod
    async def get_listing(db: Any, listing_id: str) -> Optional[Any]:
        from app.models.listing import Listing
        return db.query(Listing).filter(Listing.id == listing_id).first()
    
    @staticmethod
    async def create_listing(db: Any, seller_id: str, product: str, qty: float, price: float, province: str) -> Any:
        from app.models.listing import Listing, ListingStatus, Sector
        import uuid
        listing = Listing(
            id=uuid.uuid4(),
            seller_id=seller_id,
            sector=Sector.CROPS,
            product_type=product,
            quantity=qty,
            price_per_unit=price,
            location_province=province,
            status=ListingStatus.ACTIVE,
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        return listing

ussd_marketplace = USSDMarketplaceService()
