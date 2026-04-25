"""
Schema Patcher — runs on every startup AFTER create_all.

Handles the gap between ORM model evolution and existing DB tables:
  - create_all creates missing tables but never adds columns to existing ones
  - This patcher issues ALTER TABLE ... ADD COLUMN IF NOT EXISTS for every
    column defined in the ORM that is absent from the live DB.

Safe to run multiple times — IF NOT EXISTS makes every statement idempotent.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Column type helpers
# ---------------------------------------------------------------------------

def _pg_type(col) -> str:
    """Convert a SQLAlchemy column type to a PostgreSQL DDL type string."""
    from sqlalchemy import (
        Boolean, DateTime, Enum, Float, Integer, JSON, String, Text
    )
    from sqlalchemy.dialects.postgresql import UUID

    t = col.type
    if isinstance(t, UUID):
        return "UUID"
    if isinstance(t, Boolean):
        return "BOOLEAN"
    if isinstance(t, Integer):
        return "INTEGER"
    if isinstance(t, Float):
        return "DOUBLE PRECISION"
    if isinstance(t, String):
        length = getattr(t, "length", None)
        return f"VARCHAR({length})" if length else "VARCHAR"
    if isinstance(t, Text):
        return "TEXT"
    if isinstance(t, DateTime):
        return "TIMESTAMPTZ"
    if isinstance(t, JSON):
        return "JSONB"
    if isinstance(t, Enum):
        # Use TEXT for enum columns — avoids having to create PG enum types
        return "TEXT"
    # Fallback
    return "TEXT"


def _default_clause(col) -> str:
    """Return a DEFAULT clause string if the column has a server/Python default."""
    # Nullable columns with no default are fine as NULL
    if col.nullable:
        return ""
    # Boolean defaults
    from sqlalchemy import Boolean
    if isinstance(col.type, Boolean):
        val = col.default.arg if col.default else False
        return f" DEFAULT {str(val).upper()}"
    # Integer / Float defaults
    from sqlalchemy import Integer, Float
    if isinstance(col.type, (Integer, Float)):
        val = col.default.arg if col.default else 0
        return f" DEFAULT {val}"
    return ""


# ---------------------------------------------------------------------------
# Core patcher
# ---------------------------------------------------------------------------

def apply_schema_patches(engine: Engine) -> None:
    """
    Inspects every mapped table and adds any columns that exist in the ORM
    model but are missing from the live PostgreSQL database.
    """
    from app.db.base import Base  # import here to avoid circular imports

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    patched_cols = 0
    patched_tables: list[str] = []

    with engine.begin() as conn:
        for table_name, table in Base.metadata.tables.items():
            if table_name not in existing_tables:
                # Table doesn't exist yet — create_all will handle it
                continue

            existing_cols = {
                row["name"] for row in inspector.get_columns(table_name)
            }

            for col in table.columns:
                if col.name in existing_cols:
                    continue  # already present

                pg_type = _pg_type(col)
                null_clause = "" if col.nullable else " NOT NULL"
                default_clause = _default_clause(col)

                ddl = (
                    f'ALTER TABLE "{table_name}" '
                    f'ADD COLUMN IF NOT EXISTS "{col.name}" '
                    f"{pg_type}{null_clause}{default_clause};"
                )

                try:
                    conn.execute(text(ddl))
                    logger.info(
                        "SCHEMA PATCH | %s.%s (%s) — added",
                        table_name, col.name, pg_type,
                    )
                    patched_cols += 1
                    if table_name not in patched_tables:
                        patched_tables.append(table_name)
                except Exception as exc:
                    logger.warning(
                        "SCHEMA PATCH | %s.%s — could not add: %s",
                        table_name, col.name, exc,
                    )

    if patched_cols:
        logger.info(
            "SCHEMA PATCH | Complete — %d column(s) added across tables: %s",
            patched_cols,
            ", ".join(patched_tables),
        )
    else:
        logger.info("SCHEMA PATCH | No missing columns — schema is up to date.")
