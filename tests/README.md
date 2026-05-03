# Tests

This directory contains test suites for the ZimAgritrust platform.

## Structure

- `unit/` - Unit tests for individual components
- `integration/` - Integration tests for service interactions

## Running Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run unit tests only
docker-compose exec backend pytest tests/unit/

# Run with coverage
docker-compose exec backend pytest --cov=app
```

## Test Coverage

Aim for >80% coverage on critical paths:
- Authentication flows
- Transaction processing
- API endpoints
- Database operations

## Adding Tests

1. Place unit tests in `tests/unit/`
2. Place integration tests in `tests/integration/`
3. Follow naming convention: `test_*.py`
4. Use descriptive test names
