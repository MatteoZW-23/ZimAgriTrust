"""Add missing columns to agent_training table.

The following columns exist in the AgentTraining SQLAlchemy model but were
never added via any migration:
  - shadowing_tasks_completed
  - supervised_tasks_completed
  - field_evaluation_score
  - topics_progress
  - last_exam_started_at
  - active_exam_question_ids

Revision ID: 0041
Revises: 0040
Create Date: 2026-05-25
"""
from __future__ import annotations

from alembic import op
from sqlalchemy import text

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE agent_training
            ADD COLUMN IF NOT EXISTS shadowing_tasks_completed INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS supervised_tasks_completed INTEGER NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS field_evaluation_score FLOAT NULL,
            ADD COLUMN IF NOT EXISTS topics_progress JSONB NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS last_exam_started_at TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS active_exam_question_ids JSONB NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("""
        ALTER TABLE agent_training
            DROP COLUMN IF EXISTS shadowing_tasks_completed,
            DROP COLUMN IF EXISTS supervised_tasks_completed,
            DROP COLUMN IF EXISTS field_evaluation_score,
            DROP COLUMN IF EXISTS topics_progress,
            DROP COLUMN IF EXISTS last_exam_started_at,
            DROP COLUMN IF EXISTS active_exam_question_ids
    """))
