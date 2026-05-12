.PHONY: run test test-unit test-integration build clean deploy lint-imports spec-coverage spec-missing spec-categories ci-check retrain seed-training

# ── Application lifecycle ──────────────────────────────────────────────────
run:
	docker-compose up backend

build:
	docker-compose build

deploy:
	sh scripts/deploy.sh

# ── Testing ────────────────────────────────────────────────────────────────
test:
	pytest tests/

test-unit:
	docker compose exec backend pytest tests/unit -v

test-integration:
	docker compose exec backend pytest tests/integration -v

# ── Architecture & spec enforcement ────────────────────────────────────────
# Verifies clean-architecture dependency rules (see backend/.importlinter).
lint-imports:
	docker compose exec backend lint-imports --config .importlinter

# F#NNN traceability: scan source for spec markers.
spec-coverage:
	python scripts/spec_coverage.py

spec-categories:
	python scripts/spec_coverage.py --by-category

spec-missing:
	python scripts/spec_coverage.py --missing

# All CI gates in one command.
ci-check: lint-imports test-unit
	@echo "✅ CI gates passed"

# ── Maintenance ────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

retrain:
	sh scripts/retrain_models.sh

seed-training:
	python scripts/seed_agent_training.py
