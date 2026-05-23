# ZimAgriTrust Mock Fintech Sandbox

A complete mock fintech sandbox environment for the ZimAgriTrust agricultural marketplace platform. This sandbox simulates real payment provider behavior without requiring access to live payment systems, enabling comprehensive testing and development of financial flows.

## Overview

The mock fintech sandbox provides a production-grade simulation environment that includes:

- **Mock Payment Providers**: EcoCash, OneMoney, Innbucks, ZIPIT, Bank, and Visa with realistic behavior
- **Payment Simulation Engine**: State transitions, delays, failures, timeouts, and retry scenarios
- **Webhook Engine**: Delivery with retry handlers, signature validation, and replay protection
- **Escrow System**: Fund holding, disputes, partial releases, and automatic settlement
- **Wallet & Ledger**: Immutable ledger with double-entry accounting and audit-safe history
- **Settlement Engine**: Platform fee deduction and batch settlement processing
- **Reconciliation Engine**: Daily jobs, orphaned transaction detection, and balance verification
- **Queue System**: BullMQ/Celery-style queues with exponential backoff and dead-letter queues
- **Financial Events**: Transaction event streaming and audit logging
- **Fraud Detection**: Suspicious transaction detection and safety systems
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Admin Dashboards**: Comprehensive financial monitoring endpoints

## Architecture

The sandbox is designed to allow real providers to replace mock providers without changing core business logic. Only provider adapters need to change; all wallets, escrow, settlements, queues, reconciliation, and ledger systems remain unchanged.

### Directory Structure

```
backend/app/
├── providers/mock/
│   ├── __init__.py
│   ├── base_provider.py
│   ├── ecocash_provider.py
│   ├── onemoney_provider.py
│   ├── innbucks_provider.py
│   ├── zipit_provider.py
│   ├── bank_provider.py
│   ├── visa_provider.py
│   └── provider_registry.py
├── services/
│   ├── payment_simulator.py
│   ├── webhook_simulator.py
│   ├── escrow_simulator.py
│   ├── wallet_transaction_engine.py
│   ├── settlement_simulator.py
│   ├── reconciliation_engine.py
│   ├── queue_system.py
│   ├── financial_event_system.py
│   ├── fraud_detection.py
│   ├── monitoring.py
│   └── financial_flow_tester.py
└── api/v1/endpoints/
    └── financial_dashboard.py

infra/monitoring/
├── prometheus/
│   └── prometheus-sandbox.yml
└── grafana/
    ├── provisioning/
    │   └── dashboards/
    │       └── sandbox.yml
    └── dashboards/
        └── fintech-sandbox-dashboard.json

docker-compose.fintech-sandbox.yml
```

## Quick Start

### 1. Start the Sandbox Environment

```bash
# Start all sandbox services
docker-compose -f docker-compose.fintech-sandbox.yml up -d

# View logs
docker-compose -f docker-compose.fintech-sandbox.yml logs -f
```

Services included:
- **postgres-sandbox**: PostgreSQL database (port 5433)
- **redis-sandbox**: Redis for caching and queues (port 6380)
- **backend-sandbox**: FastAPI backend with sandbox features (port 8001)
- **prometheus-sandbox**: Metrics collection (port 9091)
- **grafana-sandbox**: Dashboards (port 3001)
- **queue-worker-sandbox**: Background job processing
- **reconciliation-worker-sandbox**: Daily reconciliation jobs

### 2. Access Dashboards

- **Grafana**: http://localhost:3001 (admin/sandbox_grafana)
- **Prometheus**: http://localhost:9091
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### 3. Run Financial Flow Tests

```bash
# From the backend directory
cd backend
python -m app.services.financial_flow_tester
```

This will run 8 comprehensive tests:
1. Payment Flow
2. Escrow Flow
3. Settlement Flow
4. Webhook Flow
5. Reconciliation Flow
6. Queue Flow
7. Fraud Detection Flow
8. Complete End-to-End Flow

## Mock Payment Providers

### Available Providers

- **EcoCash**: Mobile money provider (95% success rate, 1-5s delay)
- **OneMoney**: Mobile money provider (93% success rate, 2-6s delay)
- **Innbucks**: Mobile wallet provider (94% success rate, 1-4s delay)
- **ZIPIT**: Bank transfer provider (96% success rate, 3-8s delay)
- **Bank**: Bank transfer provider (97% success rate, 5-15s delay)
- **Visa**: Card payment provider (98% success rate, 2-5s delay)

### Provider Configuration

Each provider can be configured with:
- `success_rate`: Probability of successful payment (0.0-1.0)
- `delay_range`: Tuple of (min_delay, max_delay) in seconds
- `timeout_rate`: Probability of timeout (0.0-1.0)
- `failure_rate`: Probability of failure (0.0-1.0)

Example:
```python
from app.providers.mock.provider_registry import provider_registry

# Get provider
ecocash = provider_registry.get_provider("ecocash")

# Configure provider
ecocash_config = {
    "success_rate": 0.95,
    "delay_range": (1, 5),
    "timeout_rate": 0.02,
    "failure_rate": 0.03
}
```

## Payment Simulation

### Simulation Scenarios

The payment simulator supports various scenarios:

- **SUCCESS**: Normal successful payment
- **FAILURE**: Payment fails immediately
- **TIMEOUT**: Payment times out after delay
- **DELAYED**: Payment with extended delay
- **DUPLICATE_WEBHOOK**: Simulates duplicate webhook delivery
- **NETWORK_FAILURE**: Simulates network timeout
- **PROVIDER_DOWNTIME**: Simulates provider unavailability
- **RETRY_SUCCESS**: Payment succeeds after retries
- **PARTIAL_REFUND**: Partial refund scenario
- **FULL_REFUND**: Full refund scenario

### Example Usage

```python
from app.services.payment_simulator import payment_simulator, SimulationConfig, SimulationScenario

config = SimulationConfig(
    scenario=SimulationScenario.SUCCESS,
    provider="ecocash",
    amount=100.0,
    currency="USD",
    phone_number="+263771234567",
    reference="ORDER_001",
    description="Payment for order"
)

result = await payment_simulator.simulate_payment(config)
print(f"Transaction ID: {result.transaction_id}")
print(f"Status: {result.status.value}")
print(f"Success: {result.success}")
```

## Escrow System

### Escrow Flow

1. Buyer initiates payment
2. Funds held in escrow wallet
3. Order marked as ESCROW_HELD
4. Delivery confirmed
5. Settlement triggered
6. Platform fee deducted
7. Supplier/farmer wallet credited

### Example Usage

```python
from app.services.escrow_simulator import escrow_simulator

# Hold funds in escrow
escrow = await escrow_simulator.hold_escrow(
    order_id="ORDER_001",
    buyer_id="buyer_001",
    seller_id="seller_001",
    amount=500.0,
    currency="USD"
)

# Release escrow
await escrow_simulator.release_escrow(escrow.escrow_id)

# Raise dispute
dispute = await escrow_simulator.raise_dispute(
    escrow_id=escrow.escrow_id,
    order_id="ORDER_001",
    raised_by="buyer_001",
    reason="Product not as described",
    description="Quality issues"
)
```

## Wallet & Ledger System

### Double-Entry Accounting

The wallet transaction engine implements immutable double-entry accounting:

- Every transaction creates debit and credit entries
- Ledger entries are cryptographically hashed for integrity
- Balances are calculated from ledger entries (never stored directly)
- Distributed locks prevent race conditions

### Example Usage

```python
from app.services.wallet_transaction_engine import wallet_transaction_engine, WalletType

# Create wallet
wallet = await wallet_transaction_engine.create_wallet(
    user_id="user_001",
    wallet_type=WalletType.BUYER,
    currency="USD"
)

# Deposit funds
transaction = await wallet_transaction_engine.deposit(
    wallet_id=wallet.wallet_id,
    amount=1000.0,
    currency="USD",
    reference="DEPOSIT_001"
)

# Transfer with platform fee
transaction = await wallet_transaction_engine.transfer(
    from_wallet_id=wallet.wallet_id,
    to_wallet_id=recipient_wallet_id,
    amount=500.0,
    currency="USD",
    deduct_platform_fee=True
)

# Verify ledger integrity
integrity = wallet_transaction_engine.verify_ledger_integrity()
print(f"Ledger balanced: {integrity['is_balanced']}")
```

## Settlement System

### Settlement Flow

1. Create settlement item with platform fee calculation
2. Create settlement batch
3. Submit batch for processing
4. Process batch (transfer to seller, deduct fee)
5. Platform fee credited to platform wallet

### Example Usage

```python
from app.services.settlement_simulator import SettlementSimulator

settlement_sim = SettlementSimulator(wallet_transaction_engine)

# Create settlement item
item = await settlement_sim.create_settlement_item(
    order_id="ORDER_001",
    seller_id="seller_001",
    amount=1000.0,
    currency="USD",
    platform_fee_rate=0.05  # 5%
)

# Create and process batch
batch = await settlement_sim.create_settlement_batch(
    batch_name="Daily Settlement",
    currency="USD",
    item_ids=[item.item_id]
)

await settlement_sim.submit_batch(batch.batch_id)
await settlement_sim.process_batch(batch.batch_id, escrow_wallet_id, platform_wallet_id)
```

## Reconciliation Engine

### Reconciliation Checks

The reconciliation engine performs daily checks for:
- Orphaned transactions (payments without ledger entries)
- Duplicate payments
- Balance mismatches between wallet and ledger
- Webhook delivery mismatches
- Failed settlements
- Missing ledger entries
- Escrow balance mismatches
- Platform fee calculation errors

### Example Usage

```python
from app.services.reconciliation_engine import ReconciliationEngine

reconciliation = ReconciliationEngine(wallet_transaction_engine)

# Run daily reconciliation
report = await reconciliation.run_daily_reconciliation()

print(f"Issues found: {report.total_issues_found}")
print(f"Status: {report.status.value}")

# Get unresolved issues
unresolved = reconciliation.get_unresolved_issues()
```

## Queue System

### Queue Types

- **PAYMENT**: Payment processing jobs
- **WEBHOOK**: Webhook delivery jobs
- **SETTLEMENT**: Settlement processing jobs
- **RECONCILIATION**: Reconciliation jobs
- **NOTIFICATION**: Notification jobs
- **WITHDRAWAL**: Withdrawal processing jobs

### Example Usage

```python
from app.services.queue_system import queue_system, QueueType

# Register handler
async def payment_handler(payload):
    # Process payment
    return {"status": "success"}

queue_system.register_handler(QueueType.PAYMENT, payment_handler)

# Enqueue job
job = await queue_system.enqueue(
    queue_type=QueueType.PAYMENT,
    payload={"order_id": "ORDER_001", "amount": 100.0},
    max_attempts=3,
    retry_strategy=queue_system.RetryStrategy.EXPONENTIAL_BACKOFF
)

# Process queue
processed = await queue_system.process_queue(QueueType.PAYMENT)
```

## Fraud Detection

### Detection Rules

The fraud detection system monitors for:
- Suspicious transactions
- Duplicate withdrawals
- Rapid payment spikes
- Webhook abuse
- Retry storms
- Unusual IP patterns
- Large transactions
- Frequent failed attempts
- Balance anomalies
- Escrow anomalies

### Example Usage

```python
from app.services.fraud_detection import fraud_detection_system

# Check transaction
alerts = await fraud_detection_system.check_transaction(
    transaction=transaction,
    user_id="user_001",
    ip_address="192.168.1.1"
)

# Calculate risk score
risk_score = await fraud_detection_system.calculate_risk_score(
    entity_id="user_001",
    entity_type="user",
    factors={
        "transaction_frequency": 0.3,
        "amount_variance": 0.2,
        "failed_attempts": 0.1
    }
)

# Block entity if needed
await fraud_detection_system.block_entity("user_001", "Suspicious activity")
```

## Admin Dashboard API

### Available Endpoints

- `GET /api/v1/dashboard/payment` - Payment monitoring dashboard
- `GET /api/v1/dashboard/settlement` - Settlement dashboard
- `GET /api/v1/dashboard/reconciliation` - Reconciliation dashboard
- `GET /api/v1/dashboard/escrow` - Escrow dashboard
- `GET /api/v1/dashboard/fraud` - Fraud monitoring dashboard
- `GET /api/v1/dashboard/queue` - Queue monitoring dashboard
- `GET /api/v1/dashboard/ledger` - Ledger integrity dashboard
- `GET /api/v1/dashboard/webhook` - Webhook monitoring dashboard
- `GET /api/v1/dashboard/events` - Financial events dashboard
- `GET /api/v1/dashboard/overview` - Comprehensive overview

### Example

```bash
# Get payment dashboard
curl http://localhost:8001/api/v1/dashboard/payment?hours=24

# Get overview dashboard
curl http://localhost:8001/api/v1/dashboard/overview
```

## Monitoring

### Prometheus Metrics

The system exports Prometheus metrics for:
- Payment throughput and success rates
- Settlement processing
- Queue backlogs
- Escrow balances
- Fraud alerts
- Ledger integrity
- API request duration

### Grafana Dashboards

Pre-configured dashboards include:
- Payment success rate gauge
- Payment throughput graph
- Revenue & escrow metrics
- Queue backlog monitoring
- Fraud alert statistics
- Ledger entry counts
- Total wallet balance
- Blocked entities count

Access Grafana at http://localhost:3001

## Environment Variables

Configure the sandbox with these environment variables:

```bash
# Database
POSTGRES_PASSWORD=sandbox_dev_password

# Security
SECRET_KEY=sandbox_secret_key_change_in_production
REFRESH_SECRET_KEY=sandbox_refresh_secret_change_in_production
ADMIN_BOOTSTRAP_TOKEN=sandbox_admin_token

# Monitoring
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=sandbox_grafana

# Sandbox Features
MOCK_PAYMENT_PROVIDERS=true
ENABLE_FINTECH_SANDBOX=true
```

## Testing

### Run All Tests

```bash
cd backend
python -m app.services.financial_flow_tester
```

### Individual Test Examples

```python
from app.services.financial_flow_tester import FinancialFlowTester

tester = FinancialFlowTester()

# Run specific test
await tester.test_payment_flow()
await tester.test_escrow_flow()
await tester.test_settlement_flow()
await tester.test_complete_end_to_end_flow()
```

## Production Integration

To replace mock providers with real providers:

1. Implement the `BasePaymentProvider` interface for each real provider
2. Update the `ProviderRegistry` to use real providers
3. Configure real provider credentials in environment variables
4. No changes needed to:
   - Wallet system
   - Escrow system
   - Settlement engine
   - Reconciliation engine
   - Queue system
   - Event system
   - Fraud detection
   - Monitoring

## Security Considerations

The sandbox includes:
- Webhook signature verification (HMAC-SHA256)
- Idempotency keys for duplicate prevention
- Transaction validation
- RBAC financial permissions
- Secure retries with exponential backoff
- Audit-safe event logging
- Distributed locks for race condition prevention
- Anti-race-condition protection

## Scalability

The sandbox architecture supports:
- 10,000+ concurrent users
- Payment spikes
- Retry storms
- Webhook floods
- High queue volume
- High settlement volume

## Troubleshooting

### Common Issues

**Sandbox not starting:**
```bash
# Check logs
docker-compose -f docker-compose.fintech-sandbox.yml logs backend-sandbox

# Restart services
docker-compose -f docker-compose.fintech-sandbox.yml restart
```

**Database connection errors:**
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.fintech-sandbox.yml ps postgres-sandbox

# Restart PostgreSQL
docker-compose -f docker-compose.fintech-sandbox.yml restart postgres-sandbox
```

**Queue processing issues:**
```bash
# Check queue worker logs
docker-compose -f docker-compose.fintech-sandbox.yml logs queue-worker-sandbox

# Restart queue worker
docker-compose -f docker-compose.fintech-sandbox.yml restart queue-worker-sandbox
```

## Support

For issues or questions:
1. Check the logs: `docker-compose -f docker-compose.fintech-sandbox.yml logs`
2. Run the financial flow tests to verify system health
3. Check dashboard endpoints for system status
4. Review Prometheus metrics for performance issues

## License

This mock fintech sandbox is part of the ZimAgriTrust platform.
