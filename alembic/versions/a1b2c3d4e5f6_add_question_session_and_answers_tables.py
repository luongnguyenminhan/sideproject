"""Add question session and answers tables for survey system

Revision ID: a1b2c3d4e5f6
Revises: 7f4552107251
Create Date: 2025-06-29 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7f4552107251'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Drop the existing question_sessions table (it seems to be for a different purpose)
    op.drop_index('ix_question_sessions_user_id', table_name='question_sessions')
    op.drop_index('ix_question_sessions_session_id', table_name='question_sessions')
    op.drop_table('question_sessions')
    
    # Create new question_sessions table for survey system
    op.create_table('question_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('update_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('parent_session_id', sa.String(length=36), nullable=True),
        sa.Column('session_type', sa.String(length=50), nullable=False),
        sa.Column('questions_data', sa.JSON(), nullable=True),
        sa.Column('session_status', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('extra_metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_session_id'], ['question_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create question_answers table
    op.create_table('question_answers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('update_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=255), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=True),
        sa.Column('answer_data', sa.JSON(), nullable=False),
        sa.Column('answer_type', sa.String(length=50), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['question_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index(op.f('ix_question_sessions_conversation_id'), 'question_sessions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_question_sessions_user_id'), 'question_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_question_sessions_session_status'), 'question_sessions', ['session_status'], unique=False)
    op.create_index(op.f('ix_question_answers_session_id'), 'question_answers', ['session_id'], unique=False)
    op.create_index(op.f('ix_question_answers_question_id'), 'question_answers', ['question_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Drop new tables
    op.drop_index(op.f('ix_question_answers_question_id'), table_name='question_answers')
    op.drop_index(op.f('ix_question_answers_session_id'), table_name='question_answers')
    op.drop_table('question_answers')
    
    op.drop_index(op.f('ix_question_sessions_session_status'), table_name='question_sessions')
    op.drop_index(op.f('ix_question_sessions_user_id'), table_name='question_sessions')
    op.drop_index(op.f('ix_question_sessions_conversation_id'), table_name='question_sessions')
    op.drop_table('question_sessions')
    
    # Recreate the old question_sessions table
    op.create_table('question_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('update_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('current_iteration', sa.Integer(), nullable=False),
        sa.Column('max_iterations', sa.Integer(), nullable=False),
        sa.Column('user_profile_data', sa.JSON(), nullable=True),
        sa.Column('existing_user_data', sa.JSON(), nullable=True),
        sa.Column('generated_questions', sa.JSON(), nullable=True),
        sa.Column('all_previous_questions', sa.JSON(), nullable=True),
        sa.Column('completeness_score', sa.Float(), nullable=False),
        sa.Column('missing_areas', sa.JSON(), nullable=True),
        sa.Column('focus_areas', sa.JSON(), nullable=True),
        sa.Column('should_continue', sa.Boolean(), nullable=False),
        sa.Column('workflow_complete', sa.Boolean(), nullable=False),
        sa.Column('total_questions_generated', sa.Integer(), nullable=False),
        sa.Column('analysis_decision', sa.JSON(), nullable=True),
        sa.Column('generation_history', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_question_sessions_session_id', 'question_sessions', ['session_id'], unique=False)
    op.create_index('ix_question_sessions_user_id', 'question_sessions', ['user_id'], unique=False)