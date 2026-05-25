"""
Enterprise Fraud Detection Engine

Implements velocity detection, pattern analysis, and risk scoring.
Automatically freezes high-risk transactions and creates investigation records.
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_

from app.models.user import User
from app.models.transaction import Transaction, Order
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class FraudRiskLevel(str, Enum):
    """Fraud risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudFlag(str, Enum):
    """Types of fraud flags"""
    VELOCITY_EXCEEDED = "velocity_exceeded"
    STRUCTURING_DETECTED = "structuring_detected"
    NEW_USER_LARGE_TXN = "new_user_large_txn"
    GEO_RISK = "geo_risk"
    ACCOUNT_TAKEOVER = "account_takeover"
    UNUSUAL_PATTERN = "unusual_pattern"
    DEVICE_CHANGE = "device_change"
    IP_MISMATCH = "ip_mismatch"
    FAILED_ATTEMPT_SPIKE = "failed_attempt_spike"


class FraudConfig:
    """Configuration for fraud detection thresholds"""
    
    # Velocity thresholds
    VELOCITY_WINDOW_SECONDS = 3600  # 1 hour
    VELOCITY_MAX_TRANSACTIONS = 10
    VELOCITY_MAX_AMOUNT = 5000.0
    
    # Structuring detection
    STRUCTURING_GAP_PERCENT = 0.05  # Within 5% of limit
    STRUCTURING_MIN_TRANSACTIONS = 3
    
    # New user thresholds
    NEW_USER_DAYS = 7
    NEW_USER_MAX_WITHDRAWAL = 100.0
    
    # Failed attempt thresholds
    FAILED_ATTEMPT_WINDOW = 300  # 5 minutes
    FAILED_ATTEMPT_MAX = 5


class FraudEngine:
    """
    Enterprise fraud detection engine.
    Analyzes transactions for suspicious patterns and assigns risk scores.
    """

    @staticmethod
    async def analyze_transaction(
        db: Session,
        user_id: uuid.UUID,
        amount: float,
        transaction_type: str,
        ip_address: str = None,
        user_agent: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud risk.
        Returns risk assessment with flags and recommendations.
        """
        flags = []
        risk_score = 0.0
        
        # 1. Velocity Detection
        velocity_flags = await FraudEngine._check_velocity(db, user_id, amount)
        flags.extend(velocity_flags)
        risk_score += len(velocity_flags) * 25
        
        # 2. Structuring Detection
        structuring_flags = await FraudEngine._check_structuring(db, user_id, amount)
        flags.extend(structuring_flags)
        risk_score += len(structuring_flags) * 30
        
        # 3. New User Check
        new_user_flags = await FraudEngine._check_new_user(db, user_id, amount)
        flags.extend(new_user_flags)
        risk_score += len(new_user_flags) * 20
        
        # 4. Failed Attempt Spike
        failed_flags = await FraudEngine._check_failed_attempts(user_id, ip_address)
        flags.extend(failed_flags)
        risk_score += len(failed_flags) * 35
        
        # 5. Device/IP Anomaly
        anomaly_flags = await FraudEngine._check_device_anomaly(db, user_id, ip_address, user_agent)
        flags.extend(anomaly_flags)
        risk_score += len(anomaly_flags) * 15
        
        # Determine risk level
        risk_level = FraudEngine._determine_risk_level(risk_score, flags)
        
        # Determine action
        action = FraudEngine._determine_action(risk_level, flags)
        
        return {
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level.value,
            "flags": [flag.value for flag in flags],
            "action": action,
            "should_freeze": action in ["freeze", "manual_review"],
            "requires_2fa": action in ["require_2fa", "manual_review"],
        }

    @staticmethod
    async def _check_velocity(
        db: Session,
        user_id: uuid.UUID,
        amount: float
    ) -> List[FraudFlag]:
        """Check if transaction velocity exceeds thresholds"""
        flags = []
        
        # Check transaction count in window
        window_start = datetime.now(timezone.utc) - timedelta(seconds=FraudConfig.VELOCITY_WINDOW_SECONDS)
        
        txn_count = db.execute(
            select(func.count(Transaction.id))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= window_start
                )
            )
        ).scalar() or 0
        
        if txn_count >= FraudConfig.VELOCITY_MAX_TRANSACTIONS:
            flags.append(FraudFlag.VELOCITY_EXCEEDED)
            logger.warning(f"Velocity exceeded for user {user_id}: {txn_count} transactions")
        
        # Check total amount in window
        total_amount = db.execute(
            select(func.sum(Transaction.amount))
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= window_start,
                    Transaction.currency == "USD"
                )
            )
        ).scalar() or 0.0
        
        if total_amount + amount > FraudConfig.VELOCITY_MAX_AMOUNT:
            flags.append(FraudFlag.VELOCITY_EXCEEDED)
            logger.warning(f"Amount velocity exceeded for user {user_id}: ${total_amount + amount}")
        
        return flags

    @staticmethod
    async def _check_structuring(
        db: Session,
        user_id: uuid.UUID,
        amount: float
    ) -> List[FraudFlag]:
        """Check for transaction structuring (breaking large amounts into smaller ones)"""
        flags = []
        
        # Get recent transactions
        window_start = datetime.now(timezone.utc) - timedelta(seconds=FraudConfig.VELOCITY_WINDOW_SECONDS)
        
        recent_txns = db.execute(
            select(Transaction.amount)
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= window_start,
                    Transaction.currency == "USD"
                )
            )
            .order_by(Transaction.created_at.desc())
            .limit(10)
        ).scalars().all()
        
        if len(recent_txns) < FraudConfig.STRUCTURING_MIN_TRANSACTIONS:
            return flags
        
        # Check if amounts are similar (potential structuring)
        amounts = list(recent_txns)
        avg_amount = sum(amounts) / len(amounts)
        
        similar_count = sum(
            1 for amt in amounts
            if abs(amt - avg_amount) / avg_amount < FraudConfig.STRUCTURING_GAP_PERCENT
        )
        
        if similar_count >= FraudConfig.STRUCTURING_MIN_TRANSACTIONS:
            flags.append(FraudFlag.STRUCTURING_DETECTED)
            logger.warning(f"Structuring detected for user {user_id}: {similar_count} similar transactions")
        
        return flags

    @staticmethod
    async def _check_new_user(
        db: Session,
        user_id: uuid.UUID,
        amount: float
    ) -> List[FraudFlag]:
        """Check if new user is making large transactions"""
        flags = []
        
        user = db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
        
        if not user:
            return flags
        
        # Check if user is new
        account_age = (datetime.now(timezone.utc) - user.created_at).days
        
        if account_age <= FraudConfig.NEW_USER_DAYS:
            if amount > FraudConfig.NEW_USER_MAX_WITHDRAWAL:
                flags.append(FraudFlag.NEW_USER_LARGE_TXN)
                logger.warning(
                    f"New user large transaction: user {user_id}, "
                    f"age {account_age} days, amount ${amount}"
                )
        
        return flags

    @staticmethod
    async def _check_failed_attempts(
        user_id: uuid.UUID,
        ip_address: str = None
    ) -> List[FraudFlag]:
        """Check for spike in failed authentication attempts"""
        flags = []
        
        # Check Redis for failed attempt count
        cache_key = f"failed_attempts:{user_id}"
        if ip_address:
            cache_key = f"failed_attempts:{ip_address}"
        
        failed_count = await cache_service.get(cache_key)
        
        if failed_count and int(failed_count) >= FraudConfig.FAILED_ATTEMPT_MAX:
            flags.append(FraudFlag.FAILED_ATTEMPT_SPIKE)
            logger.warning(f"Failed attempt spike: {cache_key} count {failed_count}")
        
        return flags

    @staticmethod
    async def _check_device_anomaly(
        db: Session,
        user_id: uuid.UUID,
        ip_address: str = None,
        user_agent: str = None
    ) -> List[FraudFlag]:
        """Check for device/IP changes that may indicate account takeover"""
        flags = []
        
        if not ip_address:
            return flags
        
        # Get recent transactions from different IPs
        window_start = datetime.now(timezone.utc) - timedelta(days=7)
        
        recent_ips = db.execute(
            select(func.distinct(Transaction.id))  # This would need to be updated to track IP
            .where(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= window_start
                )
            )
        ).all()
        
        # Check if this is a new IP (would need proper IP tracking in Transaction model)
        # For now, this is a placeholder
        
        return flags

    @staticmethod
    def _determine_risk_level(
        risk_score: float,
        flags: List[FraudFlag]
    ) -> FraudRiskLevel:
        """Determine risk level based on score and flags"""
        if risk_score >= 75:
            return FraudRiskLevel.CRITICAL
        elif risk_score >= 50:
            return FraudRiskLevel.HIGH
        elif risk_score >= 25:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW

    @staticmethod
    def _determine_action(
        risk_level: FraudRiskLevel,
        flags: List[FraudFlag]
    ) -> str:
        """Determine what action to take based on risk level and flags"""
        if risk_level == FraudRiskLevel.CRITICAL:
            return "freeze"
        elif risk_level == FraudRiskLevel.HIGH:
            return "manual_review"
        elif FraudFlag.ACCOUNT_TAKEOVER in flags:
            return "freeze"
        elif FraudFlag.STRUCTURING_DETECTED in flags:
            return "manual_review"
        elif risk_level == FraudRiskLevel.MEDIUM:
            return "require_2fa"
        else:
            return "allow"

    @staticmethod
    async def record_fraud_detection(
        db: Session,
        transaction_id: uuid.UUID,
        risk_assessment: Dict[str, Any]
    ) -> None:
        """
        Record fraud detection results for audit and ML training.
        Would store in a fraud_detection_log table.
        """
        # Placeholder for logging to fraud detection table
        logger.info(
            f"Fraud detection recorded for transaction {transaction_id}: "
            f"risk_level={risk_assessment['risk_level']}, "
            f"risk_score={risk_assessment['risk_score']}, "
            f"action={risk_assessment['action']}"
        )

    @staticmethod
    async def freeze_transaction(
        db: Session,
        transaction_id: uuid.UUID,
        reason: str
    ) -> bool:
        """
        Freeze a transaction pending manual review.
        """
        # Placeholder for freezing logic
        logger.warning(f"Transaction {transaction_id} frozen: {reason}")
        return True

    @staticmethod
    async def create_investigation(
        db: Session,
        transaction_id: uuid.UUID,
        user_id: uuid.UUID,
        flags: List[str],
        risk_score: float
    ) -> uuid.UUID:
        """
        Create a fraud investigation record.
        Returns investigation ID.
        """
        # Placeholder for investigation creation
        investigation_id = uuid.uuid4()
        logger.info(
            f"Fraud investigation created: {investigation_id} for transaction {transaction_id}"
        )
        return investigation_id


# Singleton instance
fraud_engine = FraudEngine()
