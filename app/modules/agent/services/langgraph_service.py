import os
from typing import Dict, Any, AsyncGenerator, Optional
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from app.modules.agent.models.agent import Agent
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class LangGraphService:
	"""Ultra-simplified LangGraph service using agent with embedded config and API key"""

	def __init__(self, db: Session):
		logger.info('LangGraphService.__init__ - Initializing service')
		self.db = db
		logger.info('LangGraphService.__init__ - Service initialized successfully')

	def _get_llm(self, agent: Agent):
		"""Create LLM instance from agent with embedded config"""
		logger.info(f'_get_llm - Creating LLM with model: {agent.model_name}, temp: {agent.temperature}')
		from langchain_google_genai import ChatGoogleGenerativeAI

		# Use agent's embedded API key or environment variable
		api_key = agent.get_api_key() or os.getenv('GOOGLE_API_KEY')

		if not api_key:
			logger.info('ERROR _get_llm - No API key found in agent or environment')
			raise ValidationException(_('google_api_key_not_found'))

		llm = ChatGoogleGenerativeAI(
			model=agent.model_name,
			temperature=agent.temperature,
			max_tokens=agent.max_tokens,
			google_api_key=api_key,
		)
		logger.info('_get_llm - LLM created successfully')
		return llm

	async def execute_conversation_workflow(
		self,
		agent: Agent,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: list = None,
	) -> dict:
		"""Execute workflow for conversation using agent with embedded config"""
		logger.info(f'execute_conversation_workflow - Starting for conversation: {conversation_id}')

		try:
			# Create LLM using agent's embedded config and API key
			llm = self._get_llm(agent)

			# Create workflow
			workflow = self._create_workflow(agent, llm, conversation_system_prompt)

			# Prepare input
			workflow_input = self._prepare_workflow_input(
				conversation_system_prompt or agent.default_system_prompt,
				user_message,
				conversation_history or [],
			)

			# Execute workflow
			result = await self._execute_langgraph_workflow(workflow, workflow_input, conversation_id)

			return {
				'content': result.get('content', ''),
				'metadata': {
					'model_used': f'{agent.model_provider.value}:{agent.model_name}',
					'tokens_used': result.get('tokens_used'),
					'response_time_ms': result.get('response_time_ms'),
					'conversation_id': conversation_id,
				},
			}
		except Exception as e:
			logger.info(f'ERROR execute_conversation_workflow - Error: {str(e)}')
			raise ValidationException(f'{_("workflow_execution_failed")}: {str(e)}')

	async def execute_streaming_conversation_workflow(
		self,
		agent: Agent,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: list = None,
	):
		"""Execute streaming workflow for conversation using agent with embedded config"""
		logger.info(f'execute_streaming_conversation_workflow - Starting for conversation: {conversation_id}')

		try:
			# Create LLM using agent's embedded config and API key
			llm = self._get_llm(agent)

			# Create workflow
			workflow = self._create_workflow(agent, llm, conversation_system_prompt)

			# Prepare input
			workflow_input = self._prepare_workflow_input(
				conversation_system_prompt or agent.default_system_prompt,
				user_message,
				conversation_history or [],
			)

			# Execute streaming
			async for chunk in self._execute_streaming_langgraph_workflow(workflow, workflow_input, conversation_id):
				yield chunk

		except Exception as e:
			logger.info(f'ERROR execute_streaming_conversation_workflow - Error: {str(e)}')
			yield {
				'type': 'error',
				'message': f'{_("workflow_execution_failed")}: {str(e)}',
			}

	def _create_workflow(self, agent: Agent, llm, conversation_system_prompt: str = None):
		"""Create LangGraph workflow using agent config"""
		from langgraph.prebuilt import create_react_agent
		from langgraph.checkpoint.memory import MemorySaver

		# Use tools from agent's embedded config
		tools = []  # Add tools based on agent.tools_config if needed
		memory = MemorySaver()

		# Use conversation-specific prompt or agent's default
		system_prompt = conversation_system_prompt or agent.default_system_prompt

		workflow = create_react_agent(llm, tools, checkpointer=memory, state_modifier=system_prompt)
		return workflow

	def _prepare_workflow_input(self, system_prompt: str, user_message: str, conversation_history: list) -> dict:
		"""Prepare input for workflow execution"""
		from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

		messages = []

		# Add system prompt
		if system_prompt:
			messages.append(SystemMessage(content=system_prompt))

		# Add conversation history
		for msg in conversation_history:
			if msg.get('role') == 'user':
				messages.append(HumanMessage(content=msg['content']))
			elif msg.get('role') == 'assistant':
				messages.append(AIMessage(content=msg['content']))

		# Add current user message
		messages.append(HumanMessage(content=user_message))

		return {'messages': messages}

	async def _execute_langgraph_workflow(self, workflow, workflow_input: dict, conversation_id: str) -> dict:
		"""Execute LangGraph workflow"""
		import time

		start_time = time.time()
		config = {'configurable': {'thread_id': conversation_id}}
		result = None

		for chunk in workflow.stream(workflow_input, config):
			if 'agent' in chunk:
				result = chunk['agent']['messages'][-1]

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)

		content = result.content if result else 'No response generated'
		tokens_used = getattr(result, 'usage_metadata', {}).get('total_tokens', 0) if result else 0

		return {
			'content': content,
			'tokens_used': tokens_used,
			'response_time_ms': response_time,
		}

	async def _execute_streaming_langgraph_workflow(self, workflow, workflow_input: dict, conversation_id: str):
		"""Execute streaming LangGraph workflow"""
		import time

		start_time = time.time()
		config = {'configurable': {'thread_id': conversation_id}}
		full_content = ''
		token_count = 0

		for chunk in workflow.stream(workflow_input, config, stream_mode='values'):
			if 'agent' in chunk and 'messages' in chunk['agent']:
				message = chunk['agent']['messages'][-1]

				if hasattr(message, 'content'):
					new_content = message.content[len(full_content) :]
					if new_content:
						full_content = message.content
						yield {
							'type': 'content',
							'content': new_content,
							'total_content': full_content,
						}

				if hasattr(message, 'usage_metadata'):
					token_count = message.usage_metadata.get('total_tokens', 0)

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)

		yield {
			'type': 'metadata',
			'data': {
				'tokens_used': token_count,
				'response_time_ms': response_time,
				'conversation_id': conversation_id,
			},
		}
