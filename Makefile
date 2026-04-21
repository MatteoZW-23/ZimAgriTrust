.PHONY: run test build clean deploy

run:
	docker-compose up backend

test:
	pytest tests/

build:
	docker-compose build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +

retrain:
	python scripts/retrain_models.sh

seed-training:
	python scripts/seed_agent_training.sh

deploy:
	sh scripts/deploy.sh
