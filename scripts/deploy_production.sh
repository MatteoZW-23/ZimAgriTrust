#!/bin/bash
# Production Deployment Script
# Automated deployment with health checks and rollback capability

set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"

echo "=========================================="
echo "Agritrust Production Deployment"
echo "=========================================="
echo "Starting deployment at $(date)"

# Pre-deployment checks
echo "Step 1: Pre-deployment checks..."

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: Environment file not found: $ENV_FILE"
    echo "Copy .env.production.example to .env.production and configure it"
    exit 1
fi

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Docker compose file not found: $COMPOSE_FILE"
    exit 1
fi

# Create backup directory
mkdir -p $BACKUP_DIR

# Step 2: Database backup
echo "Step 2: Creating database backup..."
./scripts/backup_database.sh
if [ $? -ne 0 ]; then
    echo "ERROR: Database backup failed. Aborting deployment."
    exit 1
fi

# Step 3: Pull latest images
echo "Step 3: Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Step 4: Build images
echo "Step 4: Building images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Step 5: Stop current services
echo "Step 5: Stopping current services..."
docker-compose -f $COMPOSE_FILE down

# Step 6: Start new services
echo "Step 6: Starting new services..."
docker-compose -f $COMPOSE_FILE up -d

# Step 7: Wait for services to be ready
echo "Step 7: Waiting for services to be ready..."
sleep 30

# Step 8: Health checks
echo "Step 8: Running health checks..."

# Check backend health
BACKEND_HEALTH=$(curl -s http://localhost:8080/health || echo "failed")
if [[ $BACKEND_HEALTH == *"healthy"* ]]; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed"
    echo "Initiating rollback..."
    docker-compose -f $COMPOSE_FILE down
    echo "Rollback complete. Please investigate the issue."
    exit 1
fi

# Check database health
DB_HEALTH=$(curl -s http://localhost:8080/health/ready || echo "failed")
if [[ $DB_HEALTH == *"ready"* ]]; then
    echo "✓ Database health check passed"
else
    echo "✗ Database health check failed"
    echo "Initiating rollback..."
    docker-compose -f $COMPOSE_FILE down
    echo "Rollback complete. Please investigate the issue."
    exit 1
fi

# Step 9: Run database migrations
echo "Step 9: Running database migrations..."
docker-compose -f $COMPOSE_FILE exec backend alembic upgrade head

# Step 10: Verify critical endpoints
echo "Step 10: Verifying critical endpoints..."

ENDPOINTS=(
    "http://localhost:8080/health"
    "http://localhost:8080/health/ready"
)

for endpoint in "${ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" $endpoint)
    if [ $STATUS -eq 200 ]; then
        echo "✓ $endpoint is responding"
    else
        echo "✗ $endpoint returned status $STATUS"
        echo "Initiating rollback..."
        docker-compose -f $COMPOSE_FILE down
        echo "Rollback complete. Please investigate the issue."
        exit 1
    fi
done

# Step 11: Display deployment summary
echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="
echo "Timestamp: $(date)"
echo ""
echo "Services running:"
docker-compose -f $COMPOSE_FILE ps
echo ""
echo "Logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "Health checks: curl http://localhost:8080/health"
echo ""
echo "To rollback: docker-compose -f $COMPOSE_FILE down && ./scripts/restore_database.sh <backup_file>"

# Step 12: Send notification (optional)
# Add your notification logic here (email, Slack, etc.)

exit 0
