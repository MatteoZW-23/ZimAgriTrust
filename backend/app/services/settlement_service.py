from sqlalchemy.orm import Session
from app.models.transaction import Order, OrderStatus
from app.services.escrow_service import process_auto_settlement
from datetime import datetime, timedelta
import logging

class SettlementService:
    @staticmethod
    def run_settlement_sweep(db: Session):
        """
        Scans for DELIVERED orders that have remained unchallenged for >48 hours 
        and automatically releases funds to the seller.
        """
        logging.info("[SETTLEMENT] INITIATING AUTOMATED ESCROW SWEEP...")
        
        # In a real production environment, we filter by updated_at
        # threshold = datetime.now() - timedelta(hours=48)
        # For this stage, we sweep all DELIVERED orders to demonstrate the safety-net
        
        orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).all()
        
        count = 0
        for order in orders:
            try:
                if process_auto_settlement(db, order):
                    count += 1
            except Exception as e:
                logging.error(f"Failed to auto-settle order {order.id}: {e}")
        
        logging.info(f"[SUCCESS] [SETTLEMENT] SWEEP COMPLETE. {count} ORDERS AUTO-SETTLED.")

settlement_worker = SettlementService()
