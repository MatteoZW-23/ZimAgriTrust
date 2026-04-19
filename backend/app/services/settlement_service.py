from sqlalchemy.orm import Session
from app.models.transaction import Order, OrderStatus
from app.services.escrow_service import process_auto_settlement
from datetime import datetime, timedelta
import logging

class SettlementService:
    @staticmethod
    def run_settlement_sweep(db: Session):
        """
        Scans for DELIVERED orders and handles the 7-day notification/auto-release lifecycle
        as per Diagram 9: TIMING DIAGRAM - AUTO ESCROW RELEASE.
        """
        logging.info("[SETTLEMENT] INITIATING AGRI-TRUST ESCROW SWEEP...")
        
        now = datetime.now()
        
        # 1. IDENTIFY DELIVERED ORDERS
        orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).all()
        
        settled_count = 0
        reminded_count = 0
        
        for order in orders:
            # Calculate days elapsed since delivery
            delivery_time = order.updated_at # Assuming status change to DELIVERED is last update
            days_elapsed = (now - delivery_time).days
            
            try:
                if days_elapsed >= 7:
                    # DAY 7: AUTO-RELEASE
                    logging.info(f"[SETTLEMENT] DAY 7 EXPIRED for Order {order.order_number}. Executing Auto-Release.")
                    if process_auto_settlement(db, order):
                        settled_count += 1
                        # Note: In production, trigger "Failure to confirm" penalty to trust score here
                
                elif days_elapsed in [1, 2, 3, 4, 5, 6]:
                    # DAYS 1-6: SEND REMINDERS
                    reminded_count += 1
                    days_remaining = 7 - days_elapsed
                    msg = f"Reminder: Please confirm delivery for Order {order.order_number}. "
                    if days_remaining == 1:
                        msg += "Final Warning: Auto-release will trigger TOMORROW."
                    else:
                        msg += f"Auto-release will trigger in {days_remaining} days."
                    
                    # LOGGING AS SIMULATED SMS
                    logging.info(f"[SETTLEMENT] SMS TO BUYER {order.buyer_id}: {msg}")
                    
            except Exception as e:
                logging.error(f"Failed to process settlement logic for order {order.id}: {e}")
        
        logging.info(f"[SWEEP COMPLETE] Settled: {settled_count} | Reminded: {reminded_count}")

settlement_worker = SettlementService()
