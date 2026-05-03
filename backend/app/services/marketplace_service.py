import math
import uuid
import secrets
import string
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.listing import Listing, ListingStatus, Offer, OfferStatus, Sector, BuyerRequest, FarmerResponse
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreate, OfferCreate, BuyerRequestCreate, FarmerResponseCreate
from app.services.wallet_service import wallet_service

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Haversine formula
    R = 6371 # Earth radius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_seller_settlement(amount: float, trust_score: float, currency: str = "USD"):
    """
    ZimAgritrust Fee Structure:
    - Standardfee: 1.0% (0.01)
    - High Trust Discount: 0.5% if trust_score > 90
    """
    fee_rate = 0.01
    if trust_score > 90:
        fee_rate = 0.005
        
    fee = amount * fee_rate
    payout = amount - fee
    return fee, payout

def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
    listing = Listing(
        seller_id=seller.id,
        **payload.model_dump()
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot bid on own listing")
        
    offer = Offer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        **payload.model_dump(),
        status=OfferStatus.PENDING
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer

def accept_offer(
    db: Session,
    listing: Listing,
    offer: Offer,
    transport_insurance_elected: bool = False,
) -> Order:
    if offer.status != OfferStatus.PENDING:
        raise HTTPException(status_code=400, detail="Offer not pending")

    # Update state
    offer.status = OfferStatus.ACCEPTED
    listing.status = ListingStatus.SOLD

    # Reject competing offers
    db.query(Offer).filter(
        Offer.listing_id == listing.id,
        Offer.id != offer.id
    ).update({"status": OfferStatus.REJECTED})

    total_amount = offer.quantity * offer.price_per_unit

    # Determine if buyer is using on-platform transport (incentive discount)
    from app.models.listing import LogisticsType
    using_platform_transport = offer.logistics_type == LogisticsType.PLATFORM

    fee, payout = calculate_seller_settlement(
        total_amount,
        listing.seller.trust_score,
        offer.currency,
        using_platform_transport=using_platform_transport,
    )

    # Transport insurance fee (optional, buyer-elected)
    from app.core.policy import calculate_transport_insurance_fee
    insurance_fee = calculate_transport_insurance_fee(
        total_amount, offer.currency, transport_insurance_elected
    )

    order = Order(
        listing_id=listing.id,
        offer_id=offer.id,
        buyer_id=offer.buyer_id,
        seller_id=listing.seller_id,
        order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        quantity=offer.quantity,
        total_amount=total_amount,
        platform_fee=fee,
        seller_payout=payout,
        currency=offer.currency,
        status=OrderStatus.PENDING,
        logistics_type=offer.logistics_type,
        handover_code=secrets.token_hex(3).upper(),
        transport_insurance_elected=transport_insurance_elected,
        transport_insurance_fee=insurance_fee,
    )
    db.add(order)
    db.flush()

    # Escrow holds goods amount + insurance fee
    escrow_amount = round(total_amount + insurance_fee, 2)
    success = wallet_service.hold_escrow(db, order.buyer_id, escrow_amount, order.currency)
    if success:
        order.status = OrderStatus.ESCROW_HELD
        db.add(Transaction(
            order_id=order.id, user_id=order.buyer_id, type=TransactionType.ESCROW_HOLD,
            amount=escrow_amount, currency=order.currency
        ))

    db.commit()
    db.refresh(order)

    # Create delivery tracking record immediately after escrow is funded
    if order.status == OrderStatus.ESCROW_HELD:
        from app.services.delivery_service import create_delivery_record
        create_delivery_record(db, order)

    return order

def reject_offer(db: Session, offer: Offer) -> Offer:
    offer.status = OfferStatus.REJECTED
    db.commit()
    db.refresh(offer)
    return offer

def counter_offer(db: Session, offer: Offer, counter_price: float, actor: User) -> Offer:
    """
    ZimAgritrust Spec (Diagram 5): Negotiation Flow.
    Allows a party to suggest a new price.
    """
    if offer.status not in {OfferStatus.PENDING, OfferStatus.COUNTERED}:
        raise HTTPException(status_code=400, detail="Offer not in negotiable state")

    # Update logic: Flip the initiator
    offer.status = OfferStatus.COUNTERED
    offer.price_per_unit = counter_price
    
    # In a real system, we might track 'last_actor_id' to know who needs to respond next.
    db.commit()
    db.refresh(offer)
    return offer

def create_buyer_request(db: Session, buyer: User, payload: BuyerRequestCreate) -> BuyerRequest:
    request = BuyerRequest(
        buyer_id=buyer.id,
        **payload.model_dump()
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

def farmer_respond_to_request(db: Session, farmer: User, request: BuyerRequest, payload: FarmerResponseCreate) -> FarmerResponse:
    if farmer.role != UserRole.FARMER:
        raise HTTPException(status_code=403, detail="Only farmers can respond")
    response = FarmerResponse(
        request_id=request.id,
        farmer_id=farmer.id,
        **payload.model_dump()
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response

def accept_farmer_response(db: Session, response: FarmerResponse) -> Order:
    response.status = "accepted"
    response.request.status = "filled"
    
    # Create Virtual Listing
    virtual_listing = Listing(
        seller_id=response.farmer_id,
        sector=Sector.MIXED_FARMING,
        product_type=response.request.product_type,
        quantity=response.supply_quantity,
        price_per_unit=response.bid_price,
        currency=response.currency,
        status=ListingStatus.SOLD,
        notes=f"Buyer Request {response.request_id} Fulfillment"
    )
    db.add(virtual_listing)
    db.flush()

    total_amount = response.supply_quantity * response.bid_price
    fee, payout = calculate_seller_settlement(total_amount, response.farmer.trust_score, response.currency)

    order = Order(
        listing_id=virtual_listing.id,
        buyer_id=response.request.buyer_id,
        seller_id=response.farmer_id,
        order_number=f"ORD-REQ-{uuid.uuid4().hex[:8].upper()}",
        quantity=response.supply_quantity,
        total_amount=total_amount,
        platform_fee=fee,
        seller_payout=payout,
        currency=response.currency,
        status=OrderStatus.PENDING,
        handover_code=secrets.token_hex(3).upper()
    )
    db.add(order)
    db.flush()

    success = wallet_service.hold_escrow(db, order.buyer_id, order.total_amount, order.currency)
    if success:
        order.status = OrderStatus.ESCROW_HELD
        db.add(Transaction(
            order_id=order.id, user_id=order.buyer_id, type=TransactionType.ESCROW_HOLD,
            amount=order.total_amount, currency=order.currency
        ))

    db.commit()
    db.refresh(order)
    return order

def expire_old_listings(db: Session, days: int = 30) -> int:
    """
    Auto-expires listings older than the specified duration.
    """
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=days)
    expired_count = db.query(Listing).filter(
        Listing.status == ListingStatus.ACTIVE,
        Listing.created_at < cutoff
    ).update({"status": ListingStatus.EXPIRED})
    db.commit()
    return expired_count

def bump_listing(db: Session, listing: Listing) -> Listing:
    """
    Bumps a listing to the top of search results by updating its created_at timestamp.
    """
    listing.created_at = datetime.utcnow()
    db.commit()
    db.refresh(listing)
    return listing


def search_listings(
    db: Session,
    crop: str | None = None,
    location: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    grade: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Listing], int]:
    query = (
        db.query(Listing)
        .options(selectinload(Listing.seller))
        .filter(Listing.status == ListingStatus.ACTIVE)
    )

    if crop:
        term = f"%{crop.strip()}%"
        if term != "%%":
            query = query.filter(
                or_(
                    Listing.crop.ilike(term),
                    Listing.product_type.ilike(term),
                    Listing.product_subtype.ilike(term),
                    Listing.ai_crop_type.ilike(term),
                )
            )

    if location:
        term = f"%{location.strip()}%"
        if term != "%%":
            query = query.filter(
                or_(
                    Listing.location.ilike(term),
                    Listing.location_province.ilike(term),
                    Listing.location_district.ilike(term),
                    Listing.pickup_address.ilike(term),
                )
            )

    if min_price is not None:
        query = query.filter(Listing.price_per_unit >= min_price)

    if max_price is not None:
        query = query.filter(Listing.price_per_unit <= max_price)

    if grade:
        term = f"%{grade.strip()}%"
        if term != "%%":
            query = query.filter(
                or_(
                    Listing.grade.ilike(term),
                    Listing.ai_grade_estimate.ilike(term),
                )
            )

    total = query.count()
    results = (
        query.order_by(Listing.is_boosted.desc(), Listing.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return results, total

class MarketplaceService:
    @staticmethod
    def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
        return create_listing(db, seller, payload)
    @staticmethod
    def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
        return create_offer(db, buyer, listing, payload)
    @staticmethod
    def accept_offer(db: Session, listing: Listing, offer: Offer) -> Order:
        return accept_offer(db, listing, offer)
    @staticmethod
    def reject_offer(db: Session, offer: Offer) -> Offer:
        return reject_offer(db, offer)
    @staticmethod
    def counter_offer(db: Session, offer: Offer, counter_price: float, actor: User) -> Offer:
        return counter_offer(db, offer, counter_price, actor)
    @staticmethod
    def create_buyer_request(db: Session, buyer: User, payload: BuyerRequestCreate) -> BuyerRequest:
        return create_buyer_request(db, buyer, payload)
    @staticmethod
    def farmer_respond_to_request(db: Session, farmer: User, request: BuyerRequest, payload: FarmerResponseCreate) -> FarmerResponse:
        return farmer_respond_to_request(db, farmer, request, payload)
    @staticmethod
    def accept_farmer_response(db: Session, response: FarmerResponse) -> Order:
        return accept_farmer_response(db, response)
    @staticmethod
    def expire_old_listings(db: Session, days: int = 30) -> int:
        return expire_old_listings(db, days)
    @staticmethod
    def bump_listing(db: Session, listing: Listing) -> Listing:
        return bump_listing(db, listing)
    @staticmethod
    def search_listings(
        db: Session,
        crop: str | None = None,
        location: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        grade: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Listing], int]:
        return search_listings(db, crop, location, min_price, max_price, grade, limit, offset)

marketplace_core = MarketplaceService()
