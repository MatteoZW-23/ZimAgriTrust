"""
Domain layer — pure business logic.

RULES (enforced by import-linter contracts):
  - This package MUST NOT import from `app.api`, `app.services`,
    `app.infrastructure`, `app.db`, `app.models`, or any third-party
    framework (SQLAlchemy, FastAPI, Pydantic, etc.).
  - Only stdlib + `app.domain` internal imports allowed.
  - Tests run in milliseconds without a database.
"""
