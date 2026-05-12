# AgriTrust v2.0 - Architecture Implementation Guide

## Overview

This document provides a comprehensive guide for implementing the production-grade, enterprise-scale architecture for AgriTrust 2.0. The architecture follows Domain-Driven Design (DDD), Clean Architecture, and CQRS patterns for maximum scalability and maintainability.

## What Has Been Implemented

### 1. Folder Structure (✅ COMPLETE)
- Domain-driven organization with bounded contexts
- Clear separation of concerns across layers
- Each domain (auth, orders, marketplace, payments, etc.) follows identical structure

### 2. Shared Infrastructure Layer (✅ COMPLETE)
- **Base Infrastructure**:
  - Database configuration with connection pooling
  - Event bus (in-memory, can be replaced with Redis/RabbitMQ)
  - Multi-layer cache (local + Redis)
  - Structured logging
  - System clock

- **CQRS Mediator**:
  - Command Bus for mutations
  - Query Bus for reads
  - Handler registration and execution

- **Unit of Work Pattern**:
  - Transaction management
  - Event publishing after commit
  - Automatic rollback on failure

### 3. Auth Domain (✅ COMPLETE)
- **Domain Layer**:
  - User aggregate root with full business logic
  - Domain events (UserCreated, UserAuthenticated, etc.)
  - Value objects (Credentials, Permission)
  - Comprehensive permission system

- **Application Layer**:
  - Register, Login, ChangePassword commands
  - GetUser, VerifyToken queries
  - DTO layer for request/response validation

- **Infrastructure Layer**:
  - SQLAlchemy ORM models and repositories
  - BCrypt password hashing
  - JWT token generation/verification

- **API Layer**:
  - FastAPI routes with proper error handling
  - Dependency injection integration
  - Request/response validation

### 4. Dependency Injection Container (✅ COMPLETE)
- Centralized service management
- Singleton pattern for expensive resources
- Factory pattern for transient services
- Automatic handler registration

### 5. Main Application Factory (✅ COMPLETE)
- FastAPI app creation
- Middleware configuration (CORS, TrustedHost)
- Exception handlers for domain/validation/general errors
- Health checks for Kubernetes

### 6. Configuration Management (✅ COMPLETE)
- Environment-based settings
- Pydantic validation
- Secret management support

### 7. Testing Framework (✅ COMPLETE)
- Domain layer unit tests (no DB)
- Application layer tests (with mocks)
- Repository integration test examples
- Async test support

### 8. Kubernetes Manifests (✅ COMPLETE)
- Deployment with 3+ replicas
- Horizontal Pod Autoscaler (HPA)
- Pod Disruption Budget for HA
- Network policies
- Health probes
- Resource limits

### 9. Terraform Infrastructure (✅ COMPLETE)
- VPC with public/private subnets
- RDS PostgreSQL (multi-AZ for production)
- ElastiCache Redis cluster
- ECS with Fargate
- Application Load Balancer
- Auto-scaling policies
- KMS encryption
- Secrets Manager integration

## What Still Needs Implementation

### 1. Additional Domains

#### Orders Domain
```
apps/orders/
├── domain/
│   ├── models.py          # Order, OrderItem aggregates
│   ├── events.py          # OrderCreated, OrderPaid, etc.
│   └── interfaces.py      # OrderRepository, PaymentService
├── application/
│   ├── use_cases.py       # CreateOrder, CancelOrder commands
│   └── dto.py             # Request/response models
├── infrastructure/
│   ├── persistence.py     # SQLAlchemy repository
│   └── external.py        # Payment gateway adapters
└── api/
    └── routes.py          # FastAPI routes
```

#### Marketplace Domain
- Product listings
- Inventory management
- Search and filtering

#### Payments Domain
- Payment orchestration
- Gateway integrations (EcoCash, OneMoney)
- Escrow management
- Settlement

#### Logistics Domain
- Delivery routing
- Transportation management
- GPS tracking

#### ML Services Domain
- Crop detection (YOLOv8)
- Price prediction
- Fraud detection

#### Notifications Domain
- SMS (AfricasTalking)
- Email
- Push notifications
- WhatsApp

### 2. Frontend Implementation

Convert apps/ to monorepo structure:
```
frontend/
├── packages/
│   ├── shared-ui/       # Component library
│   ├── api-client/      # OpenAPI codegen
│   └── store/           # Zustand state
└── apps/
    ├── admin-dashboard/
    ├── agent-portal/
    └── app-portal/
```

### 3. Observability

#### Logging (TODO)
```python
from apps.shared.infrastructure import StructuredLogger

logger = StructuredLogger(__name__)
logger.info("Order created", extra={
    "order_id": order_id,
    "amount": 1000.00,
})
```

#### Metrics (TODO)
```yaml
# Prometheus scrape config
- job_name: 'agritrust'
  static_configs:
    - targets: ['localhost:8000']
```

#### Tracing (TODO)
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("process_order"):
    # Business logic here
    pass
```

### 4. CI/CD Pipeline

Create GitHub Actions workflows:
- Build Docker image
- Run tests
- Security scanning
- Deploy to staging/production

### 5. Documentation

- API OpenAPI/Swagger spec
- Architecture Decision Records (ADRs)
- Deployment runbooks
- Troubleshooting guides

## Quick Start

### 1. Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup database
export DATABASE_URL="postgresql://user:password@localhost:5432/agritrust"
alembic upgrade head

# Run tests
pytest tests/ -v

# Run development server
python -m uvicorn core.main:app --reload
```

### 2. Docker Setup

```bash
# Build image
docker build -t agritrust/backend:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### 3. Kubernetes Deployment

```bash
# Create namespace and deploy
kubectl apply -f infra/kubernetes/backend-deployment.yaml

# Check deployment
kubectl get deployments -n agritrust
kubectl get pods -n agritrust

# View logs
kubectl logs -f deployment/agritrust-backend -n agritrust

# Scale manually (if needed)
kubectl scale deployment agritrust-backend --replicas=5 -n agritrust
```

### 4. Terraform Deployment

```bash
# Initialize Terraform
cd infra/terraform
terraform init

# Plan deployment
terraform plan -var="environment=prod"

# Apply configuration
terraform apply -var="environment=prod"

# Destroy (if needed)
terraform destroy
```

## Migration Checklist

- [ ] **Week 1-2: Setup**
  - [ ] Create GitHub/GitLab repository
  - [ ] Setup CI/CD pipeline
  - [ ] Configure Sentry for error tracking
  - [ ] Setup development environment documentation

- [ ] **Week 3-4: Core Domains**
  - [ ] Implement Orders domain (full CRUD)
  - [ ] Implement Marketplace domain
  - [ ] Write comprehensive tests
  - [ ] Deploy to staging K8s

- [ ] **Week 5-6: Payment Integration**
  - [ ] Implement Payments domain
  - [ ] Integrate EcoCash/OneMoney
  - [ ] Add payment webhooks
  - [ ] Implement settlement system

- [ ] **Week 7-8: Logistics**
  - [ ] Implement Logistics domain
  - [ ] Add GPS tracking
  - [ ] Implement delivery routing
  - [ ] Create delivery UI

- [ ] **Week 9-10: ML Services**
  - [ ] Setup Triton inference server
  - [ ] Implement crop detection service
  - [ ] Add price prediction
  - [ ] Integrate fraud detection

- [ ] **Week 11-12: Observability**
  - [ ] Setup Prometheus + Grafana
  - [ ] Configure OpenTelemetry tracing
  - [ ] Create operational dashboards
  - [ ] Setup alerting

- [ ] **Week 13-14: Security & Performance**
  - [ ] Security audit
  - [ ] Load testing
  - [ ] Cache optimization
  - [ ] Database query optimization

- [ ] **Week 15-16: Production Readiness**
  - [ ] Disaster recovery setup
  - [ ] Backup testing
  - [ ] Runbook creation
  - [ ] Production launch

## Key Files Reference

| File | Purpose |
|------|---------|
| `apps/shared/domain/models.py` | Base entities, value objects, domain events |
| `apps/shared/infrastructure/base.py` | Database, cache, logging infrastructure |
| `apps/auth/domain/models.py` | User aggregate with business logic |
| `apps/auth/application/use_cases.py` | CQRS commands and handlers |
| `apps/auth/api/routes.py` | FastAPI endpoints |
| `core/container.py` | Dependency injection container |
| `core/main.py` | FastAPI app factory |
| `infra/kubernetes/backend-deployment.yaml` | K8s deployment manifest |
| `infra/terraform/main.tf` | AWS infrastructure as code |

## Performance Targets

- **API Response Time**: < 200ms (p95)
- **Database Query**: < 50ms (p95)
- **Cache Hit Rate**: > 80%
- **Error Rate**: < 0.1%
- **Uptime**: 99.95%

## Scaling Numbers

- **Horizontal**: 3-20 pods (auto-scaling)
- **Database**: 20 connection pool, 40 overflow
- **Cache**: Redis Cluster (6 nodes)
- **Throughput**: 10K req/sec target

## Support & Questions

For architecture discussions:
1. Review ADRs in `docs/architecture/`
2. Check domain README in each `apps/*/`
3. See implementation examples in `tests/`

---

**Version**: 2.0.0  
**Last Updated**: May 4, 2026  
**Status**: Production-Ready Architecture
