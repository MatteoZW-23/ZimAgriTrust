"""Create agent_assignments table.

The AgentAssignment model exists in app/models/agent.py but the table
was never created in any migration, causing ProgrammingError on
GET /api/v1/admin/agents/stats.

Revision ID: 0043
Revises: 0042
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_assignments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            assignment_type VARCHAR(20) NOT NULL,
            listing_id UUID REFERENCES listings(id) ON DELETE SET NULL,
            order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
            dispute_id UUID REFERENCES disputes(id) ON DELETE SET NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'assigned',
            priority INTEGER NOT NULL DEFAULT 1,
            assigned_at TIMESTAMPTZ DEFAULT now(),
            accepted_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            deadline TIMESTAMPTZ,
            agent_notes TEXT,
            resolution TEXT,
            bounty_amount FLOAT DEFAULT 0.0,
            bonus_amount FLOAT DEFAULT 0.0,
            is_paid BOOLEAN DEFAULT FALSE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_assignments_agent_id ON agent_assignments(agent_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_assignments_status ON agent_assignments(status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_assignments")
