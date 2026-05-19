"""classroom_lms

Revision ID: 0034
Revises: 0033
Create Date: 2025-01-18 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0034'
down_revision = '51f1bf200556'
branch_labels = None
depends_on = None


def upgrade():
    # Use string types instead of ENUM to avoid duplicate type errors
    # The models will handle validation
    
    # Create classroom_courses table
    op.create_table(
        'classroom_courses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('module_number', sa.Integer(), nullable=False),
        sa.Column('passing_score', sa.Float(), nullable=False, server_default='80.0'),
        sa.Column('estimated_hours', sa.Float(), nullable=False, server_default='2.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    
    # Create classroom_course_topics table
    op.create_table(
        'classroom_course_topics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('order_sequence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_course_topics_course_id', 'classroom_course_topics', ['course_id'])
    
    # Create classroom_resources table
    op.create_table(
        'classroom_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_courses.id'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_course_topics.id', ondelete='CASCADE'), nullable=True),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('order_sequence', sa.Integer(), nullable=False),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('passing_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_resources_course_id', 'classroom_resources', ['course_id'])
    op.create_index('ix_classroom_resources_topic_id', 'classroom_resources', ['topic_id'])
    
    # Create classroom_quiz_questions table
    op.create_table(
        'classroom_quiz_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(50), nullable=False),
        sa.Column('options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('correct_answer', sa.String(500), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('order_sequence', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_quiz_questions_resource_id', 'classroom_quiz_questions', ['resource_id'])
    
    # Create classroom_enrollments table
    op.create_table(
        'classroom_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id'), nullable=False),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='enrolled'),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_enrollments_agent_id', 'classroom_enrollments', ['agent_id'])
    op.create_index('ix_classroom_enrollments_course_id', 'classroom_enrollments', ['course_id'])
    
    # Create classroom_topic_progress table
    op.create_table(
        'classroom_topic_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('enrollment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_course_topics.id'), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_topic_progress_enrollment_id', 'classroom_topic_progress', ['enrollment_id'])
    op.create_index('ix_classroom_topic_progress_topic_id', 'classroom_topic_progress', ['topic_id'])
    
    # Create classroom_quiz_attempts table
    op.create_table(
        'classroom_quiz_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('enrollment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_enrollments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('answers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('passed', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_classroom_quiz_attempts_enrollment_id', 'classroom_quiz_attempts', ['enrollment_id'])
    op.create_index('ix_classroom_quiz_attempts_resource_id', 'classroom_quiz_attempts', ['resource_id'])
    
    # Create classroom_essay_answers table
    op.create_table(
        'classroom_essay_answers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('quiz_attempt_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_quiz_attempts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_quiz_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('grade', sa.Float(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('graded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
    )
    op.create_index('ix_classroom_essay_answers_quiz_attempt_id', 'classroom_essay_answers', ['quiz_attempt_id'])
    op.create_index('ix_classroom_essay_answers_question_id', 'classroom_essay_answers', ['question_id'])
    
    # Create classroom_announcements table
    op.create_table(
        'classroom_announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('course_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classroom_courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_classroom_announcements_course_id', 'classroom_announcements', ['course_id'])


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('classroom_announcements')
    op.drop_table('classroom_essay_answers')
    op.drop_table('classroom_quiz_attempts')
    op.drop_table('classroom_topic_progress')
    op.drop_table('classroom_enrollments')
    op.drop_table('classroom_quiz_questions')
    op.drop_table('classroom_resources')
    op.drop_table('classroom_course_topics')
    op.drop_table('classroom_courses')
    
    # Drop enums
    postgresql.ENUM(name='enrollment_status').drop(op.get_bind())
    postgresql.ENUM(name='resource_type').drop(op.get_bind())
    postgresql.ENUM(name='question_type').drop(op.get_bind())
