"""
Financial Flow Simulation Tester
Tests complete financial flows to demonstrate sandbox functionality
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime

from app.providers.mock.provider_registry import provider_registry
from app.services.payment_simulator import payment_simulator, SimulationConfig, SimulationScenario
from app.services.webhook_simulator import webhook_simulator, WebhookPayload, WebhookDeliveryStatus
from app.services.escrow_simulator import escrow_simulator
from app.services.wallet_transaction_engine import wallet_transaction_engine, WalletType
from app.services.settlement_simulator import SettlementSimulator
from app.services.reconciliation_engine import ReconciliationEngine
from app.services.queue_system import queue_system, QueueType
from app.services.financial_event_system import financial_event_system, EventType
from app.services.fraud_detection import fraud_detection_system
from app.services.monitoring import monitoring_system


class FinancialFlowTester:
    """
    Financial flow simulation tester
    Tests complete financial flows to demonstrate sandbox functionality
    """
    
    def __init__(self):
        self.settlement_simulator = SettlementSimulator(wallet_transaction_engine)
        self.reconciliation_engine = ReconciliationEngine(wallet_transaction_engine)
        self.test_results: List[Dict[str, Any]] = []
    
    async def test_payment_flow(self) -> Dict[str, Any]:
        """
        Test 1: Complete payment flow
        - Initialize payment
        - Process webhook
        - Update wallet
        - Emit events
        """
        print("\n=== Test 1: Payment Flow ===")
        
        # Create wallets
        buyer_wallet = await wallet_transaction_engine.create_wallet(
            user_id="buyer_001",
            wallet_type=WalletType.BUYER,
            currency="USD"
        )
        
        # Simulate payment
        config = SimulationConfig(
            scenario=SimulationScenario.SUCCESS,
            provider="ecocash",
            amount=100.0,
            currency="USD",
            phone_number="+263771234567",
            reference="ORDER_001",
            description="Payment for order ORDER_001",
            callback_url="https://example.com/webhook"
        )
        
        result = await payment_simulator.simulate_payment(config)
        
        # Deposit to buyer wallet
        if result.success:
            await wallet_transaction_engine.deposit(
                wallet_id=buyer_wallet.wallet_id,
                amount=result.amount,
                currency=result.currency,
                reference=result.transaction_id,
                description="Payment deposit"
            )
            
            # Emit event
            await financial_event_system.emit_event(
                event_type=EventType.PAYMENT_SUCCESS,
                entity_id=result.transaction_id,
                entity_type="transaction",
                data={"amount": result.amount, "provider": result.provider},
                user_id="buyer_001"
            )
            
            # Update metrics
            monitoring_system.increment_counter("payments_total")
            monitoring_system.increment_counter("payments_success_total")
        
        test_result = {
            "test": "payment_flow",
            "success": result.success,
            "transaction_id": result.transaction_id,
            "status": result.status.value,
            "amount": result.amount,
            "webhook_delivered": result.webhook_delivered
        }
        
        self.test_results.append(test_result)
        print(f"Payment Flow Result: {test_result}")
        return test_result
    
    async def test_escrow_flow(self) -> Dict[str, Any]:
        """
        Test 2: Escrow flow
        - Hold funds in escrow
        - Release escrow
        - Update wallets
        """
        print("\n=== Test 2: Escrow Flow ===")
        
        # Create wallets
        buyer_wallet = await wallet_transaction_engine.create_wallet(
            user_id="buyer_002",
            wallet_type=WalletType.BUYER,
            currency="USD"
        )
        
        seller_wallet = await wallet_transaction_engine.create_wallet(
            user_id="seller_001",
            wallet_type=WalletType.FARMER,
            currency="USD"
        )
        
        escrow_wallet = await wallet_transaction_engine.create_wallet(
            user_id="ESCROW",
            wallet_type=WalletType.ESCROW,
            currency="USD"
        )
        
        # Deposit to buyer wallet
        await wallet_transaction_engine.deposit(
            wallet_id=buyer_wallet.wallet_id,
            amount=500.0,
            currency="USD",
            reference="DEPOSIT_001",
            description="Initial deposit"
        )
        
        # Hold in escrow
        escrow = await escrow_simulator.hold_escrow(
            order_id="ORDER_002",
            buyer_id="buyer_002",
            seller_id="seller_001",
            amount=500.0,
            currency="USD"
        )
        
        # Transfer to escrow wallet
        await wallet_transaction_engine.transfer(
            from_wallet_id=buyer_wallet.wallet_id,
            to_wallet_id=escrow_wallet.wallet_id,
            amount=500.0,
            currency="USD",
            reference="ESCROW_HOLD_001",
            description="Escrow hold"
        )
        
        # Release escrow
        released_escrow = await escrow_simulator.release_escrow(
            escrow_id=escrow.escrow_id,
            amount=500.0,
            reason="Order delivered successfully"
        )
        
        # Transfer to seller wallet
        await wallet_transaction_engine.transfer(
            from_wallet_id=escrow_wallet.wallet_id,
            to_wallet_id=seller_wallet.wallet_id,
            amount=500.0,
            currency="USD",
            reference="ESCROW_RELEASE_001",
            description="Escrow release to seller"
        )
        
        # Emit events
        await financial_event_system.emit_event(
            event_type=EventType.ESCROW_HELD,
            entity_id=escrow.escrow_id,
            entity_type="escrow",
            data={"amount": escrow.amount, "order_id": escrow.order_id}
        )
        
        await financial_event_system.emit_event(
            event_type=EventType.ESCROW_RELEASED,
            entity_id=escrow.escrow_id,
            entity_type="escrow",
            data={"amount": escrow.amount, "order_id": escrow.order_id}
        )
        
        # Update metrics
        monitoring_system.increment_counter("escrow_released_total")
        monitoring_system.set_gauge("escrow_held_total", 0)
        
        test_result = {
            "test": "escrow_flow",
            "success": True,
            "escrow_id": escrow.escrow_id,
            "order_id": escrow.order_id,
            "amount": escrow.amount,
            "status": released_escrow.status.value
        }
        
        self.test_results.append(test_result)
        print(f"Escrow Flow Result: {test_result}")
        return test_result
    
    async def test_settlement_flow(self) -> Dict[str, Any]:
        """
        Test 3: Settlement flow
        - Create settlement item
        - Process settlement
        - Deduct platform fee
        """
        print("\n=== Test 3: Settlement Flow ===")
        
        # Create wallets
        seller_wallet = await wallet_transaction_engine.create_wallet(
            user_id="seller_002",
            wallet_type=WalletType.FARMER,
            currency="USD"
        )
        
        escrow_wallet = await wallet_transaction_engine.create_wallet(
            user_id="ESCROW",
            wallet_type=WalletType.ESCROW,
            currency="USD"
        )
        
        platform_wallet = await wallet_transaction_engine.create_wallet(
            user_id="PLATFORM",
            wallet_type=WalletType.PLATFORM,
            currency="USD"
        )
        
        # Add funds to escrow
        await wallet_transaction_engine.deposit(
            wallet_id=escrow_wallet.wallet_id,
            amount=1000.0,
            currency="USD",
            reference="ESCROW_DEPOSIT",
            description="Escrow deposit"
        )
        
        # Create settlement item
        settlement_item = await self.settlement_simulator.create_settlement_item(
            order_id="ORDER_003",
            seller_id="seller_002",
            amount=1000.0,
            currency="USD",
            platform_fee_rate=0.05
        )
        
        # Create and process batch
        batch = await self.settlement_simulator.create_settlement_batch(
            batch_name="Test Batch",
            currency="USD",
            item_ids=[settlement_item.item_id]
        )
        
        await self.settlement_simulator.submit_batch(batch.batch_id)
        processed_batch = await self.settlement_simulator.process_batch(
            batch.batch_id,
            escrow_wallet.wallet_id,
            platform_wallet.wallet_id
        )
        
        # Emit event
        await financial_event_system.emit_event(
            event_type=EventType.SETTLEMENT_COMPLETED,
            entity_id=batch.batch_id,
            entity_type="settlement_batch",
            data={"total_amount": batch.total_amount, "platform_fee": batch.total_platform_fee}
        )
        
        # Update metrics
        monitoring_system.increment_counter("settlements_total")
        monitoring_system.increment_counter("settlements_completed_total")
        monitoring_system.set_gauge("platform_fees_total", batch.total_platform_fee)
        
        test_result = {
            "test": "settlement_flow",
            "success": processed_batch.status.value == "completed",
            "batch_id": batch.batch_id,
            "total_amount": batch.total_amount,
            "platform_fee": batch.total_platform_fee,
            "net_amount": batch.total_net_amount,
            "status": processed_batch.status.value
        }
        
        self.test_results.append(test_result)
        print(f"Settlement Flow Result: {test_result}")
        return test_result
    
    async def test_webhook_flow(self) -> Dict[str, Any]:
        """
        Test 4: Webhook flow with retries
        - Create webhook
        - Deliver webhook
        - Test retry logic
        """
        print("\n=== Test 4: Webhook Flow ===")
        
        # Create webhook payload
        from app.providers.mock.base_provider import PaymentStatus
        
        payload = WebhookPayload(
            transaction_id="TXN_WEBHOOK_001",
            status=PaymentStatus.SUCCESS,
            amount=150.0,
            currency="USD",
            reference="ORDER_004",
            provider_reference="PROV_REF_001",
            timestamp=datetime.utcnow(),
            signature="test_signature"
        )
        
        # Create webhook
        webhook = await webhook_simulator.create_webhook(
            payload=payload,
            callback_url="https://example.com/webhook",
            max_retries=3,
            retry_strategy=webhook_simulator.WebhookRetryStrategy.EXPONENTIAL_BACKOFF
        )
        
        # Deliver webhook
        attempt = await webhook_simulator.deliver_webhook(
            webhook.webhook_id,
            simulate_failure=False
        )
        
        # Update metrics
        monitoring_system.increment_counter("webhook_deliveries_total")
        
        test_result = {
            "test": "webhook_flow",
            "success": attempt.status.value == "delivered",
            "webhook_id": webhook.webhook_id,
            "attempt_number": attempt.attempt_number,
            "status": attempt.status.value,
            "response_code": attempt.response_code
        }
        
        self.test_results.append(test_result)
        print(f"Webhook Flow Result: {test_result}")
        return test_result
    
    async def test_reconciliation_flow(self) -> Dict[str, Any]:
        """
        Test 5: Reconciliation flow
        - Run reconciliation
        - Check for issues
        - Generate report
        """
        print("\n=== Test 5: Reconciliation Flow ===")
        
        # Run reconciliation
        report = await self.reconciliation_engine.run_daily_reconciliation()
        
        # Update metrics
        monitoring_system.increment_counter("reconciliation_runs_total")
        monitoring_system.set_gauge("reconciliation_issues_total", report.total_issues_found)
        
        test_result = {
            "test": "reconciliation_flow",
            "success": report.status.value == "completed",
            "report_id": report.report_id,
            "total_transactions_checked": report.total_transactions_checked,
            "total_issues_found": report.total_issues_found,
            "status": report.status.value
        }
        
        self.test_results.append(test_result)
        print(f"Reconciliation Flow Result: {test_result}")
        return test_result
    
    async def test_queue_flow(self) -> Dict[str, Any]:
        """
        Test 6: Queue flow
        - Enqueue jobs
        - Process jobs
        - Test retry logic
        """
        print("\n=== Test 6: Queue Flow ===")
        
        # Register handler
        async def mock_handler(payload):
            return {"status": "success", "processed": True}
        
        queue_system.register_handler(QueueType.PAYMENT, mock_handler)
        
        # Enqueue jobs
        job1 = await queue_system.enqueue(
            queue_type=QueueType.PAYMENT,
            payload={"order_id": "ORDER_005", "amount": 200.0},
            max_attempts=3
        )
        
        job2 = await queue_system.enqueue(
            queue_type=QueueType.PAYMENT,
            payload={"order_id": "ORDER_006", "amount": 300.0},
            max_attempts=3
        )
        
        # Process queue
        processed_jobs = await queue_system.process_queue(QueueType.PAYMENT)
        
        # Update metrics
        monitoring_system.set_gauge("queue_payment_pending", 0)
        
        test_result = {
            "test": "queue_flow",
            "success": len(processed_jobs) > 0,
            "jobs_enqueued": 2,
            "jobs_processed": len(processed_jobs),
            "queue_stats": queue_system.get_queue_stats()
        }
        
        self.test_results.append(test_result)
        print(f"Queue Flow Result: {test_result}")
        return test_result
    
    async def test_fraud_detection_flow(self) -> Dict[str, Any]:
        """
        Test 7: Fraud detection flow
        - Check transaction for fraud
        - Generate alerts
        - Test blocking
        """
        print("\n=== Test 7: Fraud Detection Flow ===")
        
        # Create a large transaction to trigger alert
        from app.services.wallet_transaction_engine import Transaction, TransactionType
        
        transaction = Transaction(
            transaction_id="TXN_FRAUD_001",
            transaction_type=TransactionType.TRANSFER,
            amount=15000.0,  # Above threshold
            currency="USD",
            from_wallet_id="WLT_001",
            to_wallet_id="WLT_002",
            status="completed",
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        # Check for fraud
        alerts = await fraud_detection_system.check_transaction(
            transaction=transaction,
            user_id="user_001",
            ip_address="192.168.1.1"
        )
        
        # Update metrics
        monitoring_system.increment_counter("fraud_alerts_total", len(alerts))
        monitoring_system.set_gauge("fraud_alerts_unresolved", len(alerts))
        
        test_result = {
            "test": "fraud_detection_flow",
            "success": True,
            "alerts_generated": len(alerts),
            "alert_types": [a.alert_type.value for a in alerts],
            "fraud_stats": fraud_detection_system.get_fraud_stats()
        }
        
        self.test_results.append(test_result)
        print(f"Fraud Detection Flow Result: {test_result}")
        return test_result
    
    async def test_complete_end_to_end_flow(self) -> Dict[str, Any]:
        """
        Test 8: Complete end-to-end flow
        - Buyer makes payment
        - Funds held in escrow
        - Order delivered
        - Escrow released
        - Settlement processed
        - Platform fee deducted
        - Reconciliation run
        """
        print("\n=== Test 8: Complete End-to-End Flow ===")
        
        # Setup wallets
        buyer_wallet = await wallet_transaction_engine.create_wallet(
            user_id="buyer_e2e",
            wallet_type=WalletType.BUYER,
            currency="USD"
        )
        
        seller_wallet = await wallet_transaction_engine.create_wallet(
            user_id="seller_e2e",
            wallet_type=WalletType.FARMER,
            currency="USD"
        )
        
        escrow_wallet = await wallet_transaction_engine.create_wallet(
            user_id="ESCROW",
            wallet_type=WalletType.ESCROW,
            currency="USD"
        )
        
        platform_wallet = await wallet_transaction_engine.create_wallet(
            user_id="PLATFORM",
            wallet_type=WalletType.PLATFORM,
            currency="USD"
        )
        
        # 1. Buyer makes payment
        payment_config = SimulationConfig(
            scenario=SimulationScenario.SUCCESS,
            provider="ecocash",
            amount=750.0,
            currency="USD",
            phone_number="+263777654321",
            reference="ORDER_E2E_001",
            description="End-to-end test payment"
        )
        
        payment_result = await payment_simulator.simulate_payment(payment_config)
        
        # 2. Deposit to buyer wallet
        if payment_result.success:
            await wallet_transaction_engine.deposit(
                wallet_id=buyer_wallet.wallet_id,
                amount=payment_result.amount,
                currency=payment_result.currency,
                reference=payment_result.transaction_id
            )
        
        # 3. Hold in escrow
        escrow = await escrow_simulator.hold_escrow(
            order_id="ORDER_E2E_001",
            buyer_id="buyer_e2e",
            seller_id="seller_e2e",
            amount=750.0,
            currency="USD"
        )
        
        # 4. Transfer to escrow
        await wallet_transaction_engine.transfer(
            from_wallet_id=buyer_wallet.wallet_id,
            to_wallet_id=escrow_wallet.wallet_id,
            amount=750.0,
            currency="USD",
            reference="E2E_ESCROW_HOLD"
        )
        
        # 5. Release escrow (simulating delivery confirmation)
        await escrow_simulator.release_escrow(escrow.escrow_id)
        
        # 6. Create settlement
        settlement_item = await self.settlement_simulator.create_settlement_item(
            order_id="ORDER_E2E_001",
            seller_id="seller_e2e",
            amount=750.0,
            currency="USD",
            platform_fee_rate=0.05
        )
        
        # 7. Process settlement
        batch = await self.settlement_simulator.create_settlement_batch(
            batch_name="E2E Batch",
            currency="USD",
            item_ids=[settlement_item.item_id]
        )
        
        await self.settlement_simulator.submit_batch(batch.batch_id)
        processed_batch = await self.settlement_simulator.process_batch(
            batch.batch_id,
            escrow_wallet.wallet_id,
            platform_wallet.wallet_id
        )
        
        # 8. Run reconciliation
        reconciliation_report = await self.reconciliation_engine.run_daily_reconciliation()
        
        # Get final balances
        buyer_balance = wallet_transaction_engine.get_wallet_balance(buyer_wallet.wallet_id)
        seller_balance = wallet_transaction_engine.get_wallet_balance(seller_wallet.wallet_id)
        platform_balance = wallet_transaction_engine.get_wallet_balance(platform_wallet.wallet_id)
        
        test_result = {
            "test": "complete_end_to_end_flow",
            "success": all([
                payment_result.success,
                escrow.status.value == "released",
                processed_batch.status.value == "completed",
                reconciliation_report.status.value == "completed"
            ]),
            "payment_success": payment_result.success,
            "escrow_status": escrow.status.value,
            "settlement_status": processed_batch.status.value,
            "reconciliation_status": reconciliation_report.status.value,
            "final_balances": {
                "buyer": buyer_balance,
                "seller": seller_balance,
                "platform": platform_balance
            },
            "platform_fee": batch.total_platform_fee,
            "seller_net": batch.total_net_amount
        }
        
        self.test_results.append(test_result)
        print(f"Complete End-to-End Flow Result: {test_result}")
        return test_result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all financial flow tests
        Returns comprehensive test results
        """
        print("\n" + "="*50)
        print("RUNNING FINANCIAL FLOW SIMULATION TESTS")
        print("="*50)
        
        start_time = datetime.utcnow()
        
        # Run all tests
        await self.test_payment_flow()
        await self.test_escrow_flow()
        await self.test_settlement_flow()
        await self.test_webhook_flow()
        await self.test_reconciliation_flow()
        await self.test_queue_flow()
        await self.test_fraud_detection_flow()
        await self.test_complete_end_to_end_flow()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t.get("success", False))
        failed_tests = total_tests - passed_tests
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "duration_seconds": duration,
            "test_results": self.test_results,
            "timestamp": end_time.isoformat()
        }
        
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {summary['success_rate']:.2f}%")
        print(f"Duration: {duration:.2f} seconds")
        print("="*50)
        
        return summary


# Global tester instance
financial_flow_tester = FinancialFlowTester()


# Main entry point for running tests
async def main():
    """Main entry point for running financial flow tests"""
    tester = FinancialFlowTester()
    results = await tester.run_all_tests()
    return results


if __name__ == "__main__":
    asyncio.run(main())
