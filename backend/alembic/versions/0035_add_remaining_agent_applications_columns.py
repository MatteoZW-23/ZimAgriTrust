"""add remaining agent_applications columns

Revision ID: 0035
Revises: 0034
Create Date: 2026-05-23 15:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '0035'
down_revision = '0034'
branch_labels = None
depends_on = None


def upgrade():
    # Recruitment Profile columns (skip email, documents - they already exist)
    op.add_column('agent_applications', sa.Column('has_smartphone', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('agent_applications', sa.Column('has_transport', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('agent_applications', sa.Column('transport_type', sa.String(50), nullable=True))
    op.add_column('agent_applications', sa.Column('agri_experience_years', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('agent_applications', sa.Column('specializations', sa.JSON(), nullable=True, server_default='[]'))
    # Rename references to applicant_references to match model
    op.alter_column('agent_applications', 'references', new_column_name='applicant_references')
    
    # Progress tracking columns
    op.add_column('agent_applications', sa.Column('has_signed_contract', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('agent_applications', sa.Column('id_verified', sa.Boolean(), nullable=True, server_default='false'))
    
    # Training columns
    op.add_column('agent_applications', sa.Column('training_modules_completed', sa.JSON(), nullable=True, server_default='[]'))
    
    # Equipment columns
    op.add_column('agent_applications', sa.Column('equipment_issued', sa.Boolean(), nullable=True, server_default='false'))
    
    # Practical/Shadowing columns
    op.add_column('agent_applications', sa.Column('shadowing_completed', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('agent_applications', sa.Column('shadowing_supervisor_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('agent_applications', sa.Column('shadowing_rating', sa.Float(), nullable=True))
    
    # Supervised Work columns
    op.add_column('agent_applications', sa.Column('supervised_tasks_count', sa.Integer(), nullable=True, server_default='0'))
    
    # Final Review columns (reviewed_at already exists)
    op.add_column('agent_applications', sa.Column('reviewer_notes', sa.JSON(), nullable=True, server_default='[]'))
    
    # Rename submitted_at to created_at to match model
    op.alter_column('agent_applications', 'submitted_at', new_column_name='created_at')


def downgrade():
    # Rename created_at back to submitted_at
    op.alter_column('agent_applications', 'created_at', new_column_name='submitted_at')
    
    # Final Review columns
    op.drop_column('agent_applications', 'reviewer_notes')
    
    # Supervised Work columns
    op.drop_column('agent_applications', 'supervised_tasks_count')
    
    # Practical/Shadowing columns
    op.drop_column('agent_applications', 'shadowing_rating')
    op.drop_column('agent_applications', 'shadowing_supervisor_id')
    op.drop_column('agent_applications', 'shadowing_completed')
    
    # Equipment columns
    op.drop_column('agent_applications', 'equipment_issued')
    
    # Training columns
    op.drop_column('agent_applications', 'training_modules_completed')
    
    # Progress tracking columns
    op.drop_column('agent_applications', 'id_verified')
    op.drop_column('agent_applications', 'has_signed_contract')
    
    # Recruitment Profile columns
    op.alter_column('agent_applications', 'applicant_references', new_column_name='references')
    op.drop_column('agent_applications', 'specializations')
    op.drop_column('agent_applications', 'agri_experience_years')
    op.drop_column('agent_applications', 'transport_type')
    op.drop_column('agent_applications', 'has_transport')
    op.drop_column('agent_applications', 'has_smartphone')
