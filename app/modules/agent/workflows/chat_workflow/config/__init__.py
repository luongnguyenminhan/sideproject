"""
Configuration module cho Chat Workflow
"""

import logging

logger = logging.getLogger(__name__)

logger.info('🔧 [Config] Initializing Chat Workflow configuration module...')

from .workflow_config import WorkflowConfig
from .persona_prompts import PersonaPrompts, PersonaType

logger.info('✅ [Config] Successfully imported WorkflowConfig from workflow_config')
logger.info('✅ [Config] Successfully imported SystemPrompts, PromptTemplates, ValidationPrompts from prompts')
logger.info('✅ [Config] Successfully imported PersonaPrompts, PersonaType from persona_prompts')

__all__ = [
	'WorkflowConfig',
	'PersonaPrompts',
	'PersonaType',
]

logger.info(f'📦 [Config] Module initialization complete. Exported classes: {__all__}')
logger.info('🚀 [Config] Chat Workflow configuration module ready for use')
