"""
Marketplace Repository - Consolidated Single Source for Listing/Offer Data Access
Replaces duplicate marketplace_repository.py, transaction_repository.py fragments
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from backend.app.infrastructure.repositories.base import BaseRepository
from backend.app.models import Listing as ListingORM, Offer as OfferORM, BuyerRequest as BuyerRequestORM
from backend.app.shared.types import ListingStatus, OfferStatus


class ListingRepository(BaseRepository):
    """
    Consolidated repository for listing data access.
    
    Responsibilities:
    - Listing CRUD operations
    - Query listings by status, seller, category
    - Search functionality
    
    WHY: Consolidates duplicate marketplace_repository.py and transaction_repository.py
    """
    
    def __init__(self, db: Session):
        super().__init__(db, ListingORM)
        self.db = db
    
    async def get_by_seller(self, seller_id: UUID, skip: int = 0, limit: int = 100) -> List[ListingORM]:
        """Get all listings by a seller"""
        return self.db.query(ListingORM).filter(
            ListingORM.seller_id == seller_id
        ).offset(skip).limit(limit).all()
    
    async def get_by_status(self, status: ListingStatus, skip: int = 0, limit: int = 100) -> List[ListingORM]:
        """Get listings with specific status (DRAFT, ACTIVE, SOLD, CLOSED)"""
        return self.db.query(ListingORM).filter(
            ListingORM.status == status
        ).order_by(
            desc(ListingORM.created_at)
        ).offset(skip).limit(limit).all()
    
    async def get_active_listings(self, skip: int = 0, limit: int = 100) -> List[ListingORM]:
        """Get all active listings (shorthand)"""
        return await self.get_by_status(ListingStatus.ACTIVE, skip, limit)
    
    async def get_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[ListingORM]:
        """Get listings in specific category"""
        return self.db.query(ListingORM).filter(
            and_(
                ListingORM.category == category,
                ListingORM.status == ListingStatus.ACTIVE
            )
        ).offset(skip).limit(limit).all()
    
    async def search(self, query: str, skip: int = 0, limit: int = 100) -> List[ListingORM]:
        """
        Search listings by title or description.
        
        Used by marketplace search.
        """
        return self.db.query(ListingORM).filter(
            and_(
                ListingORM.status == ListingStatus.ACTIVE,
                or_(
                    ListingORM.title.ilike(f"%{query}%"),
                    ListingORM.description.ilike(f"%{query}%")
                )
            )
        ).offset(skip).limit(limit).all()
    
    async def search_with_filters(self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ListingORM]:
        """
        Advanced search with multiple filters.
        
        Optimization: Use indexed columns for filtering
        """
        filters = [ListingORM.status == ListingStatus.ACTIVE]
        
        if query:
            filters.append(
                or_(
                    ListingORM.title.ilike(f"%{query}%"),
                    ListingORM.description.ilike(f"%{query}%")
                )
            )
        
        if category:
            filters.append(ListingORM.category == category)
        
        if min_price is not None:
            filters.append(ListingORM.price >= min_price)
        
        if max_price is not None:
            filters.append(ListingORM.price <= max_price)
        
        if location:
            filters.append(ListingORM.location.ilike(f"%{location}%"))
        
        return self.db.query(ListingORM).filter(
            and_(*filters)
        ).offset(skip).limit(limit).all()
    
    async def get_similar_listings(self, listing_id: UUID, limit: int = 5) -> List[ListingORM]:
        """
        Get similar listings (same category, active).
        
        Used for recommendation.
        """
        listing = await self.get(listing_id)
        if not listing:
            return []
        
        return self.db.query(ListingORM).filter(
            and_(
                ListingORM.id != listing_id,
                ListingORM.category == listing.category,
                ListingORM.status == ListingStatus.ACTIVE
            )
        ).limit(limit).all()
    
    async def count_by_seller(self, seller_id: UUID) -> int:
        """Count listings by seller"""
        return self.db.query(ListingORM).filter(
            ListingORM.seller_id == seller_id
        ).count()
    
    async def count_active(self) -> int:
        """Total active listings"""
        return self.db.query(ListingORM).filter(
            ListingORM.status == ListingStatus.ACTIVE
        ).count()


class OfferRepository(BaseRepository):
    """
    Consolidated repository for offer data access.
    
    Responsibilities:
    - Offer CRUD operations
    - Query offers by listing, buyer, status
    - Track offer history
    """
    
    def __init__(self, db: Session):
        super().__init__(db, OfferORM)
        self.db = db
    
    async def get_by_listing(self, listing_id: UUID, skip: int = 0, limit: int = 100) -> List[OfferORM]:
        """Get all offers for a listing"""
        return self.db.query(OfferORM).filter(
            OfferORM.listing_id == listing_id
        ).order_by(
            desc(OfferORM.created_at)
        ).offset(skip).limit(limit).all()
    
    async def get_by_buyer(self, buyer_id: UUID, skip: int = 0, limit: int = 100) -> List[OfferORM]:
        """Get all offers made by a buyer"""
        return self.db.query(OfferORM).filter(
            OfferORM.buyer_id == buyer_id
        ).offset(skip).limit(limit).all()
    
    async def get_pending_for_listing(self, listing_id: UUID) -> List[OfferORM]:
        """Get all pending offers for a listing"""
        return self.db.query(OfferORM).filter(
            and_(
                OfferORM.listing_id == listing_id,
                OfferORM.status == OfferStatus.PENDING
            )
        ).order_by(
            desc(OfferORM.price)  # Highest price first
        ).all()
    
    async def get_accepted_for_listing(self, listing_id: UUID) -> Optional[OfferORM]:
        """Get accepted offer for listing (should only be one)"""
        return self.db.query(OfferORM).filter(
            and_(
                OfferORM.listing_id == listing_id,
                OfferORM.status == OfferStatus.ACCEPTED
            )
        ).first()
    
    async def buyer_already_offered(self, listing_id: UUID, buyer_id: UUID) -> bool:
        """Check if buyer already has pending offer on listing"""
        return self.db.query(OfferORM).filter(
            and_(
                OfferORM.listing_id == listing_id,
                OfferORM.buyer_id == buyer_id,
                OfferORM.status == OfferStatus.PENDING
            )
        ).first() is not None
    
    async def get_highest_offer(self, listing_id: UUID) -> Optional[OfferORM]:
        """Get highest price pending offer for listing"""
        return self.db.query(OfferORM).filter(
            and_(
                OfferORM.listing_id == listing_id,
                OfferORM.status == OfferStatus.PENDING
            )
        ).order_by(
            desc(OfferORM.price)
        ).first()
    
    async def count_pending_for_listing(self, listing_id: UUID) -> int:
        """Count pending offers on listing"""
        return self.db.query(OfferORM).filter(
            and_(
                OfferORM.listing_id == listing_id,
                OfferORM.status == OfferStatus.PENDING
            )
        ).count()


class BuyerRequestRepository(BaseRepository):
    """
    Repository for buyer requests (buyers request products).
    
    Separate from offers because buyer requests are outbound requests from buyers,
    while offers are inbound bids on seller listings.
    """
    
    def __init__(self, db: Session):
        super().__init__(db, BuyerRequestORM)
        self.db = db
    
    async def get_by_buyer(self, buyer_id: UUID, skip: int = 0, limit: int = 100) -> List[BuyerRequestORM]:
        """Get all requests posted by buyer"""
        return self.db.query(BuyerRequestORM).filter(
            BuyerRequestORM.buyer_id == buyer_id
        ).offset(skip).limit(limit).all()
    
    async def get_open_requests(self, skip: int = 0, limit: int = 100) -> List[BuyerRequestORM]:
        """Get all open buyer requests (for suppliers to respond to)"""
        return self.db.query(BuyerRequestORM).filter(
            BuyerRequestORM.status == "OPEN"
        ).order_by(
            desc(BuyerRequestORM.created_at)
        ).offset(skip).limit(limit).all()
    
    async def get_by_product(self, product: str, skip: int = 0, limit: int = 100) -> List[BuyerRequestORM]:
        """Get all open requests for a specific product"""
        return self.db.query(BuyerRequestORM).filter(
            and_(
                BuyerRequestORM.product == product,
                BuyerRequestORM.status == "OPEN"
            )
        ).offset(skip).limit(limit).all()
