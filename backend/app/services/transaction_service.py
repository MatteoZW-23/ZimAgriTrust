"""
Unified Transaction Service

This service consolidates all transaction-related operations from:
- listings.py (market listings and offer-based transactions)
- trades.py (negotiation sessions and messaging)
- transactions.py (order management and post-transaction activities)
- requests.py (buyer requests and farmer responses)

The service provides a unified interface for the complete transaction lifecycle:
1. Listing/Request Creation
2. Search and Discovery
3. Negotiation (Offers and Messages)
4. Order Creation
5. Order Execution (Delivery and Payment)
6. Post-Transaction (Reviews, Receipts, Surveys)

This service wraps existing services (marketplace_core, escrow_service, receipt_service, etc.)
to provide a single entry point for all transaction operations.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from app.models.listing import Listing, ListingStatus, Offer, BuyerRequest, FarmerResponse
from app.models.transaction import Order, OrderStatus, Transaction, TransportSurvey
from app.models.trade import TradeSession, TradeMessage
from app.models.user import User, UserRole
from app.models.review import TradeReview

from app.services.marketplace_service import marketplace_core
from app.services.escrow_service import release_payment
from app.services.receipt_service import receipt_service
from app.services.verification_service import verification_service
from app.services.pii_masker import pii_masker


class TransactionService:
    """Unified service for all transaction operations."""
    
    # ==================== LISTING MANAGEMENT ====================
    
    @staticmethod
    def create_listing(db: Session, seller: User, payload) -> Listing:
        """
        Create a new market listing.
        
        Wraps marketplace_core.create_listing()
        """
        return marketplace_core.create_listing(db, seller, payload)
    
    @staticmethod
    def search_listings(
        db: Session,
        crop: Optional[str] = None,
        location: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        grade: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Listing], int]:
        """
        Search market listings.
        
        Wraps marketplace_core.search_listings()
        """
        return marketplace_core.search_listings(
            db=db,
            crop=crop,
            location=location,
            min_price=min_price,
            max_price=max_price,
            grade=grade,
            limit=limit,
            offset=offset,
        )
    
    @staticmethod
    def get_listings(db: Session, user: Optional[User] = None) -> List[Listing]:
        """
        Get listings.
        
        If user provided, returns user's listings. Otherwise returns all active listings.
        """
        if user:
            return db.query(Listing).filter(Listing.seller_id == user.id).all()
        return db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE).all()
    
    @staticmethod
    def get_listing(db: Session, listing_id: uuid.UUID) -> Listing:
        """Get a specific listing."""
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        return listing
    
    # ==================== REQUEST MANAGEMENT ====================
    
    @staticmethod
    def create_buyer_request(db: Session, buyer: User, payload) -> BuyerRequest:
        """
        Create a new buyer request.
        
        Wraps marketplace_core.create_buyer_request()
        """
        return marketplace_core.create_buyer_request(db, buyer, payload)
    
    @staticmethod
    def get_buyer_requests(db: Session, status: str = "open") -> List[BuyerRequest]:
        """
        Get buyer requests.
        
        Default returns open requests.
        """
        return db.query(BuyerRequest).filter(BuyerRequest.status == status).all()
    
    @staticmethod
    def get_buyer_request(db: Session, request_id: uuid.UUID) -> BuyerRequest:
        """Get a specific buyer request."""
        request = db.query(BuyerRequest).filter(BuyerRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return request
    
    @staticmethod
    def respond_to_request(db: Session, farmer: User, request: BuyerRequest, payload) -> FarmerResponse:
        """
        Farmer responds to a buyer request.
        
        Wraps marketplace_core.farmer_respond_to_request()
        """
        return marketplace_core.farmer_respond_to_request(db, farmer, request, payload)
    
    # ==================== NEGOTIATION - OFFERS ====================
    
    @staticmethod
    def create_offer(db: Session, buyer: User, listing: Listing, payload) -> Offer:
        """
        Create an offer on a listing.
        
        Wraps marketplace_core.create_offer()
        """
        return marketplace_core.create_offer(db, buyer, listing, payload)
    
    @staticmethod
    def accept_offer(db: Session, listing: Listing, offer: Offer) -> Order:
        """
        Accept an offer and create an order.
        
        Wraps marketplace_core.accept_offer()
        """
        return marketplace_core.accept_offer(db, listing, offer)
    
    @staticmethod
    def reject_offer(db: Session, offer: Offer) -> Offer:
        """
        Reject an offer.
        
        Wraps marketplace_core.reject_offer()
        """
        return marketplace_core.reject_offer(db, offer)
    
    @staticmethod
    def counter_offer(db: Session, offer: Offer, counter_price: float, user: User) -> Offer:
        """
        Counter an offer.
        
        Wraps marketplace_core.counter_offer()
        """
        return marketplace_core.counter_offer(db, offer, counter_price, user)
    
    @staticmethod
    def get_offers(db: Session, listing: Listing) -> List[Offer]:
        """Get all offers for a listing."""
        return db.query(Offer).filter(Offer.listing_id == listing.id).all()
    
    # ==================== NEGOTIATION - MESSAGES ====================
    
    @staticmethod
    def start_trade_session(db: Session, listing: Listing, buyer: User) -> TradeSession:
        """
        Start a trade session for a listing.
        
        Creates a new session or returns existing one.
        """
        if listing.seller_id == buyer.id:
            raise HTTPException(status_code=400, detail="Cannot start a trade with yourself")
        
        session = db.query(TradeSession).filter(
            TradeSession.listing_id == listing.id,
            TradeSession.buyer_id == buyer.id
        ).first()
        
        if not session:
            session = TradeSession(
                listing_id=listing.id,
                buyer_id=buyer.id,
                seller_id=listing.seller_id
            )
            db.add(session)
            db.commit()
            db.refresh(session)
        
        return session
    
    @staticmethod
    def get_trade_sessions(db: Session, user: User) -> List[TradeSession]:
        """Get all trade sessions for a user (as buyer or seller)."""
        return db.query(TradeSession).filter(
            (TradeSession.buyer_id == user.id) | 
            (TradeSession.seller_id == user.id)
        ).all()
    
    @staticmethod
    def send_trade_message(
        db: Session,
        session: TradeSession,
        sender: User,
        content: str,
        is_formal_offer: bool = False,
        offer_payload: Optional[Dict] = None
    ) -> TradeMessage:
        """
        Send a message in a trade session.
        
        Includes PII masking for security.
        """
        if sender.id not in [session.buyer_id, session.seller_id] and sender.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to participate in this trade")
        
        # Security Masking
        masked_content, was_masked = pii_masker.mask_content(content)
        
        message = TradeMessage(
            session_id=session.id,
            sender_id=sender.id,
            content=masked_content,
            is_formal_offer=is_formal_offer,
            offer_payload=offer_payload
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # If PII was detected, inject a system warning
        if was_masked:
            warning = TradeMessage(
                session_id=session.id,
                sender_id=uuid.UUID(int=0),  # System ID
                content=pii_masker.get_security_warning()
            )
            db.add(warning)
            db.commit()
        
        return message
    
    @staticmethod
    def get_trade_messages(db: Session, session: TradeSession, user: User) -> List[TradeMessage]:
        """
        Get messages from a trade session.
        
        Includes agent access for dispute mediation.
        """
        if user.id in [session.buyer_id, session.seller_id]:
            return session.messages
        
        if user.role == UserRole.ADMIN:
            return session.messages
        
        if user.role == UserRole.AGENT:
            # AGENT ACCESS PROTOCOL: Access only if there's an active dispute
            from app.models.dispute import Dispute, DisputeStatus
            from app.models.transaction import Order
            dispute = db.query(Dispute).join(Order).filter(
                Order.listing_id == session.listing_id,
                Dispute.agent_assigned == user.id,
                Dispute.status != DisputeStatus.RESOLVED
            ).first()
            
            if dispute:
                return session.messages
        
        raise HTTPException(status_code=403, detail="Access restricted to parties or assigned dispute mediators.")
    
    # ==================== ORDER MANAGEMENT ====================
    
    @staticmethod
    def create_order_from_response(db: Session, response: FarmerResponse) -> Order:
        """
        Create an order from an accepted farmer response.
        
        Wraps marketplace_core.accept_farmer_response()
        """
        return marketplace_core.accept_farmer_response(db, response)
    
    @staticmethod
    def get_orders(db: Session, user: User) -> List[Order]:
        """
        Get orders for a user.
        
        Buyers see their orders, farmers see their orders, admins see all.
        """
        if user.role == UserRole.BUYER:
            return db.query(Order).filter(Order.buyer_id == user.id).all()
        elif user.role == UserRole.FARMER:
            return db.query(Order).filter(Order.seller_id == user.id).all()
        else:
            return db.query(Order).all()
    
    @staticmethod
    def get_order(db: Session, order_id: uuid.UUID, user: User) -> Order:
        """Get a specific order with authorization check."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if user.role != UserRole.ADMIN and order.buyer_id != user.id and order.seller_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return order
    
    @staticmethod
    def get_order_transactions(db: Session, order_id: uuid.UUID) -> List[Transaction]:
        """Get all transactions for an order."""
        return db.query(Transaction).filter(Transaction.order_id == order_id).all()
    
    # ==================== ORDER EXECUTION ====================
    
    @staticmethod
    def confirm_delivery(
        db: Session,
        order: Order,
        user: User,
        handover_code: Optional[str] = None
    ) -> Order:
        """
        Confirm order delivery and release escrow payment.
        
        Wraps escrow_service.release_payment()
        """
        if order.buyer_id != user.id:
            raise HTTPException(status_code=403, detail="Only buyer can confirm delivery")
        
        if order.status != OrderStatus.ESCROW_HELD:
            raise HTTPException(status_code=400, detail="Order not in escrow")
        
        try:
            return release_payment(db, order, handover_code=handover_code)
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Settlement Failure: {str(e)}")
    
    # ==================== POST-TRANSACTION ====================
    
    @staticmethod
    def submit_review(
        db: Session,
        order: Order,
        reviewer: User,
        rating: int,
        comment: Optional[str] = None
    ) -> TradeReview:
        """
        Submit a review for a completed order.
        
        Includes trust score updates for positive ratings.
        """
        if reviewer.id not in {order.buyer_id, order.seller_id}:
            raise HTTPException(status_code=403, detail="Only trade parties can submit reviews")
        
        if order.status not in {OrderStatus.COMPLETED, OrderStatus.SETTLED}:
            raise HTTPException(status_code=400, detail="Reviews only allowed for completed/settled orders")
        
        existing = db.query(TradeReview).filter(
            TradeReview.order_id == order.id,
            TradeReview.reviewer_id == reviewer.id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Review already submitted for this order")
        
        reviewee_id = order.seller_id if reviewer.id == order.buyer_id else order.buyer_id
        reviewee = db.query(User).filter(User.id == reviewee_id).first()
        if not reviewee:
            raise HTTPException(status_code=404, detail="Review target not found")
        
        review = TradeReview(
            order_id=order.id,
            reviewer_id=reviewer.id,
            reviewee_id=reviewee_id,
            rating=rating,
            comment=comment,
            reviewer_role=reviewer.role.value if reviewer.role else None,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # Trust score update for positive ratings
        if rating >= 4:
            verification_service.record_positive_rating(db, reviewee, reviewer.role)
        
        return review
    
    @staticmethod
    def get_reviews(db: Session, order: Order, user: User) -> List[TradeReview]:
        """Get all reviews for an order."""
        if user.role != UserRole.ADMIN and user.id not in {order.buyer_id, order.seller_id}:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return db.query(TradeReview).filter(
            TradeReview.order_id == order.id
        ).order_by(TradeReview.created_at.desc()).all()
    
    @staticmethod
    def generate_receipt(db: Session, order: Order, user: User):
        """
        Generate a PDF receipt for an order.
        
        Wraps receipt_service.generate_receipt_pdf()
        """
        if user.role != UserRole.ADMIN and order.buyer_id != user.id and order.seller_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        from fastapi.responses import FileResponse
        
        try:
            pdf_path = receipt_service.generate_receipt_pdf(order)
            return FileResponse(
                path=pdf_path,
                filename=f"ZimAgritrust_Receipt_{order.order_number}.pdf",
                media_type="application/pdf"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate receipt: {str(e)}")
    
    @staticmethod
    def submit_transport_survey(
        db: Session,
        order: Order,
        user: User,
        transport_method: str,
        transport_cost_usd: Optional[float] = None,
        distance_km: Optional[float] = None,
        would_use_platform_transport: Optional[bool] = None,
        satisfaction_rating: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Submit a transport survey for a completed order.
        
        Captures off-platform transport data for market intelligence.
        """
        if order.buyer_id != user.id:
            raise HTTPException(status_code=403, detail="Only the buyer can submit this survey")
        
        if order.status not in {OrderStatus.COMPLETED, OrderStatus.SETTLED}:
            raise HTTPException(status_code=400, detail="Survey only available after delivery is confirmed")
        
        existing = db.query(TransportSurvey).filter(TransportSurvey.order_id == order.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Survey already submitted for this order")
        
        survey = TransportSurvey(
            order_id=order.id,
            submitted_by=user.id,
            transport_method=transport_method,
            transport_cost_usd=transport_cost_usd,
            distance_km=distance_km,
            would_use_platform_transport=would_use_platform_transport,
            satisfaction_rating=satisfaction_rating,
            notes=notes,
        )
        db.add(survey)
        db.commit()
        
        return {
            "message": "Survey submitted. Thank you for your feedback.",
            "order_id": str(order.id)
        }


# Singleton instance
transaction_service = TransactionService()
