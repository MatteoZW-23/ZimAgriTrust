# ============================================
# AGRITRUST - MAKE COMMANDS
# ============================================

.PHONY: help install dev build up down logs clean test deploy backup

help:
	@echo "Available commands:"
	@echo "  make install     - Install all dependencies"
	@echo "  make dev         - Start development environment"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make logs        - View logs"
	@echo "  make clean       - Clean temporary files"
	@echo "  make test        - Run tests"
	@echo "  make deploy      - Deploy to production"
	@echo "  make backup      - Backup database"

install:
	@echo "Installing dependencies..."
	cd backend && pip install -r requirements.txt
	cd Admin_Dashboard_Web_App && npm install
	cd Farmer_Mobile_Application && npm install
	cd IoT_Sensor_Gateway && npm install
	@echo "✅ Installation complete"

dev:
	@echo "Starting development environment..."
	docker-compose -f docker-compose.dev.yml up --build

build:
	@echo "Building Docker images..."
	docker-compose build --no-cache
	@echo "✅ Build complete"

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✅ Services started"

down:
	@echo "Stopping services..."
	docker-compose down
	@echo "✅ Services stopped"

logs:
	docker-compose logs -f

clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "✅ Clean complete"

test:
	@echo "Running tests..."
	cd backend && pytest tests/ -v --cov=app
	cd Admin_Dashboard_Web_App && npm test
	@echo "✅ Tests complete"

deploy:
	@echo "Deploying to production..."
	./Project_Scripts/deploy.sh

backup:
	@echo "Backing up database..."
	./Project_Scripts/backup_db.sh
	@echo "✅ Backup complete"

migrate:
	@echo "Running database migrations..."
	cd backend && alembic upgrade head
	@echo "✅ Migrations complete"

seed:
	@echo "Seeding database..."
	cd backend && python scripts/seed_data.py
	@echo "✅ Seeding complete"

monitor:
	@echo "Starting monitoring dashboard..."
	docker-compose -f docker-compose.monitoring.yml up -d
	@echo "✅ Monitoring available at http://localhost:3000"
