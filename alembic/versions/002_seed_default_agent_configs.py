"""Seed default agent configurations

Revision ID: 002_seed_agent_configs
Revises: 001_agent_tables
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '002_seed_agent_configs'
down_revision = '001_agent_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Define table structure for data insertion
    agent_configs = table('agent_configs',
        column('id', sa.String),
        column('name', sa.String),
        column('description', sa.String),
        column('agent_type', sa.String),
        column('model_provider', sa.String),
        column('model_name', sa.String),
        column('temperature', sa.Float),
        column('max_tokens', sa.Integer),
        column('system_prompt', sa.Text),
        column('tools_config', sa.JSON),
        column('workflow_config', sa.JSON),
        column('memory_config', sa.JSON),
        column('create_date', sa.DateTime),
        column('update_date', sa.DateTime),
        column('is_deleted', sa.Boolean)
    )
    
    current_time = datetime.utcnow()
    
    # Default configurations
    default_configs = [
        {
            'id': str(uuid.uuid4()),
            'name': 'default_chat_config',
            'description': 'Default configuration for chat agents',
            'agent_type': 'chat',
            'model_provider': 'openai',
            'model_name': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2048,
            'system_prompt': """You are a helpful AI assistant. You provide accurate, helpful, and friendly responses to user questions. 
You maintain context throughout the conversation and adapt your responses to the user's needs.""",
            'tools_config': {
                'web_search': False,
                'memory_retrieval': True,
                'custom_tools': []
            },
            'workflow_config': {
                'type': 'conversational',
                'memory_enabled': True,
                'context_window': 10
            },
            'memory_config': {
                'short_term_limit': 100,
                'long_term_limit': 500,
                'importance_threshold': 0.7
            },
            'create_date': current_time,
            'update_date': current_time,
            'is_deleted': False
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'default_analysis_config',
            'description': 'Default configuration for analysis agents',
            'agent_type': 'analysis',
            'model_provider': 'openai',
            'model_name': 'gpt-4',
            'temperature': 0.3,
            'max_tokens': 4096,
            'system_prompt': """You are a data analysis specialist. You help users understand data, create insights, 
and provide analytical recommendations. You focus on accuracy and clarity in your explanations.""",
            'tools_config': {
                'web_search': True,
                'memory_retrieval': True,
                'custom_tools': ['data_visualization', 'statistical_analysis']
            },
            'workflow_config': {
                'type': 'analytical',
                'memory_enabled': True,
                'context_window': 20
            },
            'memory_config': {
                'short_term_limit': 200,
                'long_term_limit': 1000,
                'importance_threshold': 0.7
            },
            'create_date': current_time,
            'update_date': current_time,
            'is_deleted': False
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'default_task_config',
            'description': 'Default configuration for task management agents',
            'agent_type': 'task',
            'model_provider': 'openai',
            'model_name': 'gpt-3.5-turbo',
            'temperature': 0.5,
            'max_tokens': 2048,
            'system_prompt': """You are a task management assistant. You help users organize, prioritize, 
and complete tasks efficiently. You provide structured and actionable guidance.""",
            'tools_config': {
                'web_search': False,
                'memory_retrieval': True,
                'custom_tools': ['task_scheduling', 'reminder_setting']
            },
            'workflow_config': {
                'type': 'task_oriented',
                'memory_enabled': True,
                'context_window': 15
            },
            'memory_config': {
                'short_term_limit': 150,
                'long_term_limit': 750,
                'importance_threshold': 0.7
            },
            'create_date': current_time,
            'update_date': current_time,
            'is_deleted': False
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'anthropic_chat_config',
            'description': 'Chat configuration using Anthropic Claude',
            'agent_type': 'chat',
            'model_provider': 'anthropic',
            'model_name': 'claude-3-sonnet-20240229',
            'temperature': 0.7,
            'max_tokens': 2048,
            'system_prompt': """You are Claude, an AI assistant created by Anthropic. You're helpful, harmless, and honest. 
You provide thoughtful responses while maintaining a conversational and engaging tone.""",
            'tools_config': {
                'web_search': False,
                'memory_retrieval': True,
                'custom_tools': []
            },
            'workflow_config': {
                'type': 'conversational',
                'memory_enabled': True,
                'context_window': 15
            },
            'memory_config': {
                'short_term_limit': 100,
                'long_term_limit': 500,
                'importance_threshold': 0.7
            },
            'create_date': current_time,
            'update_date': current_time,
            'is_deleted': False
        },
        {
            'id': str(uuid.uuid4()),
            'name': 'groq_fast_config',
            'description': 'Fast response configuration using Groq',
            'agent_type': 'chat',
            'model_provider': 'groq',
            'model_name': 'llama3-8b-8192',
            'temperature': 0.6,
            'max_tokens': 1024,
            'system_prompt': """You are a fast and efficient AI assistant. You provide quick, accurate responses 
while maintaining quality. You're optimized for speed and responsiveness.""",
            'tools_config': {
                'web_search': False,
                'memory_retrieval': True,
                'custom_tools': []
            },
            'workflow_config': {
                'type': 'conversational',
                'memory_enabled': True,
                'context_window': 8
            },
            'memory_config': {
                'short_term_limit': 80,
                'long_term_limit': 400,
                'importance_threshold': 0.7
            },
            'create_date': current_time,
            'update_date': current_time,
            'is_deleted': False
        }
    ]
    
    # Insert default configurations
    op.bulk_insert(agent_configs, default_configs)


def downgrade():
    # Remove seeded data
    op.execute("DELETE FROM agent_configs WHERE name IN ('default_chat_config', 'default_analysis_config', 'default_task_config', 'anthropic_chat_config', 'groq_fast_config')")