# 🚀 Quick Start Guide - AgriTrust Backend v2.0

Get your development environment running in **10 minutes**.

## Prerequisites

- **Python 3.10+** (check: `python --version`)
- **PostgreSQL 14+** (check: `psql --version`)
- **Redis 7+** (check: `redis-cli --version`)
- **Git** (check: `git --version`)

## Step 1: Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/agritrust.git
cd agritrust/backend

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements-v2.txt
```

## Step 2: Configure Environment (2 minutes)

```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your local settings
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Minimum Configuration**:
```env
ENVIRONMENT=development
DEBUG=true

# Database (local PostgreSQL)
DATABASE_URL=postgresql://postgres:password@localhost:5432/zimagritrust

# Cache (local Redis)
REDIS_URL=redis://localhost:6379/0

# Security (generate random string for development)
JWT_SECRET=your-super-secret-key-min-32-chars!

# Logging
LOG_LEVEL=INFO
```

## Step 3: Setup Database (3 minutes)

```bash
# Create database (if not exists)
psql -U postgres -c "CREATE DATABASE zimagritrust;"

# Run migrations
alembic upgrade head

# Check it worked
psql -U postgres -d zimagritrust -c "\dt"  # List tables
```

## Step 4: Start Development Server (1 minute)

```bash
# Run with hot reload
python -m uvicorn core.main:app --reload

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

## Step 5: Access Application (1 minute)

### API Documentation
Visit **http://localhost:8000/docs** for interactive Swagger UI

### Health Check
```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

### Register New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "phone": "+263771234567",
    "password": "SecurePass123!",
    "role": "FARMER"
  }'

# Response:
# {"user_id": "123e4567-e89b-12d3-a456-426614174000", "email": "john@example.com"}
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_phone": "john@example.com",
    "password": "SecurePass123!",
    "ip_address": "127.0.0.1"
  }'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer",
#   "user_id": "123e4567-e89b-12d3-a456-426614174000"
# }
```

## Step 6: Run Tests (Optional, 2 minutes)

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=apps --cov-report=html
# Open htmlcov/index.html in browser

# Run specific test
pytest tests/example_tests.py::TestUserAggregateRoot -v

# Run only fast tests (exclude integration)
pytest tests/ -m "not integration" -v
```

## Verify Everything Works

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "phone": "+263771234567", "password": "Test123!", "role": "FARMER"}'

# 3. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_phone": "test@example.com", "password": "Test123!", "ip_address": "127.0.0.1"}'

# 4. Check docs
open http://localhost:8000/docs
```

✅ **If all 4 work, you're ready to develop!**

## Common Commands

### Development
```bash
# Run with hot reload (auto-restart on file changes)
python -m uvicorn core.main:app --reload

# Run tests while coding
pytest tests/ -v --tb=short

# Format code
black apps/ core/ tests/
isort apps/ core/ tests/

# Type checking
mypy apps/ core/

# Linting
flake8 apps/ core/ tests/
```

### Database
```bash
# Create new migration
alembic revision --autogenerate -m "Add new_column to users"

# View migrations
alembic current  # Show current version
alembic history  # Show all migrations
alembic downgrade -1  # Rollback one migration

# Connect to database
psql -U postgres -d zimagritrust
```

### Cache
```bash
# Connect to Redis
redis-cli

# View stats
redis-cli INFO stats

# Clear cache
redis-cli FLUSHALL
```

### Debugging
```bash
# Pretty print JSON response
curl -s http://localhost:8000/docs | python -m json.tool

# See detailed logs
export LOG_LEVEL=DEBUG
python -m uvicorn core.main:app --reload --log-level debug

# Debug a test
pytest tests/example_tests.py::TestUserAggregateRoot::test_user_creation -vvs --pdb
```

## Troubleshooting

### "Connection refused: localhost:5432"
```bash
# Make sure PostgreSQL is running
# Windows: Check Services (postgresql-x64-14)
# macOS: brew services start postgresql@14
# Linux: sudo systemctl start postgresql
```

### "Connection refused: localhost:6379"
```bash
# Make sure Redis is running
# Windows: redis-server.exe in cmd
# macOS: brew services start redis
# Linux: sudo systemctl start redis-server
```

### "ModuleNotFoundError: No module named 'apps'"
```bash
# Make sure you're in the backend directory
cd backend

# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### "ERROR: Database 'zimagritrust' does not exist"
```bash
# Create it
psql -U postgres -c "CREATE DATABASE zimagritrust;"
```

### Tests fail with "could not translate host name"
```bash
# Check DATABASE_URL in .env
export DATABASE_URL="postgresql://postgres:password@localhost:5432/zimagritrust"
pytest tests/
```

## Project Structure

```
backend/
├── apps/
│   ├── shared/           # Reusable domain logic & infrastructure
│   ├── auth/             # Authentication domain (complete example)
│   ├── orders/           # Order management (template structure)
│   └── [other domains]/
├── core/
│   ├── main.py           # FastAPI application factory
│   ├── container.py      # Dependency injection
│   └── config.py         # Configuration
├── tests/
│   ├── example_tests.py   # Test patterns & examples
│   └── [other tests]/
├── requirements-v2.txt   # Dependencies
├── Dockerfile            # Container image
└── alembic/              # Database migrations
```

## Next Steps

1. **Read the Architecture Guide**: `ARCHITECTURE_IMPLEMENTATION_GUIDE.md`
2. **Explore Auth Domain**: Start in `apps/auth/domain/models.py`
3. **Write a Test**: Add a test in `tests/example_tests.py`
4. **Implement Orders Domain**: Copy auth domain as template
5. **Deploy to Staging**: Push Docker image to registry

## Key Files to Know

| File | Purpose |
|------|---------|
| `core/main.py` | Application entry point |
| `apps/auth/domain/models.py` | Business logic (testable) |
| `apps/auth/application/use_cases.py` | CQRS commands/queries |
| `apps/auth/infrastructure/persistence.py` | Database layer |
| `apps/auth/api/routes.py` | HTTP endpoints |
| `core/container.py` | Dependency injection |

## Additional Resources

- 📖 **Architecture Guide**: `ARCHITECTURE_IMPLEMENTATION_GUIDE.md`
- 📖 **Backend README**: `backend/README_V2.md`
- 📖 **Executive Summary**: `IMPLEMENTATION_EXECUTIVE_SUMMARY.md`
- 🔗 **API Docs**: `http://localhost:8000/docs`
- 🧪 **Test Examples**: `tests/example_tests.py`

## Need Help?

1. **Check the docs**: `docs/` directory
2. **Review example code**: `apps/auth/` is a complete domain
3. **Look at tests**: `tests/example_tests.py` shows patterns
4. **Check GitHub issues**: Search for your error message
5. **Ask in Slack**: #agritrust-backend channel

---

**You're ready!** 🎉

Start by exploring the auth domain, then implement your first domain using it as a template.

Questions? Check `backend/README_V2.md` or the architecture guide.
