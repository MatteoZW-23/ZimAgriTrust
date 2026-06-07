import math
import uuid
import secrets
import string
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.core.policy import calculate_transport_insurance_fee
from app.models.listing import Listing, ListingStatus, Offer, OfferStatus, Sector, BuyerRequest, FarmerResponse
from app.models.transaction import Order, OrderStatus, Transaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.listing import ListingCreate, OfferCreate, BuyerRequestCreate, FarmerResponseCreate
from app.services.wallet_service import wallet_service
from app.services.escrow_account_service import EscrowAccountService

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Haversine formula
    R = 6371 # Earth radius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
    data = payload.model_dump()
    # Compatibility mapping for legacy schema variants that still require title/description.
    data.setdefault("crop", data.get("product_type"))
    data.setdefault("crop_type", data.get("product_type") or "general")
    qty = float(data.get("quantity") or 0)
    unit = str(data.get("quantity_unit") or "kg").strip().lower()
    if unit == "kg":
        data.setdefault("quantity_kg", qty)
        data.setdefault("price_per_kg", float(data.get("price_per_unit") or 0))
    elif unit in {"g", "gram", "grams"}:
        data.setdefault("quantity_kg", qty / 1000.0)
        data.setdefault("price_per_kg", float(data.get("price_per_unit") or 0) * 1000.0)
    elif unit in {"t", "ton", "tons", "tonne", "tonnes"}:
        data.setdefault("quantity_kg", qty * 1000.0)
        data.setdefault("price_per_kg", float(data.get("price_per_unit") or 0) / 1000.0)
    else:
        data.setdefault("quantity_kg", qty)
        data.setdefault("price_per_kg", float(data.get("price_per_unit") or 0))
    # Map province/district to location_province/location_district for database
    data.setdefault("location_province", data.get("province"))
    data.setdefault("location_district", data.get("district"))
    data.setdefault("location", data.get("pickup_address") or data.get("location_district") or data.get("location_province"))
    data.setdefault("title", f"{data.get('product_type', 'Produce').title()} listing")
    data.setdefault("description", data.get("storage_requirements") or f"{data.get('product_type', 'Produce')} available")
    data.setdefault("available_from", datetime.now(timezone.utc))

    listing = Listing(seller_id=seller.id, **data)
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
    if listing.seller_id == buyer.id:
        raise HTTPException(status_code=400, detail="Cannot bid on own listing")

    offered_price = payload.offered_price_per_kg
    if offered_price is None:
        offered_price = listing.price_per_kg if getattr(listing, "price_per_kg", None) is not None else listing.price_per_unit

    offered_quantity = payload.offered_quantity_kg
    if offered_quantity is None:
        offered_quantity = listing.quantity_kg if getattr(listing, "quantity_kg", None) is not None else listing.quantity

    available_quantity = listing.quantity_kg if getattr(listing, "quantity_kg", None) else listing.quantity
    if offered_quantity and available_quantity and offered_quantity > available_quantity:
        raise HTTPException(status_code=400, detail="Offered quantity exceeds available stock")

    payload_data = payload.model_dump(exclude={"offered_price_per_kg", "offered_quantity_kg"})

    offer = Offer(
        listing_id=listing.id,
        buyer_id=buyer.id,
        seller_id=listing.seller_id,
        offered_price_per_kg=offered_price,
        offered_quantity_kg=offered_quantity,
        **payload_data,
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
    ).update({"status": OfferStatus.DECLINED})

    total_amount = listing.quantity * listing.price_per_unit

    # Determine if buyer is using on-platform transport (incentive discount)
    from app.models.listing import LogisticsType
    using_platform_transport = offer.logistics_type == LogisticsType.PLATFORM

    from app.services.subscription_service import SubscriptionService
    fee_breakdown = SubscriptionService.calculate_fee_for_owner(db, total_amount, user=listing.seller)
    fee = fee_breakdown["platform_fee"]
    payout = round(total_amount - fee, 2)

    # Transport insurance fee (optional, buyer-elected)
    insurance_fee = calculate_transport_insurance_fee(
        total_amount, offer.currency, transport_insurance_elected
    )

    order = Order(
        listing_id=listing.id,
        offer_id=offer.id,
        buyer_id=offer.buyer_id,
        seller_id=listing.seller_id,
        order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        quantity=listing.quantity,
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
    success = wallet_service.hold_escrow(db, order.buyer_id, escrow_amount, order.currency, order_id=order.id)
    if success:
        order.status = OrderStatus.ESCROW_HELD
        EscrowAccountService.mark_funded(db, order, escrow_amount)
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
    offer.status = OfferStatus.DECLINED
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
    offer.offered_price_per_kg = counter_price

    # In a real system, we might track 'last_actor_id' to know who needs to respond next.
    db.commit()
    db.refresh(offer)
    return offer

def create_buyer_request(db: Session, buyer: User, payload: BuyerRequestCreate) -> BuyerRequest:
    data = payload.model_dump()
    if data.get("sector") is not None:
        data["sector"] = getattr(data["sector"], "value", data["sector"])
    request = BuyerRequest(
        buyer_id=buyer.id,
        **data
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
    from app.services.subscription_service import SubscriptionService
    fee_breakdown = SubscriptionService.calculate_fee_for_owner(db, total_amount, user=response.farmer)
    fee = fee_breakdown["platform_fee"]
    payout = round(total_amount - fee, 2)

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

    success = wallet_service.hold_escrow(db, order.buyer_id, order.total_amount, order.currency, order_id=order.id)
    if success:
        order.status = OrderStatus.ESCROW_HELD
        EscrowAccountService.mark_funded(db, order, order.total_amount)
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
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
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
    listing.created_at = datetime.now(timezone.utc)
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
    page = query.order_by(Listing.is_boosted.desc(), Listing.created_at.desc()).all()
    from app.services.subscription_service import SubscriptionService
    results = sorted(
        page,
        key=lambda item: (
            bool(getattr(item, "is_boosted", False)),
            SubscriptionService.visibility_weight(db, user=item.seller) if item.seller else 100,
            item.created_at,
        ),
        reverse=True,
    )[offset:offset + limit]
    return results, total

class MarketplaceService:
    @staticmethod
    def create_listing(db: Session, seller: User, payload: ListingCreate) -> Listing:
        return create_listing(db, seller, payload)
    @staticmethod
    def create_offer(db: Session, buyer: User, listing: Listing, payload: OfferCreate) -> Offer:
        return create_offer(db, buyer, listing, payload)
    @staticmethod
    def place_offer(db: Session, listing_id: uuid.UUID, buyer: User, payload: OfferCreate) -> Offer:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
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
