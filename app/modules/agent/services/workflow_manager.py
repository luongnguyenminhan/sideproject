from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import time

from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.models.agent import Agent, AgentType
from app.modules.agent.models.agent_config import AgentConfig
from app.modules.agent.services.langgraph_service import LangGraphService
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from sqlalchemy.orm import Session


class WorkflowManager:
	"""Manager for different workflow types and execution strategies"""

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.langgraph_service = LangGraphService(db)
		self.workflow_types = {
			AgentType.CHAT: self._execute_chat_workflow,
			AgentType.ANALYSIS: self._execute_analysis_workflow,
			AgentType.TASK: self._execute_task_workflow,
			AgentType.CUSTOM: self._execute_custom_workflow,
		}

	async def execute_workflow(self, agent: Agent, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute workflow based on agent type"""

		if agent.agent_type not in self.workflow_types:
			raise ValidationException(_('unsupported_workflow_type'))

		workflow_executor = self.workflow_types[agent.agent_type]

		try:
			start_time = time.time()

			result = await workflow_executor(config, context, api_key)

			end_time = time.time()
			execution_time = int((end_time - start_time) * 1000)

			# Add execution metadata
			result['metadata']['execution_time_ms'] = execution_time
			result['metadata']['agent_id'] = agent.id
			result['metadata']['agent_name'] = agent.name
			result['metadata']['workflow_type'] = agent.agent_type.value

			return result

		except Exception as e:
			raise ValidationException(f'{_("workflow_execution_failed")}: {str(e)}')

	async def execute_streaming_workflow(self, agent: Agent, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
		"""Execute streaming workflow based on agent type"""

		if agent.agent_type not in self.workflow_types:
			yield {'type': 'error', 'message': _('unsupported_workflow_type')}
			return

		try:
			start_time = time.time()

			# For streaming, we'll use the LangGraph service directly
			# but add agent-specific preprocessing
			enhanced_context = self._enhance_context_for_agent_type(agent.agent_type, context, config)

			chunk_count = 0
			async for chunk in self.langgraph_service.execute_streaming_workflow(config, enhanced_context, api_key):
				chunk_count += 1

				# Add agent metadata to chunks
				if chunk.get('type') == 'metadata':
					chunk['data']['agent_id'] = agent.id
					chunk['data']['agent_name'] = agent.name
					chunk['data']['workflow_type'] = agent.agent_type.value
					chunk['data']['execution_time_ms'] = int((time.time() - start_time) * 1000)

				yield chunk

		except Exception as e:
			yield {'type': 'error', 'message': f'{_("streaming_workflow_failed")}: {str(e)}'}

	async def validate_workflow_config(self, agent_type: AgentType, config: AgentConfig) -> bool:
		"""Validate workflow configuration for agent type"""

		try:
			# Basic validation
			if not config.system_prompt:
				return False

			# Agent-specific validation
			if agent_type == AgentType.CHAT:
				result = self._validate_chat_config(config)
				return result
			elif agent_type == AgentType.ANALYSIS:
				result = self._validate_analysis_config(config)
				return result
			elif agent_type == AgentType.TASK:
				result = self._validate_task_config(config)
				return result
			else:
				return True  # Custom agents have flexible configs

		except Exception as e:
			return False

	def get_workflow_capabilities(self, agent_type: AgentType) -> Dict[str, Any]:
		"""Get capabilities and features for workflow type"""

		capabilities = {
			AgentType.CHAT: {'streaming': True, 'memory': True, 'tools': ['memory_retrieval'], 'features': ['context_awareness', 'conversation_flow'], 'max_context_length': 10},
			AgentType.ANALYSIS: {
				'streaming': True,
				'memory': True,
				'tools': ['web_search', 'memory_retrieval', 'data_analysis'],
				'features': ['data_processing', 'insight_generation', 'visualization'],
				'max_context_length': 20,
			},
			AgentType.TASK: {'streaming': True, 'memory': True, 'tools': ['memory_retrieval', 'task_management'], 'features': ['task_tracking', 'scheduling', 'reminders'], 'max_context_length': 15},
			AgentType.CUSTOM: {'streaming': True, 'memory': True, 'tools': ['configurable'], 'features': ['flexible_configuration'], 'max_context_length': 'configurable'},
		}

		result = capabilities.get(agent_type, {})
		return result

	async def _execute_chat_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute chat-specific workflow"""

		# Enhance context for conversational AI
		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'conversational'

		# Add conversational prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on maintaining natural conversation flow and context awareness. Provide helpful, engaging responses.'

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		return result

	async def _execute_analysis_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute analysis-specific workflow"""

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'analytical'

		# Add analytical prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on data analysis, pattern recognition, and insight generation. Provide structured, evidence-based responses with clear reasoning.'

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		return result

	async def _execute_task_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute task-specific workflow"""

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'task_oriented'

		# Add task-oriented prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on task management, organization, and actionable guidance. Provide structured, step-by-step responses.'

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		return result

	async def _execute_custom_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute custom workflow"""

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'custom'

		# Use custom workflow config if available
		workflow_config = config.workflow_config or {}
		enhanced_context['custom_config'] = workflow_config

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		return result

	def _enhance_context_for_agent_type(self, agent_type: AgentType, context: Dict[str, Any], config: AgentConfig) -> Dict[str, Any]:
		"""Enhance context based on agent type"""

		enhanced = context.copy()

		if agent_type == AgentType.CHAT:
			enhanced['focus'] = 'conversation'
			enhanced['style'] = 'friendly_helpful'
		elif agent_type == AgentType.ANALYSIS:
			enhanced['focus'] = 'analysis'
			enhanced['style'] = 'analytical_structured'
		elif agent_type == AgentType.TASK:
			enhanced['focus'] = 'tasks'
			enhanced['style'] = 'action_oriented'
		else:
			enhanced['focus'] = 'custom'
			enhanced['style'] = 'flexible'

		# Add workflow-specific configuration
		workflow_config = config.workflow_config or {}
		enhanced['workflow_settings'] = workflow_config

		return enhanced

	def _validate_chat_config(self, config: AgentConfig) -> bool:
		"""Validate chat workflow configuration"""

		temp_valid = config.temperature >= 0.5
		tokens_valid = config.max_tokens >= 512
		prompt_valid = 'conversational' in config.system_prompt.lower() if config.system_prompt else True

		result = temp_valid and tokens_valid and prompt_valid
		return result

	def _validate_analysis_config(self, config: AgentConfig) -> bool:
		"""Validate analysis workflow configuration"""

		temp_valid = config.temperature <= 0.5
		tokens_valid = config.max_tokens >= 1024
		prompt_valid = 'analys' in config.system_prompt.lower() if config.system_prompt else True

		result = temp_valid and tokens_valid and prompt_valid
		return result

	def _validate_task_config(self, config: AgentConfig) -> bool:
		"""Validate task workflow configuration"""

		temp_valid = config.temperature <= 0.7
		tokens_valid = config.max_tokens >= 512
		prompt_valid = 'task' in config.system_prompt.lower() if config.system_prompt else True

		result = temp_valid and tokens_valid and prompt_valid
		return result
