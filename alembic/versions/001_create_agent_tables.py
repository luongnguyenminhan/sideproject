"""Create agent tables

Revision ID: 001_agent_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_agent_tables'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_configs table
    op.create_table('agent_configs',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('model_provider', sa.Enum('openai', 'anthropic', 'google', 'groq', 'ollama'), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('temperature', sa.Float, nullable=False, default=0.7),
        sa.Column('max_tokens', sa.Integer, nullable=True, default=2048),
        sa.Column('system_prompt', sa.Text, nullable=True),
        sa.Column('tools_config', sa.JSON, nullable=True),
        sa.Column('workflow_config', sa.JSON, nullable=True),
        sa.Column('memory_config', sa.JSON, nullable=True),
        sa.Column('create_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp()),
        sa.Column('update_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('agent_type', sa.Enum('chat', 'analysis', 'task', 'custom'), nullable=False),
        sa.Column('config_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('create_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp()),
        sa.Column('update_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Create agent_memories table
    op.create_table('agent_memories',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('agent_id', sa.String(36), nullable=False),
        sa.Column('conversation_id', sa.String(36), nullable=True),
        sa.Column('memory_type', sa.Enum('short_term', 'long_term', 'context', 'workflow_state'), nullable=False),
        sa.Column('content', sa.JSON, nullable=False),
        sa.Column('importance_score', sa.Float, nullable=False, default=0.5),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('create_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp()),
        sa.Column('update_date', sa.DateTime, nullable=False, default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_agents_config', 'agents', 'agent_configs', ['config_id'], ['id'])
    op.create_foreign_key('fk_agents_user', 'agents', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_agents_created_by', 'agents', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_agent_memories_agent', 'agent_memories', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('fk_agent_memories_conversation', 'agent_memories', 'conversations', ['conversation_id'], ['id'])
    
    # Add indexes for performance
    op.create_index('idx_agents_user_id', 'agents', ['user_id'])
    op.create_index('idx_agents_config_id', 'agents', ['config_id'])
    op.create_index('idx_agents_type', 'agents', ['agent_type'])
    op.create_index('idx_agents_active', 'agents', ['is_active'])
    
    op.create_index('idx_agent_configs_type', 'agent_configs', ['agent_type'])
    op.create_index('idx_agent_configs_provider', 'agent_configs', ['model_provider'])
    
    op.create_index('idx_agent_memories_agent_id', 'agent_memories', ['agent_id'])
    op.create_index('idx_agent_memories_conversation_id', 'agent_memories', ['conversation_id'])
    op.create_index('idx_agent_memories_type', 'agent_memories', ['memory_type'])
    op.create_index('idx_agent_memories_importance', 'agent_memories', ['importance_score'])


def downgrade():
    # Drop foreign key constraints first
    op.drop_constraint('fk_agent_memories_conversation', 'agent_memories', type_='foreignkey')
    op.drop_constraint('fk_agent_memories_agent', 'agent_memories', type_='foreignkey')
    op.drop_constraint('fk_agents_created_by', 'agents', type_='foreignkey')
    op.drop_constraint('fk_agents_user', 'agents', type_='foreignkey')
    op.drop_constraint('fk_agents_config', 'agents', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_agent_memories_importance', 'agent_memories')
    op.drop_index('idx_agent_memories_type', 'agent_memories')
    op.drop_index('idx_agent_memories_conversation_id', 'agent_memories')
    op.drop_index('idx_agent_memories_agent_id', 'agent_memories')
    
    op.drop_index('idx_agent_configs_provider', 'agent_configs')
    op.drop_index('idx_agent_configs_type', 'agent_configs')
    
    op.drop_index('idx_agents_active', 'agents')
    op.drop_index('idx_agents_type', 'agents')
    op.drop_index('idx_agents_config_id', 'agents')
    op.drop_index('idx_agents_user_id', 'agents')
    
    # Drop tables
    op.drop_table('agent_memories')
    op.drop_table('agents')
    op.drop_table('agent_configs')