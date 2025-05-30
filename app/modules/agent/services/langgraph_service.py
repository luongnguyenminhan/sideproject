import os
from typing import Dict, Any, AsyncGenerator, Optional
import asyncio
import json

from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from app.modules.agent.models.agent_config import AgentConfig


from app.modules.agent.models.agent_config import AgentConfig
from app.modules.chat.dal.api_key_dal import ApiKeyDAL
from app.modules.chat.models.api_key import ApiProvider
from sqlalchemy.orm import Session


class LangGraphService:
	"""Chỉ dùng Google Gemini (ChatGoogleGenerativeAI)"""

	def __init__(self, db: Session):
		self.db = db
		self.api_key_dal = ApiKeyDAL(db)

	def _get_google_api_key(self, user_id: str) -> str:
		api_key_obj = self.api_key_dal.get_user_default_api_key(user_id, ApiProvider.GOOGLE)
		if not api_key_obj:
			raise Exception('GOOGLE_API_KEY not found cho user')
		return api_key_obj.get_api_key()

	def _get_llm(self, agent_config: AgentConfig, google_api_key: str):
		from langchain_google_genai import ChatGoogleGenerativeAI

		if not google_api_key:
			print("\033[93m[DEBUG] _get_llm - GOOGLE_API_KEY not provided, using environment variable\033[0m")
			google_api_key = os.getenv('GOOGLE_API_KEY')
		print(f"\033[93m[DEBUG] _get_llm - Using GOOGLE_API_KEY: {google_api_key}\033[0m")
		llm = ChatGoogleGenerativeAI(model=agent_config.model_name, temperature=agent_config.temperature, max_tokens=agent_config.max_tokens, google_api_key=google_api_key)
		return llm

	async def execute_workflow(self, agent_config: AgentConfig, context: dict, api_key: str) -> dict:
		try:
			llm = self._get_llm(agent_config, api_key)

			workflow = self._create_workflow(agent_config, llm)

			workflow_input = self._prepare_workflow_input(context)

			result = await self._execute_langgraph_workflow(workflow, workflow_input)

			final_result = {
				'content': result.get('content', ''),
				'metadata': {
					'model_used': f'google:{agent_config.model_name}',
					'tokens_used': result.get('tokens_used'),
					'response_time_ms': result.get('response_time_ms'),
					'workflow_type': agent_config.agent_type,
				},
			}
			return final_result
		except Exception as e:
			raise Exception(f'Lỗi workflow: {str(e)}')

	async def execute_streaming_workflow(self, agent_config: AgentConfig, context: dict, apikey: str):
		try:
			llm = self._get_llm(agent_config, apikey)

			workflow = self._create_workflow(agent_config, llm)

			workflow_input = self._prepare_workflow_input(context)

			chunk_count = 0
			async for chunk in self._execute_streaming_langgraph_workflow(workflow, workflow_input):
				chunk_count += 1
				yield chunk
		except Exception as e:
			yield {'type': 'error', 'message': f'Lỗi workflow: {str(e)}'}

	def _create_workflow(self, config: AgentConfig, llm):
		from langgraph.prebuilt import create_react_agent
		from langgraph.checkpoint.memory import MemorySaver

		tools = []
		memory = MemorySaver()
		workflow = create_react_agent(llm, tools, checkpointer=memory, state_modifier=config.system_prompt)
		return workflow

	def _prepare_workflow_input(self, context: dict) -> dict:
		from langchain_core.messages import HumanMessage, SystemMessage

		messages = []
		if context['config'].get('system_prompt'):
			messages.append(SystemMessage(content=context['config']['system_prompt']))

		conversation_history = context.get('conversation_history', [])
		for i, memory in enumerate(conversation_history):
			if memory.get('role') == 'user':
				messages.append(HumanMessage(content=memory['content']))

		user_message = context['user_message']
		messages.append(HumanMessage(content=user_message))

		workflow_input = {'messages': messages, 'context': context}
		return workflow_input

	async def _execute_langgraph_workflow(self, workflow, workflow_input: dict) -> dict:
		import time

		start_time = time.time()
		thread_id = workflow_input.get('context', {}).get('timestamp', 'default')
		config = {'configurable': {'thread_id': thread_id}}
		result = None
		chunk_count = 0

		for chunk in workflow.stream(workflow_input, config):
			chunk_count += 1
			if 'agent' in chunk:
				result = chunk['agent']['messages'][-1]

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)

		content = result.content if result else 'no_response_generated'
		tokens_used = getattr(result, 'usage_metadata', {}).get('total_tokens', 0) if result else 0

		final_result = {
			'content': content,
			'tokens_used': tokens_used,
			'response_time_ms': response_time,
		}
		return final_result

	async def _execute_streaming_langgraph_workflow(self, workflow, workflow_input: dict):
		import time

		start_time = time.time()
		thread_id = workflow_input.get('context', {}).get('timestamp', 'default')
		config = {'configurable': {'thread_id': thread_id}}
		full_content = ''
		token_count = 0
		chunk_count = 0

		print("\033[93m[DEBUG] _execute_streaming_langgraph_workflow - Starting workflow stream with mode 'values'\033[0m")
		for chunk in workflow.stream(workflow_input, config, stream_mode='values'):
			chunk_count += 1

			if 'agent' in chunk and 'messages' in chunk['agent']:
				message = chunk['agent']['messages'][-1]

				if hasattr(message, 'content'):
					new_content = message.content[len(full_content) :]
					if new_content:
						full_content = message.content
						yield {'type': 'content', 'content': new_content, 'total_content': full_content}

				if hasattr(message, 'usage_metadata'):
					token_count = message.usage_metadata.get('total_tokens', 0)

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)

		metadata = {'tokens_used': token_count, 'response_time_ms': response_time, 'completed': True}
		yield {'type': 'metadata', 'data': metadata}
