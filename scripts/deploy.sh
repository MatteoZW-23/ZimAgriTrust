#!/bin/bash

# ============================================
# AGRITRUST DEPLOYMENT SCRIPT
# ============================================

set -e

echo "🚀 Starting Agritrust deployment..."

# Load environment variables
source .env.production

# Pull latest images
echo "📦 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# Run database migrations
echo "🗄️ Running migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# Seed database (first time only)
# docker-compose -f docker-compose.prod.yml run --rm backend python scripts/seed_data.py

# Start services
echo "▶️ Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Health check
echo "🏥 Running health checks..."
sleep 10
curl -f http://localhost:8000/health || exit 1

# Clean up old images
echo "🧹 Cleaning up..."
docker image prune -f

echo "✅ Deployment complete!"
echo "📊 API: http://localhost:8000"
echo "📈 Dashboard: http://localhost:3000"
echo "📱 USSD Simulator: http://localhost:5000"
