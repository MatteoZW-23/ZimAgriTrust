"""
Admin Financial Dashboards API
Provides endpoints for payment monitoring, settlement dashboard, reconciliation dashboard, failed transaction dashboard, escrow dashboard, refund dashboard, and fraud monitoring dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.payment_simulator import payment_simulator
from app.services.webhook_simulator import webhook_simulator
from app.services.escrow_simulator import escrow_simulator
from app.services.wallet_transaction_engine import wallet_transaction_engine
from app.services.settlement_simulator import SettlementSimulator
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.queue_system import queue_system
from app.services.financial_event_system import financial_event_system
from app.services.fraud_detection import fraud_detection_system


router = APIRouter()


# Initialize engines with dependencies
settlement_simulator = SettlementSimulator(wallet_transaction_engine)
reconciliation_engine = ReconciliationEngine(wallet_transaction_engine)


class DashboardResponse(BaseModel):
    """Standard dashboard response"""
    success: bool
    data: Dict[str, Any]
    timestamp: datetime


class PaymentDashboardResponse(BaseModel):
    """Payment monitoring dashboard response"""
    total_payments: int
    successful_payments: int
    failed_payments: int
    success_rate: float
    total_amount: float
    avg_payment_amount: float
    payments_by_provider: Dict[str, int]
    payments_by_status: Dict[str, int]
    recent_payments: List[Dict[str, Any]]


class SettlementDashboardResponse(BaseModel):
    """Settlement dashboard response"""
    total_items: int
    pending_items: int
    completed_items: int
    failed_items: int
    total_amount: float
    total_platform_fees: float
    total_net_amount: float
    completion_rate: float
    recent_batches: List[Dict[str, Any]]


class ReconciliationDashboardResponse(BaseModel):
    """Reconciliation dashboard response"""
    total_reports: int
    total_issues: int
    resolved_issues: int
    unresolved_issues: int
    resolution_rate: float
    issues_by_type: Dict[str, int]
    issues_by_severity: Dict[str, int]
    latest_report: Optional[Dict[str, Any]]


class EscrowDashboardResponse(BaseModel):
    """Escrow dashboard response"""
    total_escrows: int
    held_escrows: int
    released_escrows: int
    frozen_escrows: int
    refunded_escrows: int
    total_amount: float
    held_amount: float
    released_amount: float
    active_disputes: int


class FraudDashboardResponse(BaseModel):
    """Fraud monitoring dashboard response"""
    total_alerts: int
    resolved_alerts: int
    unresolved_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    blocked_entities: int
    alerts_by_type: Dict[str, int]
    recent_alerts: List[Dict[str, Any]]


class QueueDashboardResponse(BaseModel):
    """Queue monitoring dashboard response"""
    payment_queue: Dict[str, int]
    webhook_queue: Dict[str, int]
    settlement_queue: Dict[str, int]
    reconciliation_queue: Dict[str, int]
    notification_queue: Dict[str, int]
    withdrawal_queue: Dict[str, int]
    dead_letter_queue: int
    total_pending: int
    total_processing: int


class LedgerDashboardResponse(BaseModel):
    """Ledger integrity dashboard response"""
    total_entries: int
    valid_hashes: int
    invalid_hashes: int
    hash_validity_rate: float
    total_debits: float
    total_credits: float
    is_balanced: bool
    total_wallets: int
    total_balance: float


@router.get("/dashboard/payment", response_model=PaymentDashboardResponse)
async def get_payment_dashboard(
    hours: int = Query(24, description="Time range in hours")
) -> PaymentDashboardResponse:
    """
    Get payment monitoring dashboard data
    """
    stats = payment_simulator.get_simulation_stats()
    history = payment_simulator.get_simulation_history(limit=100)
    
    # Calculate provider breakdown
    payments_by_provider = {}
    payments_by_status = {}
    total_amount = 0
    successful_amount = 0
    
    for sim in history:
        provider = sim.provider
        status = sim.status.value
        
        payments_by_provider[provider] = payments_by_provider.get(provider, 0) + 1
        payments_by_status[status] = payments_by_status.get(status, 0) + 1
        
        total_amount += sim.amount
        if sim.success:
            successful_amount += sim.amount
    
    avg_payment_amount = total_amount / len(history) if history else 0
    
    return PaymentDashboardResponse(
        total_payments=stats["total"],
        successful_payments=stats["success"],
        failed_payments=stats["failure"],
        success_rate=stats["success_rate"],
        total_amount=total_amount,
        avg_payment_amount=avg_payment_amount,
        payments_by_provider=payments_by_provider,
        payments_by_status=payments_by_status,
        recent_payments=[{
            "transaction_id": s.transaction_id,
            "provider": s.provider,
            "amount": s.amount,
            "status": s.status.value,
            "scenario": s.scenario.value,
            "created_at": s.started_at.isoformat()
        } for s in history[:20]]
    )


@router.get("/dashboard/settlement", response_model=SettlementDashboardResponse)
async def get_settlement_dashboard() -> SettlementDashboardResponse:
    """
    Get settlement dashboard data
    """
    stats = settlement_simulator.get_settlement_stats()
    batch_stats = settlement_simulator.get_batch_stats()
    
    # Get recent batches
    recent_batches = []
    for batch_id in list(settlement_simulator._settlement_batches.keys())[-10:]:
        batch = settlement_simulator.get_settlement_batch(batch_id)
        if batch:
            recent_batches.append(batch.to_dict())
    
    return SettlementDashboardResponse(
        total_items=stats["total_items"],
        pending_items=stats["pending"],
        completed_items=stats["completed"],
        failed_items=stats["failed"],
        total_amount=stats["total_amount"],
        total_platform_fees=stats["total_platform_fee"],
        total_net_amount=stats["total_net_amount"],
        completion_rate=stats["completion_rate"],
        recent_batches=recent_batches
    )


@router.get("/dashboard/reconciliation", response_model=ReconciliationDashboardResponse)
async def get_reconciliation_dashboard() -> ReconciliationDashboardResponse:
    """
    Get reconciliation dashboard data
    """
    stats = reconciliation_engine.get_reconciliation_stats()
    latest_report = reconciliation_engine.get_latest_report()
    
    return ReconciliationDashboardResponse(
        total_reports=stats["total_reports"],
        total_issues=stats["total_issues"],
        resolved_issues=stats["resolved"],
        unresolved_issues=stats["unresolved"],
        resolution_rate=stats["resolution_rate"],
        issues_by_type=stats["issue_types"],
        issues_by_severity=stats["severities"],
        latest_report=latest_report.to_dict() if latest_report else None
    )


@router.get("/dashboard/escrow", response_model=EscrowDashboardResponse)
async def get_escrow_dashboard() -> EscrowDashboardResponse:
    """
    Get escrow dashboard data
    """
    escrow_stats = escrow_simulator.get_escrow_stats()
    dispute_stats = escrow_simulator.get_dispute_stats()
    
    return EscrowDashboardResponse(
        total_escrows=escrow_stats["total"],
        held_escrows=escrow_stats["held"],
        released_escrows=escrow_stats["released"],
        frozen_escrows=escrow_stats["frozen"],
        refunded_escrows=escrow_stats["refunded"],
        total_amount=escrow_stats["total_amount"],
        held_amount=escrow_stats["held_amount"],
        released_amount=escrow_stats["released_amount"],
        active_disputes=dispute_stats["open"] + dispute_stats["under_review"]
    )


@router.get("/dashboard/fraud", response_model=FraudDashboardResponse)
async def get_fraud_dashboard() -> FraudDashboardResponse:
    """
    Get fraud monitoring dashboard data
    """
    stats = fraud_detection_system.get_fraud_stats()
    unresolved_alerts = fraud_detection_system.get_unresolved_alerts()
    
    # Count by severity
    critical = len([a for a in unresolved_alerts if a.severity.value == "critical"])
    high = len([a for a in unresolved_alerts if a.severity.value == "high"])
    medium = len([a for a in unresolved_alerts if a.severity.value == "medium"])
    low = len([a for a in unresolved_alerts if a.severity.value == "low"])
    
    # Recent alerts
    recent_alerts = []
    for alert in fraud_detection_system._alerts[-20:]:
        recent_alerts.append(alert.to_dict())
    
    return FraudDashboardResponse(
        total_alerts=stats["total_alerts"],
        resolved_alerts=stats["resolved"],
        unresolved_alerts=stats["unresolved"],
        critical_alerts=critical,
        high_alerts=high,
        medium_alerts=medium,
        low_alerts=low,
        blocked_entities=stats["blocked_entities"],
        alerts_by_type=stats["by_type"],
        recent_alerts=recent_alerts
    )


@router.get("/dashboard/queue", response_model=QueueDashboardResponse)
async def get_queue_dashboard() -> QueueDashboardResponse:
    """
    Get queue monitoring dashboard data
    """
    queue_stats = queue_system.get_queue_stats()
    
    total_pending = sum(q["pending"] for q in queue_stats.values() if isinstance(q, dict))
    total_processing = sum(q["processing"] for q in queue_stats.values() if isinstance(q, dict))
    
    return QueueDashboardResponse(
        payment_queue=queue_stats.get("payment", {}),
        webhook_queue=queue_stats.get("webhook", {}),
        settlement_queue=queue_stats.get("settlement", {}),
        reconciliation_queue=queue_stats.get("reconciliation", {}),
        notification_queue=queue_stats.get("notification", {}),
        withdrawal_queue=queue_stats.get("withdrawal", {}),
        dead_letter_queue=queue_stats.get("dead_letter", {}).get("total", 0),
        total_pending=total_pending,
        total_processing=total_processing
    )


@router.get("/dashboard/ledger", response_model=LedgerDashboardResponse)
async def get_ledger_dashboard() -> LedgerDashboardResponse:
    """
    Get ledger integrity dashboard data
    """
    integrity = wallet_transaction_engine.verify_ledger_integrity()
    wallet_stats = wallet_transaction_engine.get_wallet_stats()
    
    return LedgerDashboardResponse(
        total_entries=integrity["total_entries"],
        valid_hashes=integrity["valid_hashes"],
        invalid_hashes=integrity["invalid_hashes"],
        hash_validity_rate=integrity["hash_validity_rate"],
        total_debits=integrity["total_debits"],
        total_credits=integrity["total_credits"],
        is_balanced=integrity["is_balanced"],
        total_wallets=wallet_stats["total_wallets"],
        total_balance=wallet_stats["total_balance"]
    )


@router.get("/dashboard/webhook", response_model=DashboardResponse)
async def get_webhook_dashboard() -> DashboardResponse:
    """
    Get webhook monitoring dashboard data
    """
    stats = webhook_simulator.get_webhook_stats()
    pending_webhooks = webhook_simulator.get_webhooks_by_status(
        webhook_simulator.WebhookDeliveryStatus.PENDING
    )
    
    return DashboardResponse(
        success=True,
        data={
            "total_webhooks": stats["total"],
            "delivered": stats["delivered"],
            "failed": stats["failed"],
            "pending": stats["pending"],
            "retrying": stats["retrying"],
            "expired": stats["expired"],
            "delivery_rate": stats["delivery_rate"],
            "avg_attempts": stats["avg_attempts"],
            "pending_count": len(pending_webhooks)
        },
        timestamp=datetime.utcnow()
    )


@router.get("/dashboard/events", response_model=DashboardResponse)
async def get_events_dashboard(
    hours: int = Query(24, description="Time range in hours")
) -> DashboardResponse:
    """
    Get financial events dashboard data
    """
    event_stats = financial_event_system.get_event_stats()
    audit_stats = financial_event_system.get_audit_stats()
    
    # Get recent events
    start_time = datetime.utcnow() - timedelta(hours=hours)
    recent_events = financial_event_system.get_events_in_time_range(start_time, datetime.utcnow(), limit=100)
    
    return DashboardResponse(
        success=True,
        data={
            "total_events": event_stats["total_events"],
            "by_type": event_stats["by_type"],
            "by_severity": event_stats["by_severity"],
            "oldest_event": event_stats["oldest_event"],
            "newest_event": event_stats["newest_event"],
            "total_audit_logs": audit_stats["total_logs"],
            "by_action": audit_stats["by_action"],
            "recent_events_count": len(recent_events),
            "recent_events": [e.to_dict() for e in recent_events[:20]]
        },
        timestamp=datetime.utcnow()
    )


@router.get("/dashboard/overview", response_model=DashboardResponse)
async def get_overview_dashboard() -> DashboardResponse:
    """
    Get comprehensive overview dashboard data
    """
    payment_stats = payment_simulator.get_simulation_stats()
    settlement_stats = settlement_simulator.get_settlement_stats()
    escrow_stats = escrow_simulator.get_escrow_stats()
    fraud_stats = fraud_detection_system.get_fraud_stats()
    queue_stats = queue_system.get_queue_stats()
    wallet_stats = wallet_transaction_engine.get_wallet_stats()
    
    return DashboardResponse(
        success=True,
        data={
            "payments": {
                "total": payment_stats["total"],
                "success_rate": payment_stats["success_rate"],
                "total_amount": payment_stats.get("total_amount", 0)
            },
            "settlements": {
                "total_items": settlement_stats["total_items"],
                "pending": settlement_stats["pending"],
                "completed": settlement_stats["completed"],
                "total_amount": settlement_stats["total_amount"]
            },
            "escrow": {
                "total": escrow_stats["total"],
                "held": escrow_stats["held"],
                "held_amount": escrow_stats["held_amount"]
            },
            "fraud": {
                "total_alerts": fraud_stats["total_alerts"],
                "unresolved": fraud_stats["unresolved"],
                "blocked_entities": fraud_stats["blocked_entities"]
            },
            "queues": {
                "total_pending": sum(q["pending"] for q in queue_stats.values() if isinstance(q, dict)),
                "total_processing": sum(q["processing"] for q in queue_stats.values() if isinstance(q, dict)),
                "dead_letter": queue_stats.get("dead_letter", {}).get("total", 0)
            },
            "wallets": {
                "total_wallets": wallet_stats["total_wallets"],
                "total_balance": wallet_stats["total_balance"]
            }
        },
        timestamp=datetime.utcnow()
    )
