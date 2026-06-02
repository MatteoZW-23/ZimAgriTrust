"""
Celery Tasks for ZimAgriTrust Background Processing - Production Hardened
"""
import logging
from datetime import datetime, timezone
from celery import Task
from sqlalchemy.orm import Session
from app.worker.celery_app import celery_app
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""
    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(name="app.worker.tasks.health_check", bind=True)
def health_check(self):
    """Simple health check task for Celery worker monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker": self.request.hostname,
        "queue": self.request.delivery_info.get("routing_key", "default")
    }


@celery_app.task(name="app.worker.tasks.send_notification", base=DatabaseTask, bind=True, max_retries=3, default_retry_delay=60)
def send_notification(self, user_id: int, notification_type: str, message: str):
    """
    Send notification to user (email, SMS, or in-app) with proper error handling
    Routes to dead-letter queue after max retries
    """
    try:
        from app.models.user import User
        from app.services.notification_service import NotificationService
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found for notification")
            raise ValueError(f"User {user_id} not found")
        
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        
        # Route to appropriate notification channel
        if notification_type == "email":
            NotificationService.send_email(user.email, message)
        elif notification_type == "sms":
            NotificationService.send_sms(user.phone_number, message)
        elif notification_type == "whatsapp":
            NotificationService.send_whatsapp(user.phone_number, message)
        else:
            logger.warning(f"Unknown notification type: {notification_type}")
        
        return {
            "user_id": user_id,
            "notification_type": notification_type,
            "status": "sent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Failed to send notification to user {user_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="app.worker.tasks.process_payment", base=DatabaseTask, bind=True, max_retries=3, default_retry_delay=60)
def process_payment(self, payment_id: int):
    """
    Process payment in background with proper error handling and idempotency
    Routes to dead-letter queue after max retries
    """
    try:
        from app.models.transaction import Transaction, TransactionType
        from app.services.wallet_service import WalletService
        
        payment = self.db.query(Transaction).filter(Transaction.id == payment_id).first()
        if not payment:
            logger.error(f"Payment {payment_id} not found")
            raise ValueError(f"Payment {payment_id} not found")
        
        if payment.status == "completed":
            logger.info(f"Payment {payment_id} already completed - idempotent")
            return {
                "payment_id": payment_id,
                "status": "already_completed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        logger.info(f"Processing payment {payment_id}")
        
        # Process payment based on type
        if payment.type == TransactionType.DEPOSIT:
            success = WalletService.deposit(
                db=self.db,
                user_id=payment.user_id,
                amount=payment.amount,
                currency=payment.currency,
                reference=f"payment_{payment_id}",
                idempotency_key=f"payment_{payment_id}"
            )
        elif payment.type == TransactionType.WITHDRAWAL:
            success = WalletService.withdraw(
                db=self.db,
                user_id=payment.user_id,
                amount=payment.amount,
                currency=payment.currency,
                idempotency_key=f"payment_{payment_id}"
            )
        else:
            logger.warning(f"Unhandled payment type: {payment.type}")
            success = False
        
        if success:
            payment.status = "completed"
            payment.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            
            return {
                "payment_id": payment_id,
                "status": "processed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise Exception("Payment processing failed")
    
    except Exception as exc:
        logger.error(f"Failed to process payment {payment_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="app.worker.tasks.generate_report", base=DatabaseTask, bind=True, max_retries=2, default_retry_delay=120)
def generate_report(self, report_type: str, params: dict):
    """
    Generate report in background with proper error handling
    Routes to dead-letter queue after max retries
    """
    try:
        logger.info(f"Generating {report_type} report with params {params}")
        
        # Implement report generation logic based on type
        if report_type == "financial_summary":
            # Generate financial summary report
            from app.models.transaction import Transaction
            from sqlalchemy import func as sa_func
            
            total_transactions = self.db.query(Transaction).count()
            total_volume = self.db.query(sa_func.sum(Transaction.amount)).scalar() or 0
            
            report_data = {
                "total_transactions": total_transactions,
                "total_volume": float(total_volume),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        
        elif report_type == "user_activity":
            # Generate user activity report
            from app.models.user import User
            
            active_users = self.db.query(User).filter(User.is_active == True).count()
            total_users = self.db.query(User).count()
            
            report_data = {
                "active_users": active_users,
                "total_users": total_users,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        
        else:
            logger.warning(f"Unknown report type: {report_type}")
            report_data = {"error": f"Unknown report type: {report_type}"}
        
        return {
            "report_type": report_type,
            "status": "generated",
            "data": report_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Failed to generate {report_type} report: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))


@celery_app.task(name="app.worker.tasks.process_auto_settlement", base=DatabaseTask, bind=True, max_retries=3, default_retry_delay=300)
def process_auto_settlement(self):
    """
    Process automatic settlement for delivered orders older than 7 days
    Runs periodically via Celery Beat
    """
    try:
        from app.models.transaction import Order, OrderStatus
        from app.services.escrow_service import process_auto_settlement
        from app.services.supplier_service import SupplierLogisticsService
        from datetime import timedelta, timezone
        
        logger.info("Processing auto-settlement for eligible orders")
        
        # Find all DELIVERED orders
        delivered_orders = self.db.query(Order).filter(
            Order.status == OrderStatus.DELIVERED
        ).all()
        
        processed_count = 0
        failed_count = 0
        failed_order_ids = []
        for order in delivered_orders:
            try:
                success = process_auto_settlement(self.db, order)
                if success:
                    processed_count += 1
            except Exception as e:
                logger.error(f"Failed to auto-settle order {order.id}: {e}")
                failed_count += 1
                failed_order_ids.append(str(order.id))

        supplier_auto_confirmed = SupplierLogisticsService.auto_confirm_expired(self.db)
        
        return {
            "status": "completed",
            "processed_count": processed_count,
            "supplier_auto_confirmed": supplier_auto_confirmed,
            "failed_count": failed_count,
            "failed_order_ids": failed_order_ids[:20],
            "total_eligible": len(delivered_orders),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Auto-settlement batch failed: {exc}")
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))


@celery_app.task(name="app.worker.tasks.cleanup_expired_sessions", base=DatabaseTask, bind=True, max_retries=2, default_retry_delay=300)
def cleanup_expired_sessions(self):
    """
    Clean up expired user sessions
    Runs periodically via Celery Beat
    """
    try:
        from app.models.session import UserSession
        from datetime import timedelta, timezone
        
        logger.info("Cleaning up expired sessions")
        
        # Delete sessions older than 30 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        deleted_count = self.db.query(UserSession).filter(
            UserSession.expires_at < cutoff
        ).delete()
        
        self.db.commit()
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Session cleanup failed: {exc}")
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
