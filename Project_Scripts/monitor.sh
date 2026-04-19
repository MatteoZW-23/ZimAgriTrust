#!/bin/bash
# Health check for Agric platform services

echo "Checking Docker Compose services..."
docker-compose ps

echo "Checking Backend Health..."
curl -s http://localhost:8080/ | grep "ok" || echo "Backend heavily degraded or down."

echo "Monitoring metrics summary:"
docker stats --no-stream
