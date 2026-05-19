"""
Data Validation Script for Transaction Flow Unification

This script validates the data structure after the transaction flow unification.
Since the unified TransactionService uses the same underlying data models, no actual
data migration is needed.

This script performs validation and cleanup:
1. Ensures all orders have valid user references
2. Ensures all orders have valid listing or request references
3. Validates trade sessions have valid participants
4. Checks for orphaned records
5. Validates transaction consistency

Run this script after deploying the unified TransactionService.
"""
import sys
import os
from datetime import datetime
import uuid

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.db.base import Base

from app.models.listing import Listing, Offer, BuyerRequest, FarmerResponse, TradeSession, TradeMessage
from app.models.transaction import Order, Transaction, TransportSurvey
from app.models.user import User, UserRole


def validate_data(database_url: str):
    """Validate transaction data structure."""
    
    print("Starting transaction data validation...")
    print(f"Database: {database_url}")
    
    # Create engine
    engine = create_engine(database_url)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Statistics
        stats = {
            "total_orders": 0,
            "orders_without_buyer": 0,
            "orders_without_seller": 0,
            "orders_without_listing": 0,
            "orders_without_request": 0,
            "orphaned_offers": 0,
            "orphaned_responses": 0,
            "orphaned_trade_sessions": 0,
            "orphaned_trade_messages": 0,
            "orphaned_transactions": 0,
            "issues_fixed": 0
        }
        
        # 1. Validate Orders
        print("\n[1/8] Validating Order records...")
        orders = db.query(Order).all()
        stats["total_orders"] = len(orders)
        
        for order in orders:
            # Check buyer reference
            if order.buyer_id:
                buyer = db.query(User).filter(User.id == order.buyer_id).first()
                if not buyer:
                    stats["orders_without_buyer"] += 1
                    print(f"  ⚠️ Order {order.id} references non-existent buyer {order.buyer_id}")
            else:
                stats["orders_without_buyer"] += 1
                print(f"  ⚠️ Order {order.id} has no buyer reference")
            
            # Check seller reference
            if order.seller_id:
                seller = db.query(User).filter(User.id == order.seller_id).first()
                if not seller:
                    stats["orders_without_seller"] += 1
                    print(f"  ⚠️ Order {order.id} references non-existent seller {order.seller_id}")
            else:
                stats["orders_without_seller"] += 1
                print(f"  ⚠️ Order {order.id} has no seller reference")
            
            # Check listing reference (for listing-based orders)
            if order.listing_id:
                listing = db.query(Listing).filter(Listing.id == order.listing_id).first()
                if not listing:
                    stats["orders_without_listing"] += 1
                    print(f"  ⚠️ Order {order.id} references non-existent listing {order.listing_id}")
            
            # Check buyer request reference (for request-based orders)
            # Note: Orders don't directly reference buyer requests, but through farmer responses
            # This is a data model design choice, not an error
        
        # 2. Validate Offers
        print("\n[2/8] Validating Offer records...")
        offers = db.query(Offer).all()
        
        for offer in offers:
            listing = db.query(Listing).filter(Listing.id == offer.listing_id).first()
            if not listing:
                stats["orphaned_offers"] += 1
                print(f"  ⚠️ Offer {offer.id} references non-existent listing {offer.listing_id}")
            
            # Check buyer reference
            if offer.buyer_id:
                buyer = db.query(User).filter(User.id == offer.buyer_id).first()
                if not buyer:
                    print(f"  ⚠️ Offer {offer.id} references non-existent buyer {offer.buyer_id}")
        
        # 3. Validate Buyer Requests
        print("\n[3/8] Validating BuyerRequest records...")
        buyer_requests = db.query(BuyerRequest).all()
        
        for request in buyer_requests:
            # Check buyer reference
            if request.buyer_id:
                buyer = db.query(User).filter(User.id == request.buyer_id).first()
                if not buyer:
                    print(f"  ⚠️ BuyerRequest {request.id} references non-existent buyer {request.buyer_id}")
        
        # 4. Validate Farmer Responses
        print("\n[4/8] Validating FarmerResponse records...")
        farmer_responses = db.query(FarmerResponse).all()
        
        for response in farmer_responses:
            # Check request reference
            request = db.query(BuyerRequest).filter(BuyerRequest.id == response.request_id).first()
            if not request:
                stats["orphaned_responses"] += 1
                print(f"  ⚠️ FarmerResponse {response.id} references non-existent request {response.request_id}")
            
            # Check farmer reference
            if response.farmer_id:
                farmer = db.query(User).filter(User.id == response.farmer_id).first()
                if not farmer:
                    print(f"  ⚠️ FarmerResponse {response.id} references non-existent farmer {response.farmer_id}")
        
        # 5. Validate Trade Sessions
        print("\n[5/8] Validating TradeSession records...")
        trade_sessions = db.query(TradeSession).all()
        
        for session in trade_sessions:
            # Check listing reference
            listing = db.query(Listing).filter(Listing.id == session.listing_id).first()
            if not listing:
                stats["orphaned_trade_sessions"] += 1
                print(f"  ⚠️ TradeSession {session.id} references non-existent listing {session.listing_id}")
            
            # Check participants
            if session.buyer_id:
                buyer = db.query(User).filter(User.id == session.buyer_id).first()
                if not buyer:
                    print(f"  ⚠️ TradeSession {session.id} references non-existent buyer {session.buyer_id}")
            
            if session.seller_id:
                seller = db.query(User).filter(User.id == session.seller_id).first()
                if not seller:
                    print(f"  ⚠️ TradeSession {session.id} references non-existent seller {session.seller_id}")
        
        # 6. Validate Trade Messages
        print("\n[6/8] Validating TradeMessage records...")
        trade_messages = db.query(TradeMessage).all()
        
        for message in trade_messages:
            # Check session reference
            session = db.query(TradeSession).filter(TradeSession.id == message.session_id).first()
            if not session:
                stats["orphaned_trade_messages"] += 1
                print(f"  ⚠️ TradeMessage {message.id} references non-existent session {message.session_id}")
            
            # Check sender reference (unless it's a system message)
            if message.sender_id != uuid.UUID(int=0):
                sender = db.query(User).filter(User.id == message.sender_id).first()
                if not sender:
                    print(f"  ⚠️ TradeMessage {message.id} references non-existent sender {message.sender_id}")
        
        # 7. Validate Transactions
        print("\n[7/8] Validating Transaction records...")
        transactions = db.query(Transaction).all()
        
        for transaction in transactions:
            # Check order reference
            order = db.query(Order).filter(Order.id == transaction.order_id).first()
            if not order:
                stats["orphaned_transactions"] += 1
                print(f"  ⚠️ Transaction {transaction.id} references non-existent order {transaction.order_id}")
        
        # 8. Validate Transport Surveys
        print("\n[8/8] Validating TransportSurvey records...")
        transport_surveys = db.query(TransportSurvey).all()
        
        for survey in transport_surveys:
            # Check order reference
            order = db.query(Order).filter(Order.id == survey.order_id).first()
            if not order:
                print(f"  ⚠️ TransportSurvey {survey.id} references non-existent order {survey.order_id}")
            
            # Check submitted_by reference
            if survey.submitted_by:
                user = db.query(User).filter(User.id == survey.submitted_by).first()
                if not user:
                    print(f"  ⚠️ TransportSurvey {survey.id} references non-existent user {survey.submitted_by}")
        
        # Commit any fixes (none in this version, just validation)
        db.commit()
        
        # Print summary
        print("\n" + "="*50)
        print("Validation Complete!")
        print("="*50)
        print(f"Total Orders: {stats['total_orders']}")
        print(f"Orders without buyer: {stats['orders_without_buyer']}")
        print(f"Orders without seller: {stats['orders_without_seller']}")
        print(f"Orders without listing: {stats['orders_without_listing']}")
        print(f"Orphaned Offers: {stats['orphaned_offers']}")
        print(f"Orphaned Farmer Responses: {stats['orphaned_responses']}")
        print(f"Orphaned Trade Sessions: {stats['orphaned_trade_sessions']}")
        print(f"Orphaned Trade Messages: {stats['orphaned_trade_messages']}")
        print(f"Orphaned Transactions: {stats['orphaned_transactions']}")
        print(f"Issues Fixed: {stats['issues_fixed']}")
        print("="*50)
        
        total_issues = (
            stats["orders_without_buyer"] +
            stats["orders_without_seller"] +
            stats["orders_without_listing"] +
            stats["orphaned_offers"] +
            stats["orphaned_responses"] +
            stats["orphaned_trade_sessions"] +
            stats["orphaned_trade_messages"] +
            stats["orphaned_transactions"]
        )
        
        if total_issues > 0:
            print(f"\n⚠️ {total_issues} data issues found that may need manual review.")
        else:
            print("\n✅ All data validation checks passed!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Validation failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Get database URL from environment or use default
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/zimagritrust')
    
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    validate_data(database_url)
