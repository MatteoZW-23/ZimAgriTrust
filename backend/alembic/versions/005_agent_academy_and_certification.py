from app.db.domain_migration_helpers import (
    create_domain_tables,
    drop_domain_tables,
)

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

TABLES = ['agent_applications', 'document_verification_records', 'user_verification_summaries', 'verification_queue', 'verification_audit_logs', 'training_modules', 'agent_training_progress', 'agent_contracts', 'shadowing_logs', 'classroom_courses', 'classroom_course_topics', 'classroom_resources', 'classroom_quiz_questions', 'classroom_enrollments', 'classroom_topic_progress', 'classroom_quiz_attempts', 'classroom_essay_answers', 'classroom_announcements', 'agents', 'agent_assignments']

def upgrade() -> None:
    create_domain_tables(TABLES)

def downgrade() -> None:
    drop_domain_tables(TABLES)

