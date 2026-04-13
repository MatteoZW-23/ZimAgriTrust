# Agri Trust Marketplace Backend

FastAPI backend for a USSD-first agricultural marketplace with escrow, dispute handling, trust scoring, fraud controls, and AI-assisted decision support.

## Run locally

1. Copy `.env.example` to `.env`
2. Create a PostgreSQL database named `agri_trust`
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the API:

```bash
uvicorn app.main:app --reload
```

## Master Test Login

For QA and end-to-end testing, a master credential can be enabled through env settings:

- `MASTER_TEST_LOGIN_ENABLED=true`
- `MASTER_TEST_PHONE=+263777777777`
- `MASTER_TEST_PASSWORD=master`
- `MASTER_TEST_ALIAS=master`

When enabled, the backend accepts equivalent phone formats (`+263777777777`, `263777777777`, `0777777777`) and auto-provisions the master admin account if it does not exist.

## Notes

- PostgreSQL is the target production database.
- Redis is used for session storage and caching. If Redis is unavailable, the prototype falls back to an in-memory session store so demo flows still work.
- Tables are auto-created on startup for prototype convenience.
- After creating an admin account, call `POST /api/v1/admin/seed-demo` to preload a farmer, buyer, agent, admin, and sample listings.
- Public self-registration is limited to farmer and buyer accounts.
- New self-registered passwords must be at least 8 characters and include upper, lower, and numeric characters.
- In the provided Docker Compose file, Redis is exposed on host port `6380`, so local backend `.env` files should use `REDIS_URL=redis://localhost:6380/0`.
