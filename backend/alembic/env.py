from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.models.user import User
from app.models.listing import Listing
from app.models.transaction import Transaction
from app.models.dispute import Dispute
from app.models.agent import Agent, AgentAssignment
from app.models.classroom import (
    Course, CourseTopic, Resource, QuizQuestion, Enrollment,
    TopicProgress, QuizAttempt, EssayAnswer, Announcement
)
from app.api.v1.endpoints.verification import IDVerificationRequest  # noqa: F401

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
