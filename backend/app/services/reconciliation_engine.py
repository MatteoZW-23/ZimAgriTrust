"""
Reconciliation Engine with Daily Jobs
Detects orphaned transactions, duplicate payments, balance mismatches, and webhook mismatches
"""

import asyncio
import random
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import uuid

from app.services.wallet_transaction_engine import WalletTransactionEngine
from app.services.payment_simulator import SimulationResult
from app.services.webhook_simulator import WebhookRecord


class ReconciliationStatus(Enum):
    """Reconciliation status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class IssueType(Enum):
    """Issue types detected by reconciliation"""
    ORPHANED_TRANSACTION = "orphaned_transaction"
    DUPLICATE_PAYMENT = "duplicate_payment"
    BALANCE_MISMATCH = "balance_mismatch"
    WEBHOOK_MISMATCH = "webhook_mismatch"
    FAILED_SETTLEMENT = "failed_settlement"
    MISSING_LEDGER_ENTRY = "missing_ledger_entry"
    ESCROW_MISMATCH = "escrow_mismatch"
    PLATFORM_FEE_MISMATCH = "platform_fee_mismatch"


@dataclass
class ReconciliationIssue:
    """Reconciliation issue record"""
    issue_id: str
    issue_type: IssueType
    severity: str  # critical, high, medium, low
    description: str
    entity_id: str  # transaction_id, order_id, etc.
    entity_type: str  # transaction, order, wallet, etc.
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "issue_id": self.issue_id,
            "issue_type": self.issue_type.value,
            "severity": self.severity,
            "description": self.description,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution": self.resolution,
            "metadata": self.metadata
        }


@dataclass
class ReconciliationReport:
    """Reconciliation report"""
    report_id: str
    report_date: datetime
    status: ReconciliationStatus
    total_transactions_checked: int
    total_issues_found: int
    issues_by_type: Dict[str, int]
    issues_by_severity: Dict[str, int]
    started_at: datetime
    completed_at: Optional[datetime] = None
    issues: List[ReconciliationIssue] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "report_id": self.report_id,
            "report_date": self.report_date.isoformat(),
            "status": self.status.value,
            "total_transactions_checked": self.total_transactions_checked,
            "total_issues_found": self.total_issues_found,
            "issues_by_type": self.issues_by_type,
            "issues_by_severity": self.issues_by_severity,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "issues": [issue.to_dict() for issue in self.issues] if self.issues else [],
            "metadata": self.metadata
        }


class ReconciliationEngine:
    """
    Reconciliation engine with daily jobs
    Detects orphaned transactions, duplicate payments, balance mismatches, and webhook mismatches
    """
    
    def __init__(self, wallet_engine: WalletTransactionEngine):
        self.wallet_engine = wallet_engine
        self._reports: Dict[str, ReconciliationReport] = {}
        self._issues: Dict[str, ReconciliationIssue] = {}
        
        # Configuration
        self.auto_reconcile_enabled = True
        self.reconciliation_interval_hours = 24
        self.balance_tolerance = 0.01  # 1 cent tolerance
        
    async def run_daily_reconciliation(
        self,
        payment_simulations: List[SimulationResult] = None,
        webhook_records: List[WebhookRecord] = None,
        escrow_data: Dict[str, Any] = None
    ) -> ReconciliationReport:
        """
        Run daily reconciliation job
        Returns reconciliation report
        """
        report_id = f"REC_{uuid.uuid4().hex[:16]}"
        report_date = datetime.utcnow()
        
        report = ReconciliationReport(
            report_id=report_id,
            report_date=report_date,
            status=ReconciliationStatus.IN_PROGRESS,
            total_transactions_checked=0,
            total_issues_found=0,
            issues_by_type={},
            issues_by_severity={},
            started_at=datetime.utcnow(),
            issues=[]
        )
        
        self._reports[report_id] = report
        
        try:
            # Check for orphaned transactions
            await self._check_orphaned_transactions(report, payment_simulations)
            
            # Check for duplicate payments
            await self._check_duplicate_payments(report, payment_simulations)
            
            # Check for balance mismatches
            await self._check_balance_mismatches(report)
            
            # Check for webhook mismatches
            await self._check_webhook_mismatches(report, webhook_records)
            
            # Check for failed settlements
            await self._check_failed_settlements(report)
            
            # Check for missing ledger entries
            await self._check_missing_ledger_entries(report)
            
            # Check escrow mismatches
            await self._check_escrow_mismatches(report, escrow_data)
            
            # Check platform fee mismatches
            await self._check_platform_fee_mismatches(report)
            
            report.status = ReconciliationStatus.COMPLETED
            report.completed_at = datetime.utcnow()
            
        except Exception as e:
            report.status = ReconciliationStatus.FAILED
            report.completed_at = datetime.utcnow()
            report.metadata = {"error": str(e)}
        
        return report
    
    async def _check_orphaned_transactions(
        self,
        report: ReconciliationReport,
        payment_simulations: List[SimulationResult] = None
    ) -> None:
        """Check for orphaned transactions (payments without corresponding ledger entries)"""
        if not payment_simulations:
            return
        
        for sim in payment_simulations:
            if sim.success:
                # Check if transaction exists in ledger
                transaction = self.wallet_engine.get_transaction(sim.transaction_id)
                if not transaction:
                    issue = ReconciliationIssue(
                        issue_id=f"ISS_{uuid.uuid4().hex[:16]}",
                        issue_type=IssueType.ORPHANED_TRANSACTION,
                        severity="high",
                        description=f"Payment transaction {sim.transaction_id} has no corresponding ledger entry",
                        entity_id=sim.transaction_id,
                        entity_type="transaction",
                        detected_at=datetime.utcnow(),
                        metadata={"provider": sim.provider, "amount": sim.amount}
                    )
                    self._issues[issue.issue_id] = issue
                    report.issues.append(issue)
                    report.total_issues_found += 1
    
    async def _check_duplicate_payments(
        self,
        report: ReconciliationReport,
        payment_simulations: List[SimulationResult] = None
    ) -> None:
        """Check for duplicate payments"""
        if not payment_simulations:
            return
        
        # Group by reference
        reference_groups: Dict[str, List[SimulationResult]] = {}
        for sim in payment_simulations:
            ref = sim.metadata.get("config", {}).get("reference", "") if sim.metadata else ""
            if ref:
                if ref not in reference_groups:
                    reference_groups[ref] = []
                reference_groups[ref].append(sim)
        
        # Check for duplicates
        for ref, sims in reference_groups.items():
            if len(sims) > 1:
                for sim in sims[1:]:  # All but the first are duplicates
                    issue = ReconciliationIssue(
                        issue_id=f"ISS_{uuid.uuid4().hex[:16]}",
                        issue_type=IssueType.DUPLICATE_PAYMENT,
                        severity="critical",
                        description=f"Duplicate payment detected for reference {ref}",
                        entity_id=sim.transaction_id,
                        entity_type="transaction",
                        detected_at=datetime.utcnow(),
                        metadata={"reference": ref, "provider": sim.provider, "amount": sim.amount}
                    )
                    self._issues[issue.issue_id] = issue
                    report.issues.append(issue)
                    report.total_issues_found += 1
    
    async def _check_balance_mismatches(self, report: ReconciliationReport) -> None:
        """Check for balance mismatches between wallet and ledger"""
        for wallet_id, wallet in self.wallet_engine._wallets.items():
            # Calculate balance from ledger
            ledger_entries = self.wallet_engine.get_ledger_entries(wallet_id, limit=1000)
            calculated_balance = 0.0
            
            for entry in ledger_entries:
                if entry.entry_type.value == "credit":
                    calculated_balance += entry.amount
                else:
                    calculated_balance -= entry.amount
            
            # Compare with wallet balance
            difference = abs(wallet.balance - calculated_balance)
            if difference > self.balance_tolerance:
                issue = ReconciliationIssue(
                    issue_id=f"ISS_{uuid.uuid4().hex[:16]}",
                    issue_type=IssueType.BALANCE_MISMATCH,
                    severity="critical",
                    description=f"Balance mismatch for wallet {wallet_id}: wallet={wallet.balance}, ledger={calculated_balance}",
                    entity_id=wallet_id,
                    entity_type="wallet",
                    detected_at=datetime.utcnow(),
                    metadata={
                        "wallet_balance": wallet.balance,
                        "ledger_balance": calculated_balance,
                        "difference": difference
                    }
                )
                self._issues[issue.issue_id] = issue
                report.issues.append(issue)
                report.total_issues_found += 1
    
    async def _check_webhook_mismatches(
        self,
        report: ReconciliationReport,
        webhook_records: List[WebhookRecord] = None
    ) -> None:
        """Check for webhook delivery mismatches"""
        if not webhook_records:
            return
        
        for webhook in webhook_records:
            # Check if webhook was delivered but transaction status doesn't match
            if webhook.status.value == "delivered":
                transaction_id = webhook.payload.transaction_id
                transaction = self.wallet_engine.get_transaction(transaction_id)
                
                if transaction:
                    # Check if transaction status matches webhook payload
                    webhook_status = webhook.payload.status.value
                    # This is a simplified check - in real system, would be more complex
                    if webhook_status != "success" and transaction.status == "completed":
                        issue = ReconciliationIssue(
                            issue_id=f"ISS_{uuid.uuid4().hex[:16]}",
                            issue_type=IssueType.WEBHOOK_MISMATCH,
                            severity="medium",
                            description=f"Webhook status {webhook_status} doesn't match transaction status {transaction.status}",
                            entity_id=webhook.webhook_id,
                            entity_type="webhook",
                            detected_at=datetime.utcnow(),
                            metadata={
                                "webhook_status": webhook_status,
                                "transaction_status": transaction.status,
                                "transaction_id": transaction_id
                            }
                        )
                        self._issues[issue.issue_id] = issue
                        report.issues.append(issue)
                        report.total_issues_found += 1
    
    async def _check_failed_settlements(self, report: ReconciliationReport) -> None:
        """Check for failed settlements"""
        # Check for transactions that should have been settled but weren't
        for transaction_id, transaction in self.wallet_engine._transactions.items():
            if transaction.transaction_type.value == "escrow_release":
                if transaction.status == "completed":
                    # Check if corresponding transfer exists
                    # This is simplified - real system would have more complex logic
                    pass
    
    async def _check_missing_ledger_entries(self, report: ReconciliationReport) -> None:
        """Check for transactions missing ledger entries"""
        for transaction_id, transaction in self.wallet_engine._transactions.items():
            if not transaction.ledger_entries or len(transaction.ledger_entries) == 0:
                issue = ReconciliationIssue(
                    issue_id=f"ISS_{uuid.uuid4().hex[:16]}",
                    issue_type=IssueType.MISSING_LEDGER_ENTRY,
                    severity="high",
                    description=f"Transaction {transaction_id} has no ledger entries",
                    entity_id=transaction_id,
                    entity_type="transaction",
                    detected_at=datetime.utcnow(),
                    metadata={"transaction_type": transaction.transaction_type.value}
                )
                self._issues[issue.issue_id] = issue
                report.issues.append(issue)
                report.total_issues_found += 1
    
    async def _check_escrow_mismatches(
        self,
        report: ReconciliationReport,
        escrow_data: Dict[str, Any] = None
    ) -> None:
        """Check for escrow balance mismatches"""
        if not escrow_data:
            return
        
        # Check if escrow wallet balance matches held amounts
        # This is simplified - real system would have more complex logic
        pass
    
    async def _check_platform_fee_mismatches(self, report: ReconciliationReport) -> None:
        """Check for platform fee calculation mismatches"""
        # Check if platform fees are correctly calculated
        # This is simplified - real system would have more complex logic
        pass
    
    def get_report(self, report_id: str) -> Optional[ReconciliationReport]:
        """Get reconciliation report by ID"""
        return self._reports.get(report_id)
    
    def get_latest_report(self) -> Optional[ReconciliationReport]:
        """Get the latest reconciliation report"""
        if not self._reports:
            return None
        return sorted(self._reports.values(), key=lambda r: r.report_date, reverse=True)[0]
    
    def get_issue(self, issue_id: str) -> Optional[ReconciliationIssue]:
        """Get reconciliation issue by ID"""
        return self._issues.get(issue_id)
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[ReconciliationIssue]:
        """Get issues by type"""
        return [i for i in self._issues.values() if i.issue_type == issue_type]
    
    def get_issues_by_severity(self, severity: str) -> List[ReconciliationIssue]:
        """Get issues by severity"""
        return [i for i in self._issues.values() if i.severity == severity]
    
    def get_unresolved_issues(self) -> List[ReconciliationIssue]:
        """Get all unresolved issues"""
        return [i for i in self._issues.values() if i.resolved_at is None]
    
    async def resolve_issue(
        self,
        issue_id: str,
        resolution: str
    ) -> ReconciliationIssue:
        """Resolve a reconciliation issue"""
        issue = self._issues.get(issue_id)
        if not issue:
            raise ValueError(f"Issue not found: {issue_id}")
        
        issue.resolved_at = datetime.utcnow()
        issue.resolution = resolution
        
        return issue
    
    def get_reconciliation_stats(self) -> Dict[str, Any]:
        """Get reconciliation statistics"""
        total_reports = len(self._reports)
        total_issues = len(self._issues)
        
        if total_issues == 0:
            return {"total_reports": total_reports, "total_issues": 0, "resolved": 0, "unresolved": 0}
        
        resolved = len([i for i in self._issues.values() if i.resolved_at is not None])
        unresolved = total_issues - resolved
        
        # Issue type breakdown
        issue_types = {}
        for issue in self._issues.values():
            itype = issue.issue_type.value
            issue_types[itype] = issue_types.get(itype, 0) + 1
        
        # Severity breakdown
        severities = {}
        for issue in self._issues.values():
            sev = issue.severity
            severities[sev] = severities.get(sev, 0) + 1
        
        return {
            "total_reports": total_reports,
            "total_issues": total_issues,
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": (resolved / total_issues) * 100,
            "issue_types": issue_types,
            "severities": severities
        }
    
    def clear_all(self) -> None:
        """Clear all data (for testing)"""
        self._reports.clear()
        self._issues.clear()


# Global reconciliation engine instance (will be initialized with wallet engine)
reconciliation_engine = None
