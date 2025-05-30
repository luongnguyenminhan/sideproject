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
		print("\033[95m[WorkflowManager] Initializing WorkflowManager\033[0m")
		self.db = db
		self.langgraph_service = LangGraphService(db)
		self.workflow_types = {
			AgentType.CHAT: self._execute_chat_workflow,
			AgentType.ANALYSIS: self._execute_analysis_workflow,
			AgentType.TASK: self._execute_task_workflow,
			AgentType.CUSTOM: self._execute_custom_workflow,
		}
		print(f"\033[95m[WorkflowManager] Initialized with {len(self.workflow_types)} workflow types\033[0m")

	async def execute_workflow(self, agent: Agent, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute workflow based on agent type"""
		print(f"\033[92m[execute_workflow] Starting workflow execution for agent {agent.id} ({agent.agent_type.value})\033[0m")
		print(f"\033[92m[execute_workflow] Agent name: {agent.name}\033[0m")
		print(f"\033[92m[execute_workflow] Context keys: {list(context.keys())}\033[0m")
		print(f"\033[92m[execute_workflow] API key provided: {bool(api_key)}\033[0m")

		if agent.agent_type not in self.workflow_types:
			print(f"\033[91m[execute_workflow] ERROR: Unsupported workflow type {agent.agent_type}\033[0m")
			raise ValidationException(_('unsupported_workflow_type'))

		workflow_executor = self.workflow_types[agent.agent_type]
		print(f"\033[92m[execute_workflow] Found workflow executor: {workflow_executor.__name__}\033[0m")

		try:
			start_time = time.time()
			print(f"\033[92m[execute_workflow] Execution started at: {start_time}\033[0m")

			result = await workflow_executor(config, context, api_key)
			print(f"\033[92m[execute_workflow] Workflow executor completed successfully\033[0m")

			end_time = time.time()
			execution_time = int((end_time - start_time) * 1000)
			print(f"\033[92m[execute_workflow] Execution time: {execution_time}ms\033[0m")

			# Add execution metadata
			result['metadata']['execution_time_ms'] = execution_time
			result['metadata']['agent_id'] = agent.id
			result['metadata']['agent_name'] = agent.name
			result['metadata']['workflow_type'] = agent.agent_type.value
			print(f"\033[92m[execute_workflow] Added metadata to result\033[0m")

			return result

		except Exception as e:
			print(f"\033[91m[execute_workflow] ERROR: {str(e)}\033[0m")
			raise ValidationException(f'{_("workflow_execution_failed")}: {str(e)}')

	async def execute_streaming_workflow(self, agent: Agent, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> AsyncGenerator[Dict[str, Any], None]:
		"""Execute streaming workflow based on agent type"""
		print(f"\033[93m[execute_streaming_workflow] Starting streaming workflow for agent {agent.id} ({agent.agent_type.value})\033[0m")
		print(f"\033[93m[execute_streaming_workflow] Agent name: {agent.name}\033[0m")
		print(f"\033[93m[execute_streaming_workflow] Context keys: {list(context.keys())}\033[0m")
		print(f"\033[93m[execute_streaming_workflow] API key provided: {bool(api_key)}\033[0m")

		if agent.agent_type not in self.workflow_types:
			print(f"\033[91m[execute_streaming_workflow] ERROR: Unsupported workflow type {agent.agent_type}\033[0m")
			yield {'type': 'error', 'message': _('unsupported_workflow_type')}
			return

		try:
			start_time = time.time()
			print(f"\033[93m[execute_streaming_workflow] Streaming started at: {start_time}\033[0m")

			# For streaming, we'll use the LangGraph service directly
			# but add agent-specific preprocessing
			enhanced_context = self._enhance_context_for_agent_type(agent.agent_type, context, config)
			print(f"\033[93m[execute_streaming_workflow] Enhanced context keys: {list(enhanced_context.keys())}\033[0m")
			print(f"\033[93m[execute_streaming_workflow] Context focus: {enhanced_context.get('focus', 'unknown')}\033[0m")

			chunk_count = 0
			async for chunk in self.langgraph_service.execute_streaming_workflow(config, enhanced_context, api_key):
				chunk_count += 1
				print(f"\033[93m[execute_streaming_workflow] Processing chunk #{chunk_count}, type: {chunk.get('type', 'unknown')}\033[0m")
				
				# Add agent metadata to chunks
				if chunk.get('type') == 'metadata':
					print(f"\033[93m[execute_streaming_workflow] Adding metadata to chunk #{chunk_count}\033[0m")
					chunk['data']['agent_id'] = agent.id
					chunk['data']['agent_name'] = agent.name
					chunk['data']['workflow_type'] = agent.agent_type.value
					chunk['data']['execution_time_ms'] = int((time.time() - start_time) * 1000)
					print(f"\033[93m[execute_streaming_workflow] Metadata added: agent_id={agent.id}, type={agent.agent_type.value}\033[0m")

				yield chunk

			print(f"\033[93m[execute_streaming_workflow] Streaming completed. Total chunks: {chunk_count}\033[0m")

		except Exception as e:
			print(f"\033[91m[execute_streaming_workflow] ERROR: {str(e)}\033[0m")
			yield {'type': 'error', 'message': f'{_("streaming_workflow_failed")}: {str(e)}'}

	async def validate_workflow_config(self, agent_type: AgentType, config: AgentConfig) -> bool:
		"""Validate workflow configuration for agent type"""
		print(f"\033[96m[validate_workflow_config] Validating config for agent type: {agent_type.value}\033[0m")
		print(f"\033[96m[validate_workflow_config] Config temperature: {config.temperature}\033[0m")
		print(f"\033[96m[validate_workflow_config] Config max_tokens: {config.max_tokens}\033[0m")
		print(f"\033[96m[validate_workflow_config] System prompt exists: {bool(config.system_prompt)}\033[0m")

		try:
			# Basic validation
			if not config.system_prompt:
				print(f"\033[91m[validate_workflow_config] FAIL: No system prompt\033[0m")
				return False

			# Agent-specific validation
			if agent_type == AgentType.CHAT:
				result = self._validate_chat_config(config)
				print(f"\033[96m[validate_workflow_config] Chat validation result: {result}\033[0m")
				return result
			elif agent_type == AgentType.ANALYSIS:
				result = self._validate_analysis_config(config)
				print(f"\033[96m[validate_workflow_config] Analysis validation result: {result}\033[0m")
				return result
			elif agent_type == AgentType.TASK:
				result = self._validate_task_config(config)
				print(f"\033[96m[validate_workflow_config] Task validation result: {result}\033[0m")
				return result
			else:
				print(f"\033[96m[validate_workflow_config] Custom agent - validation passed\033[0m")
				return True  # Custom agents have flexible configs

		except Exception as e:
			print(f"\033[91m[validate_workflow_config] ERROR during validation: {str(e)}\033[0m")
			return False

	def get_workflow_capabilities(self, agent_type: AgentType) -> Dict[str, Any]:
		"""Get capabilities and features for workflow type"""
		print(f"\033[94m[get_workflow_capabilities] Getting capabilities for agent type: {agent_type.value}\033[0m")

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
		print(f"\033[94m[get_workflow_capabilities] Capabilities found: {list(result.keys())}\033[0m")
		return result

	async def _execute_chat_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute chat-specific workflow"""
		print(f"\033[92m[_execute_chat_workflow] Executing chat workflow\033[0m")
		print(f"\033[92m[_execute_chat_workflow] Original context keys: {list(context.keys())}\033[0m")

		# Enhance context for conversational AI
		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'conversational'

		# Add conversational prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on maintaining natural conversation flow and context awareness. Provide helpful, engaging responses.'
			print(f"\033[92m[_execute_chat_workflow] Added system enhancement\033[0m")

		print(f"\033[92m[_execute_chat_workflow] Enhanced context keys: {list(enhanced_context.keys())}\033[0m")
		print(f"\033[92m[_execute_chat_workflow] Calling LangGraph service\033[0m")

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		print(f"\033[92m[_execute_chat_workflow] Chat workflow completed\033[0m")
		return result

	async def _execute_analysis_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute analysis-specific workflow"""
		print(f"\033[92m[_execute_analysis_workflow] Executing analysis workflow\033[0m")
		print(f"\033[92m[_execute_analysis_workflow] Original context keys: {list(context.keys())}\033[0m")

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'analytical'

		# Add analytical prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on data analysis, pattern recognition, and insight generation. Provide structured, evidence-based responses with clear reasoning.'
			print(f"\033[92m[_execute_analysis_workflow] Added system enhancement\033[0m")

		print(f"\033[92m[_execute_analysis_workflow] Enhanced context keys: {list(enhanced_context.keys())}\033[0m")
		print(f"\033[92m[_execute_analysis_workflow] Calling LangGraph service\033[0m")

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		print(f"\033[92m[_execute_analysis_workflow] Analysis workflow completed\033[0m")
		return result

	async def _execute_task_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute task-specific workflow"""
		print(f"\033[92m[_execute_task_workflow] Executing task workflow\033[0m")
		print(f"\033[92m[_execute_task_workflow] Original context keys: {list(context.keys())}\033[0m")

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'task_oriented'

		# Add task-oriented prompts
		if config.system_prompt:
			enhanced_context['system_enhancement'] = 'Focus on task management, organization, and actionable guidance. Provide structured, step-by-step responses.'
			print(f"\033[92m[_execute_task_workflow] Added system enhancement\033[0m")

		print(f"\033[92m[_execute_task_workflow] Enhanced context keys: {list(enhanced_context.keys())}\033[0m")
		print(f"\033[92m[_execute_task_workflow] Calling LangGraph service\033[0m")

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		print(f"\033[92m[_execute_task_workflow] Task workflow completed\033[0m")
		return result

	async def _execute_custom_workflow(self, config: AgentConfig, context: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
		"""Execute custom workflow"""
		print(f"\033[92m[_execute_custom_workflow] Executing custom workflow\033[0m")
		print(f"\033[92m[_execute_custom_workflow] Original context keys: {list(context.keys())}\033[0m")

		enhanced_context = context.copy()
		enhanced_context['workflow_type'] = 'custom'

		# Use custom workflow config if available
		workflow_config = config.workflow_config or {}
		enhanced_context['custom_config'] = workflow_config
		print(f"\033[92m[_execute_custom_workflow] Custom config keys: {list(workflow_config.keys())}\033[0m")

		print(f"\033[92m[_execute_custom_workflow] Enhanced context keys: {list(enhanced_context.keys())}\033[0m")
		print(f"\033[92m[_execute_custom_workflow] Calling LangGraph service\033[0m")

		result = await self.langgraph_service.execute_workflow(config, enhanced_context, api_key)
		print(f"\033[92m[_execute_custom_workflow] Custom workflow completed\033[0m")
		return result

	def _enhance_context_for_agent_type(self, agent_type: AgentType, context: Dict[str, Any], config: AgentConfig) -> Dict[str, Any]:
		"""Enhance context based on agent type"""
		print(f"\033[97m[_enhance_context_for_agent_type] Enhancing context for agent type: {agent_type.value}\033[0m")
		print(f"\033[97m[_enhance_context_for_agent_type] Input context keys: {list(context.keys())}\033[0m")

		enhanced = context.copy()

		if agent_type == AgentType.CHAT:
			enhanced['focus'] = 'conversation'
			enhanced['style'] = 'friendly_helpful'
			print(f"\033[97m[_enhance_context_for_agent_type] Set CHAT focus and style\033[0m")
		elif agent_type == AgentType.ANALYSIS:
			enhanced['focus'] = 'analysis'
			enhanced['style'] = 'analytical_structured'
			print(f"\033[97m[_enhance_context_for_agent_type] Set ANALYSIS focus and style\033[0m")
		elif agent_type == AgentType.TASK:
			enhanced['focus'] = 'tasks'
			enhanced['style'] = 'action_oriented'
			print(f"\033[97m[_enhance_context_for_agent_type] Set TASK focus and style\033[0m")
		else:
			enhanced['focus'] = 'custom'
			enhanced['style'] = 'flexible'
			print(f"\033[97m[_enhance_context_for_agent_type] Set CUSTOM focus and style\033[0m")

		# Add workflow-specific configuration
		workflow_config = config.workflow_config or {}
		enhanced['workflow_settings'] = workflow_config
		print(f"\033[97m[_enhance_context_for_agent_type] Added workflow settings: {list(workflow_config.keys())}\033[0m")

		print(f"\033[97m[_enhance_context_for_agent_type] Enhanced context keys: {list(enhanced.keys())}\033[0m")
		return enhanced

	def _validate_chat_config(self, config: AgentConfig) -> bool:
		"""Validate chat workflow configuration"""
		print(f"\033[96m[_validate_chat_config] Validating chat config\033[0m")
		print(f"\033[96m[_validate_chat_config] Temperature: {config.temperature} (>= 0.5 required)\033[0m")
		print(f"\033[96m[_validate_chat_config] Max tokens: {config.max_tokens} (>= 512 required)\033[0m")
		
		temp_valid = config.temperature >= 0.5
		tokens_valid = config.max_tokens >= 512
		prompt_valid = 'conversational' in config.system_prompt.lower() if config.system_prompt else True
		
		print(f"\033[96m[_validate_chat_config] Temperature valid: {temp_valid}\033[0m")
		print(f"\033[96m[_validate_chat_config] Tokens valid: {tokens_valid}\033[0m")
		print(f"\033[96m[_validate_chat_config] Prompt valid: {prompt_valid}\033[0m")
		
		result = temp_valid and tokens_valid and prompt_valid
		print(f"\033[96m[_validate_chat_config] Final validation result: {result}\033[0m")
		return result

	def _validate_analysis_config(self, config: AgentConfig) -> bool:
		"""Validate analysis workflow configuration"""
		print(f"\033[96m[_validate_analysis_config] Validating analysis config\033[0m")
		print(f"\033[96m[_validate_analysis_config] Temperature: {config.temperature} (<= 0.5 required)\033[0m")
		print(f"\033[96m[_validate_analysis_config] Max tokens: {config.max_tokens} (>= 1024 required)\033[0m")
		
		temp_valid = config.temperature <= 0.5
		tokens_valid = config.max_tokens >= 1024
		prompt_valid = 'analys' in config.system_prompt.lower() if config.system_prompt else True
		
		print(f"\033[96m[_validate_analysis_config] Temperature valid: {temp_valid}\033[0m")
		print(f"\033[96m[_validate_analysis_config] Tokens valid: {tokens_valid}\033[0m")
		print(f"\033[96m[_validate_analysis_config] Prompt valid: {prompt_valid}\033[0m")
		
		result = temp_valid and tokens_valid and prompt_valid
		print(f"\033[96m[_validate_analysis_config] Final validation result: {result}\033[0m")
		return result

	def _validate_task_config(self, config: AgentConfig) -> bool:
		"""Validate task workflow configuration"""
		print(f"\033[96m[_validate_task_config] Validating task config\033[0m")
		print(f"\033[96m[_validate_task_config] Temperature: {config.temperature} (<= 0.7 required)\033[0m")
		print(f"\033[96m[_validate_task_config] Max tokens: {config.max_tokens} (>= 512 required)\033[0m")
		
		temp_valid = config.temperature <= 0.7
		tokens_valid = config.max_tokens >= 512
		prompt_valid = 'task' in config.system_prompt.lower() if config.system_prompt else True
		
		print(f"\033[96m[_validate_task_config] Temperature valid: {temp_valid}\033[0m")
		print(f"\033[96m[_validate_task_config] Tokens valid: {tokens_valid}\033[0m")
		print(f"\033[96m[_validate_task_config] Prompt valid: {prompt_valid}\033[0m")
		
		result = temp_valid and tokens_valid and prompt_valid
		print(f"\033[96m[_validate_task_config] Final validation result: {result}\033[0m")
		return result
