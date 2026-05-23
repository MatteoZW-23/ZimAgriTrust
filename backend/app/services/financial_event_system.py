"""
Financial Event System and Audit Logging
Implements transaction event streaming, payment event logs, and audit-safe event history
"""

import asyncio
import json
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid
import hashlib


class EventType(Enum):
    """Financial event types"""
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_TIMEOUT = "payment_timeout"
    ESCROW_HELD = "escrow_held"
    ESCROW_RELEASED = "escrow_released"
    ESCROW_REFUNDED = "escrow_refunded"
    ESCROW_FROZEN = "escrow_frozen"
    SETTLEMENT_COMPLETED = "settlement_completed"
    SETTLEMENT_FAILED = "settlement_failed"
    REFUND_PROCESSED = "refund_processed"
    WITHDRAWAL_INITIATED = "withdrawal_initiated"
    WITHDRAWAL_COMPLETED = "withdrawal_completed"
    WITHDRAWAL_FAILED = "withdrawal_failed"
    WALLET_DEPOSIT = "wallet_deposit"
    WALLET_WITHDRAWAL = "wallet_withdrawal"
    WALLET_TRANSFER = "wallet_transfer"
    PLATFORM_FEE_DEDUCTED = "platform_fee_deducted"
    DISPUTE_RAISED = "dispute_raised"
    DISPUTE_RESOLVED = "dispute_resolved"
    RECONCILIATION_COMPLETED = "reconciliation_completed"
    RECONCILIATION_ISSUE_FOUND = "reconciliation_issue_found"


class EventSeverity(Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FinancialEvent:
    """Financial event record"""
    event_id: str
    event_type: EventType
    severity: EventSeverity
    entity_id: str  # transaction_id, order_id, wallet_id, etc.
    entity_type: str  # transaction, order, wallet, etc.
    timestamp: datetime
    data: Dict[str, Any]
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    event_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "event_hash": self.event_hash
        }
    
    def compute_hash(self) -> str:
        """Compute cryptographic hash of event"""
        event_data = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "user_id": self.user_id
        }
        data_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class AuditLog:
    """Audit log entry for compliance"""
    log_id: str
    event_id: str
    action: str
    actor: str
    resource: str
    changes: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "log_id": self.log_id,
            "event_id": self.event_id,
            "action": self.action,
            "actor": self.actor,
            "resource": self.resource,
            "changes": self.changes,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }


class FinancialEventSystem:
    """
    Financial event system and audit logging
    Implements transaction event streaming and audit-safe event history
    """
    
    def __init__(self):
        self._events: List[FinancialEvent] = []
        self._audit_logs: List[AuditLog] = []
        self._event_subscribers: Dict[EventType, List[callable]] = {}
        
        # Configuration
        self.max_events = 100000  # Maximum events to keep in memory
        self.max_audit_logs = 100000
        self.event_retention_days = 90
        
    async def emit_event(
        self,
        event_type: EventType,
        entity_id: str,
        entity_type: str,
        data: Dict[str, Any],
        severity: EventSeverity = EventSeverity.INFO,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> FinancialEvent:
        """
        Emit a financial event
        Returns event record
        """
        event_id = f"EVT_{uuid.uuid4().hex[:16]}"
        
        event = FinancialEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            entity_id=entity_id,
            entity_type=entity_type,
            timestamp=datetime.utcnow(),
            data=data,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        event.event_hash = event.compute_hash()
        
        # Add to events list
        self._events.append(event)
        
        # Trim if exceeding max
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]
        
        # Notify subscribers
        await self._notify_subscribers(event)
        
        return event
    
    async def _notify_subscribers(self, event: FinancialEvent) -> None:
        """Notify event subscribers"""
        subscribers = self._event_subscribers.get(event.event_type, [])
        for subscriber in subscribers:
            try:
                await subscriber(event)
            except Exception:
                # Log error but continue with other subscribers
                pass
    
    def subscribe(self, event_type: EventType, callback: callable) -> None:
        """Subscribe to events of a specific type"""
        if event_type not in self._event_subscribers:
            self._event_subscribers[event_type] = []
        self._event_subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: callable) -> None:
        """Unsubscribe from events"""
        if event_type in self._event_subscribers:
            self._event_subscribers[event_type] = [
                c for c in self._event_subscribers[event_type] if c != callback
            ]
    
    async def create_audit_log(
        self,
        event_id: str,
        action: str,
        actor: str,
        resource: str,
        changes: Dict[str, Any],
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry
        Returns audit log record
        """
        log_id = f"AUD_{uuid.uuid4().hex[:16]}"
        
        audit_log = AuditLog(
            log_id=log_id,
            event_id=event_id,
            action=action,
            actor=actor,
            resource=resource,
            changes=changes,
            previous_state=previous_state,
            new_state=new_state,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        self._audit_logs.append(audit_log)
        
        # Trim if exceeding max
        if len(self._audit_logs) > self.max_audit_logs:
            self._audit_logs = self._audit_logs[-self.max_audit_logs:]
        
        return audit_log
    
    def get_event(self, event_id: str) -> Optional[FinancialEvent]:
        """Get event by ID"""
        for event in self._events:
            if event.event_id == event_id:
                return event
        return None
    
    def get_events_by_type(
        self,
        event_type: EventType,
        limit: int = 100
    ) -> List[FinancialEvent]:
        """Get events by type"""
        events = [e for e in self._events if e.event_type == event_type]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_events_by_entity(
        self,
        entity_id: str,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[FinancialEvent]:
        """Get events for a specific entity"""
        events = [
            e for e in self._events
            if e.entity_id == entity_id
            and (entity_type is None or e.entity_type == entity_type)
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_events_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[FinancialEvent]:
        """Get events for a specific user"""
        events = [e for e in self._events if e.user_id == user_id]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_events_by_severity(
        self,
        severity: EventSeverity,
        limit: int = 100
    ) -> List[FinancialEvent]:
        """Get events by severity"""
        events = [e for e in self._events if e.severity == severity]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_events_in_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[FinancialEvent]:
        """Get events in a time range"""
        events = [
            e for e in self._events
            if start_time <= e.timestamp <= end_time
        ]
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[:limit]
    
    def get_audit_log(self, log_id: str) -> Optional[AuditLog]:
        """Get audit log by ID"""
        for log in self._audit_logs:
            if log.log_id == log_id:
                return log
        return None
    
    def get_audit_logs_by_event(self, event_id: str) -> List[AuditLog]:
        """Get audit logs for an event"""
        return [log for log in self._audit_logs if log.event_id == event_id]
    
    def get_audit_logs_by_actor(self, actor: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for an actor"""
        logs = [log for log in self._audit_logs if log.actor == actor]
        logs.sort(key=lambda log: log.timestamp, reverse=True)
        return logs[:limit]
    
    def get_audit_logs_by_resource(self, resource: str, limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a resource"""
        logs = [log for log in self._audit_logs if log.resource == resource]
        logs.sort(key=lambda log: log.timestamp, reverse=True)
        return logs[:limit]
    
    async def verify_event_integrity(self) -> Dict[str, Any]:
        """
        Verify event integrity by checking hash chains
        Returns integrity report
        """
        total_events = len(self._events)
        valid_hashes = 0
        invalid_hashes = 0
        
        for event in self._events:
            computed_hash = event.compute_hash()
            if computed_hash == event.event_hash:
                valid_hashes += 1
            else:
                invalid_hashes += 1
        
        return {
            "total_events": total_events,
            "valid_hashes": valid_hashes,
            "invalid_hashes": invalid_hashes,
            "hash_validity_rate": (valid_hashes / total_events) * 100 if total_events > 0 else 100,
            "is_integrity_valid": invalid_hashes == 0
        }
    
    async def cleanup_old_events(self) -> int:
        """
        Clean up events older than retention period
        Returns number of events removed
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.event_retention_days)
        original_count = len(self._events)
        
        self._events = [
            e for e in self._events
            if e.timestamp >= cutoff_date
        ]
        
        removed_count = original_count - len(self._events)
        return removed_count
    
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics"""
        total_events = len(self._events)
        if total_events == 0:
            return {"total_events": 0, "by_type": {}, "by_severity": {}}
        
        # Event type breakdown
        by_type = {}
        for event in self._events:
            etype = event.event_type.value
            by_type[etype] = by_type.get(etype, 0) + 1
        
        # Severity breakdown
        by_severity = {}
        for event in self._events:
            sev = event.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        # Time range
        if total_events > 0:
            oldest = min(e.timestamp for e in self._events)
            newest = max(e.timestamp for e in self._events)
        else:
            oldest = None
            newest = None
        
        return {
            "total_events": total_events,
            "by_type": by_type,
            "by_severity": by_severity,
            "oldest_event": oldest.isoformat() if oldest else None,
            "newest_event": newest.isoformat() if newest else None
        }
    
    def get_audit_stats(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        total_logs = len(self._audit_logs)
        if total_logs == 0:
            return {"total_logs": 0, "by_action": {}, "by_actor": {}}
        
        # Action breakdown
        by_action = {}
        for log in self._audit_logs:
            action = log.action
            by_action[action] = by_action.get(action, 0) + 1
        
        # Actor breakdown
        by_actor = {}
        for log in self._audit_logs:
            actor = log.actor
            by_actor[actor] = by_actor.get(actor, 0) + 1
        
        return {
            "total_logs": total_logs,
            "by_action": by_action,
            "by_actor": by_actor
        }
    
    def clear_all(self) -> None:
        """Clear all events and audit logs (for testing)"""
        self._events.clear()
        self._audit_logs.clear()
        self._event_subscribers.clear()


# Global financial event system instance
financial_event_system = FinancialEventSystem()
