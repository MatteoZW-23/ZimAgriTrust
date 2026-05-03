# Configuration Files

This directory contains all Docker and environment configuration files for the ZimAgritrust platform.

## Files

- `docker-compose.yml` - Main Docker Compose configuration (moved to root)
- `docker-compose.monitoring.yml` - Monitoring stack configuration
- `docker-compose.override.yml` - Local development overrides
- `Dockerfile.scheduler` - Dockerfile for the notebook scheduler service
- `.env.example` - Example environment variables template
- `requirements.scheduler.txt` - Python dependencies for scheduler

## Usage

Copy `.env.example` to `.env` and configure your environment variables before starting services.

```bash
# Start all services
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up

# Start with local overrides
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```
