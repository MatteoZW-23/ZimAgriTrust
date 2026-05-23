"""
Fraud Detection Hooks and Safety Systems
Detects suspicious transactions, duplicate withdrawals, rapid payment spikes, webhook abuse, and retry storms
"""

import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.services.wallet_transaction_engine import Transaction
from app.services.payment_simulator import SimulationResult
from app.services.webhook_simulator import WebhookRecord


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert types"""
    SUSPICIOUS_TRANSACTION = "suspicious_transaction"
    DUPLICATE_WITHDRAWAL = "duplicate_withdrawal"
    RAPID_PAYMENT_SPIKE = "rapid_payment_spike"
    WEBHOOK_ABUSE = "webhook_abuse"
    RETRY_STORM = "retry_storm"
    UNUSUAL_IP_PATTERN = "unusual_ip_pattern"
    LARGE_TRANSACTION = "large_transaction"
    FREQUENT_FAILED_ATTEMPTS = "frequent_failed_attempts"
    BALANCE_ANOMALY = "balance_anomaly"
    ESCROW_ANOMALY = "escrow_anomaly"


@dataclass
class FraudAlert:
    """Fraud alert record"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    entity_id: str
    entity_type: str
    description: str
    detected_at: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type.value,
            "severity": self.severity.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
            "metadata": self.metadata
        }


@dataclass
class RiskScore:
    """Risk score for an entity"""
    entity_id: str
    entity_type: str
    score: float  # 0-100
    factors: Dict[str, float]
    calculated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "score": self.score,
            "factors": self.factors,
            "calculated_at": self.calculated_at.isoformat()
        }


class FraudDetectionSystem:
    """
    Fraud detection hooks and safety systems
    Detects suspicious transactions, duplicate withdrawals, rapid payment spikes, webhook abuse, and retry storms
    """
    
    def __init__(self):
        self._alerts: List[FraudAlert] = []
        self._risk_scores: Dict[str, RiskScore] = {}
        self._blocked_entities: Dict[str, datetime] = {}  # entity_id -> blocked_until
        
        # Configuration
        self.rapid_spike_threshold = 10  # payments in 1 minute
        self.large_transaction_threshold = 10000  # currency units
        self.failed_attempt_threshold = 5  # failed attempts in 5 minutes
        self.retry_storm_threshold = 20  # retries in 1 minute
        self.webhook_abuse_threshold = 50  # webhooks in 1 minute
        self.auto_block_enabled = True
        self.block_duration_minutes = 30
        
    async def check_transaction(
        self,
        transaction: Transaction,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> List[FraudAlert]:
        """
        Check a transaction for fraud indicators
        Returns list of alerts
        """
        alerts = []
        
        # Check if entity is blocked
        if user_id and self._is_entity_blocked(user_id):
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.SUSPICIOUS_TRANSACTION,
                severity=AlertSeverity.CRITICAL,
                entity_id=user_id,
                entity_type="user",
                description=f"Transaction attempted by blocked user: {user_id}",
                detected_at=datetime.utcnow(),
                metadata={"transaction_id": transaction.transaction_id}
            )
            alerts.append(alert)
            self._alerts.append(alert)
            return alerts
        
        # Check for large transaction
        if transaction.amount >= self.large_transaction_threshold:
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.LARGE_TRANSACTION,
                severity=AlertSeverity.HIGH,
                entity_id=transaction.transaction_id,
                entity_type="transaction",
                description=f"Large transaction detected: {transaction.amount}",
                detected_at=datetime.utcnow(),
                metadata={"amount": transaction.amount, "currency": transaction.currency}
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        # Check for unusual IP pattern (simplified)
        if ip_address and self._check_ip_anomaly(ip_address):
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.UNUSUAL_IP_PATTERN,
                severity=AlertSeverity.MEDIUM,
                entity_id=user_id or transaction.transaction_id,
                entity_type="user",
                description=f"Unusual IP pattern detected: {ip_address}",
                detected_at=datetime.utcnow(),
                metadata={"ip_address": ip_address}
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        return alerts
    
    async def check_withdrawal_pattern(
        self,
        user_id: str,
        recent_withdrawals: List[Transaction]
    ) -> List[FraudAlert]:
        """
        Check withdrawal pattern for duplicate or suspicious activity
        Returns list of alerts
        """
        alerts = []
        
        # Check for duplicate withdrawals (same amount, same user, short time)
        if len(recent_withdrawals) > 1:
            for i, withdrawal in enumerate(recent_withdrawals[:-1]):
                next_withdrawal = recent_withdrawals[i + 1]
                time_diff = (next_withdrawal.created_at - withdrawal.created_at).total_seconds()
                
                if withdrawal.amount == next_withdrawal.amount and time_diff < 60:
                    alert = FraudAlert(
                        alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                        alert_type=AlertType.DUPLICATE_WITHDRAWAL,
                        severity=AlertSeverity.HIGH,
                        entity_id=user_id,
                        entity_type="user",
                        description=f"Duplicate withdrawal detected: {withdrawal.amount}",
                        detected_at=datetime.utcnow(),
                        metadata={
                            "amount": withdrawal.amount,
                            "time_diff_seconds": time_diff,
                            "withdrawal_ids": [withdrawal.transaction_id, next_withdrawal.transaction_id]
                        }
                    )
                    alerts.append(alert)
                    self._alerts.append(alert)
        
        return alerts
    
    async def check_payment_spike(
        self,
        user_id: str,
        recent_payments: List[SimulationResult]
    ) -> List[FraudAlert]:
        """
        Check for rapid payment spike
        Returns list of alerts
        """
        alerts = []
        
        # Count payments in last minute
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_count = sum(1 for p in recent_payments if p.started_at >= one_minute_ago)
        
        if recent_count >= self.rapid_spike_threshold:
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.RAPID_PAYMENT_SPIKE,
                severity=AlertSeverity.HIGH,
                entity_id=user_id,
                entity_type="user",
                description=f"Rapid payment spike detected: {recent_count} payments in 1 minute",
                detected_at=datetime.utcnow(),
                metadata={"payment_count": recent_count, "threshold": self.rapid_spike_threshold}
            )
            alerts.append(alert)
            self._alerts.append(alert)
            
            # Auto-block if enabled
            if self.auto_block_enabled:
                await self.block_entity(user_id, "Rapid payment spike")
        
        return alerts
    
    async def check_webhook_abuse(
        self,
        webhook_records: List[WebhookRecord]
    ) -> List[FraudAlert]:
        """
        Check for webhook abuse
        Returns list of alerts
        """
        alerts = []
        
        # Count webhooks in last minute
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        recent_count = sum(1 for w in webhook_records if w.created_at >= one_minute_ago)
        
        if recent_count >= self.webhook_abuse_threshold:
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.WEBHOOK_ABUSE,
                severity=AlertSeverity.HIGH,
                entity_id="webhook_system",
                entity_type="system",
                description=f"Webhook abuse detected: {recent_count} webhooks in 1 minute",
                detected_at=datetime.utcnow(),
                metadata={"webhook_count": recent_count, "threshold": self.webhook_abuse_threshold}
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        return alerts
    
    async def check_retry_storm(
        self,
        retry_count: int,
        time_window_seconds: int = 60
    ) -> List[FraudAlert]:
        """
        Check for retry storm
        Returns list of alerts
        """
        alerts = []
        
        if retry_count >= self.retry_storm_threshold:
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.RETRY_STORM,
                severity=AlertSeverity.HIGH,
                entity_id="queue_system",
                entity_type="system",
                description=f"Retry storm detected: {retry_count} retries in {time_window_seconds} seconds",
                detected_at=datetime.utcnow(),
                metadata={"retry_count": retry_count, "threshold": self.retry_storm_threshold}
            )
            alerts.append(alert)
            self._alerts.append(alert)
        
        return alerts
    
    async def check_failed_attempts(
        self,
        user_id: str,
        failed_attempts: List[Any]
    ) -> List[FraudAlert]:
        """
        Check for frequent failed attempts
        Returns list of alerts
        """
        alerts = []
        
        # Count failed attempts in last 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_count = sum(1 for a in failed_attempts if getattr(a, 'created_at', datetime.utcnow()) >= five_minutes_ago)
        
        if recent_count >= self.failed_attempt_threshold:
            alert = FraudAlert(
                alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                alert_type=AlertType.FREQUENT_FAILED_ATTEMPTS,
                severity=AlertSeverity.HIGH,
                entity_id=user_id,
                entity_type="user",
                description=f"Frequent failed attempts detected: {recent_count} in 5 minutes",
                detected_at=datetime.utcnow(),
                metadata={"failed_count": recent_count, "threshold": self.failed_attempt_threshold}
            )
            alerts.append(alert)
            self._alerts.append(alert)
            
            # Auto-block if enabled
            if self.auto_block_enabled:
                await self.block_entity(user_id, "Frequent failed attempts")
        
        return alerts
    
    async def check_balance_anomaly(
        self,
        wallet_id: str,
        current_balance: float,
        previous_balance: float,
        time_diff_hours: float
    ) -> List[FraudAlert]:
        """
        Check for balance anomaly
        Returns list of alerts
        """
        alerts = []
        
        # Calculate percentage change
        if previous_balance > 0:
            change_percent = abs((current_balance - previous_balance) / previous_balance) * 100
            
            # Alert if change is more than 50% in less than 1 hour
            if change_percent > 50 and time_diff_hours < 1:
                alert = FraudAlert(
                    alert_id=f"ALT_{uuid.uuid4().hex[:16]}",
                    alert_type=AlertType.BALANCE_ANOMALY,
                    severity=AlertSeverity.MEDIUM,
                    entity_id=wallet_id,
                    entity_type="wallet",
                    description=f"Balance anomaly detected: {change_percent:.2f}% change in {time_diff_hours:.2f} hours",
                    detected_at=datetime.utcnow(),
                    metadata={
                        "current_balance": current_balance,
                        "previous_balance": previous_balance,
                        "change_percent": change_percent,
                        "time_diff_hours": time_diff_hours
                    }
                )
                alerts.append(alert)
                self._alerts.append(alert)
        
        return alerts
    
    async def calculate_risk_score(
        self,
        entity_id: str,
        entity_type: str,
        factors: Dict[str, float]
    ) -> RiskScore:
        """
        Calculate risk score for an entity
        Returns risk score
        """
        # Weighted average of factors
        weights = {
            "transaction_frequency": 0.2,
            "amount_variance": 0.15,
            "failed_attempts": 0.25,
            "ip_anomaly": 0.15,
            "time_pattern": 0.15,
            "geographic_anomaly": 0.1
        }
        
        score = 0.0
        total_weight = 0.0
        
        for factor_name, factor_value in factors.items():
            weight = weights.get(factor_name, 0.1)
            score += factor_value * weight
            total_weight += weight
        
        if total_weight > 0:
            score = score / total_weight
        
        # Normalize to 0-100
        score = min(max(score * 100, 0), 100)
        
        risk_score = RiskScore(
            entity_id=entity_id,
            entity_type=entity_type,
            score=score,
            factors=factors,
            calculated_at=datetime.utcnow()
        )
        
        self._risk_scores[f"{entity_type}:{entity_id}"] = risk_score
        return risk_score
    
    async def block_entity(
        self,
        entity_id: str,
        reason: str
    ) -> None:
        """Block an entity for a duration"""
        block_until = datetime.utcnow() + timedelta(minutes=self.block_duration_minutes)
        self._blocked_entities[entity_id] = block_until
    
    def _is_entity_blocked(self, entity_id: str) -> bool:
        """Check if an entity is currently blocked"""
        if entity_id not in self._blocked_entities:
            return False
        
        block_until = self._blocked_entities[entity_id]
        if datetime.utcnow() < block_until:
            return True
        
        # Block expired, remove it
        del self._blocked_entities[entity_id]
        return False
    
    async def unblock_entity(self, entity_id: str) -> None:
        """Unblock an entity"""
        if entity_id in self._blocked_entities:
            del self._blocked_entities[entity_id]
    
    def get_alert(self, alert_id: str) -> Optional[FraudAlert]:
        """Get alert by ID"""
        for alert in self._alerts:
            if alert.alert_id == alert_id:
                return alert
        return None
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[FraudAlert]:
        """Get alerts by type"""
        return [a for a in self._alerts if a.alert_type == alert_type]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[FraudAlert]:
        """Get alerts by severity"""
        return [a for a in self._alerts if a.severity == severity]
    
    def get_unresolved_alerts(self) -> List[FraudAlert]:
        """Get all unresolved alerts"""
        return [a for a in self._alerts if not a.resolved]
    
    def get_alerts_by_entity(self, entity_id: str) -> List[FraudAlert]:
        """Get alerts for an entity"""
        return [a for a in self._alerts if a.entity_id == entity_id]
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolution: str
    ) -> FraudAlert:
        """Resolve an alert"""
        alert = self.get_alert(alert_id)
        if not alert:
            raise ValueError(f"Alert not found: {alert_id}")
        
        alert.resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolution = resolution
        
        return alert
    
    def get_risk_score(self, entity_id: str, entity_type: str) -> Optional[RiskScore]:
        """Get risk score for an entity"""
        return self._risk_scores.get(f"{entity_type}:{entity_id}")
    
    def get_fraud_stats(self) -> Dict[str, Any]:
        """Get fraud detection statistics"""
        total_alerts = len(self._alerts)
        if total_alerts == 0:
            return {"total_alerts": 0, "resolved": 0, "unresolved": 0, "by_type": {}, "by_severity": {}}
        
        resolved = len([a for a in self._alerts if a.resolved])
        unresolved = total_alerts - resolved
        
        # Alert type breakdown
        by_type = {}
        for alert in self._alerts:
            atype = alert.alert_type.value
            by_type[atype] = by_type.get(atype, 0) + 1
        
        # Severity breakdown
        by_severity = {}
        for alert in self._alerts:
            sev = alert.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            "total_alerts": total_alerts,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": (resolved / total_alerts) * 100,
            "by_type": by_type,
            "by_severity": by_severity,
            "blocked_entities": len(self._blocked_entities)
        }
    
    def _check_ip_anomaly(self, ip_address: str) -> bool:
        """Check if IP address is anomalous (simplified)"""
        # In a real system, this would check against known patterns, geolocation, etc.
        # For simulation, we'll just check for some basic patterns
        if ip_address.startswith("192.168.") or ip_address.startswith("10."):
            return False  # Internal IPs are fine
        return False  # Simplified - always return False for simulation
    
    def clear_all(self) -> None:
        """Clear all data (for testing)"""
        self._alerts.clear()
        self._risk_scores.clear()
        self._blocked_entities.clear()


# Global fraud detection system instance
fraud_detection_system = FraudDetectionSystem()
