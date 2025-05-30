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
		print('\033[95m[DEBUG] LangGraphService.__init__ - Initializing service\033[0m')
		self.db = db
		self.api_key_dal = ApiKeyDAL(db)
		print('\033[95m[DEBUG] LangGraphService.__init__ - Service initialized successfully\033[0m')

	def _get_google_api_key(self, user_id: str) -> str:
		print(f'\033[96m[DEBUG] _get_google_api_key - Getting API key for user_id: {user_id}\033[0m')
		api_key_obj = self.api_key_dal.get_user_default_api_key(user_id, ApiProvider.GOOGLE)
		if not api_key_obj:
			print(f'\033[91m[ERROR] _get_google_api_key - No API key found for user: {user_id}\033[0m')
			raise Exception('GOOGLE_API_KEY not found cho user')
		print(f'\033[92m[DEBUG] _get_google_api_key - API key found for user: {user_id}\033[0m')
		return api_key_obj.get_api_key()

	def _get_llm(self, agent_config: AgentConfig, google_api_key: str):
		print(f'\033[93m[DEBUG] _get_llm - Creating LLM with model: {agent_config.model_name}, temp: {agent_config.temperature}, max_tokens: {agent_config.max_tokens}\033[0m')
		from langchain_google_genai import ChatGoogleGenerativeAI

		if not google_api_key:
			print('\033[94m[DEBUG] _get_llm - No API key provided, using environment variable\033[0m')
			google_api_key = os.getenv('GOOGLE_API_KEY')

		print(f'\033[93m[DEBUG] _get_llm - API key available: {"Yes" if google_api_key else "No"}\033[0m')
		llm = ChatGoogleGenerativeAI(model=agent_config.model_name, temperature=agent_config.temperature, max_tokens=agent_config.max_tokens, google_api_key=google_api_key)
		print(f'\033[92m[DEBUG] _get_llm - LLM created successfully\033[0m')
		return llm

	async def execute_workflow(self, agent_config: AgentConfig, context: dict, api_key: str) -> dict:
		print(f'\033[95m[DEBUG] execute_workflow - Starting workflow execution for agent type: {agent_config.agent_type}\033[0m')
		print(f'\033[96m[DEBUG] execute_workflow - Context keys: {list(context.keys())}\033[0m')
		try:
			print('\033[93m[DEBUG] execute_workflow - Creating LLM\033[0m')
			llm = self._get_llm(agent_config, api_key)

			print('\033[93m[DEBUG] execute_workflow - Creating workflow\033[0m')
			workflow = self._create_workflow(agent_config, llm)

			print('\033[93m[DEBUG] execute_workflow - Preparing workflow input\033[0m')
			workflow_input = self._prepare_workflow_input(context)
			print(f'\033[96m[DEBUG] execute_workflow - Workflow input prepared with {len(workflow_input.get("messages", []))} messages\033[0m')

			print('\033[93m[DEBUG] execute_workflow - Executing LangGraph workflow\033[0m')
			result = await self._execute_langgraph_workflow(workflow, workflow_input)
			print(f'\033[92m[DEBUG] execute_workflow - Workflow executed successfully, content length: {len(result.get("content", ""))}\033[0m')

			final_result = {
				'content': result.get('content', ''),
				'metadata': {
					'model_used': f'google:{agent_config.model_name}',
					'tokens_used': result.get('tokens_used'),
					'response_time_ms': result.get('response_time_ms'),
					'workflow_type': agent_config.agent_type,
				},
			}
			print(f'\033[92m[DEBUG] execute_workflow - Final result prepared with metadata: {final_result["metadata"]}\033[0m')
			return final_result
		except Exception as e:
			print(f'\033[91m[ERROR] execute_workflow - Error occurred: {str(e)}\033[0m')
			raise Exception(f'Lỗi workflow: {str(e)}')

	async def execute_streaming_workflow(self, agent_config: AgentConfig, context: dict, apikey: str):
		print(f'\033[95m[DEBUG] execute_streaming_workflow - Starting streaming workflow for agent type: {agent_config.agent_type}\033[0m')
		print(f'\033[96m[DEBUG] execute_streaming_workflow - Context keys: {list(context.keys())}\033[0m')
		try:
			print('\033[93m[DEBUG] execute_streaming_workflow - Creating LLM\033[0m')
			llm = self._get_llm(agent_config, apikey)

			print('\033[93m[DEBUG] execute_streaming_workflow - Creating workflow\033[0m')
			workflow = self._create_workflow(agent_config, llm)

			print('\033[93m[DEBUG] execute_streaming_workflow - Preparing workflow input\033[0m')
			workflow_input = self._prepare_workflow_input(context)
			print(f'\033[96m[DEBUG] execute_streaming_workflow - Workflow input prepared with {len(workflow_input.get("messages", []))} messages\033[0m')

			print('\033[93m[DEBUG] execute_streaming_workflow - Starting streaming execution\033[0m')
			chunk_count = 0
			async for chunk in self._execute_streaming_langgraph_workflow(workflow, workflow_input):
				chunk_count += 1
				print(f'\033[94m[DEBUG] execute_streaming_workflow - Yielding chunk #{chunk_count}: {chunk.get("type", "unknown")}\033[0m')
				yield chunk
			print(f'\033[92m[DEBUG] execute_streaming_workflow - Streaming completed, total chunks: {chunk_count}\033[0m')
		except Exception as e:
			print(f'\033[91m[ERROR] execute_streaming_workflow - Error occurred: {str(e)}\033[0m')
			yield {'type': 'error', 'message': f'Lỗi workflow: {str(e)}'}

	def _create_workflow(self, config: AgentConfig, llm):
		print(f'\033[95m[DEBUG] _create_workflow - Creating workflow with system prompt length: {len(config.system_prompt) if config.system_prompt else 0}\033[0m')
		from langgraph.prebuilt import create_react_agent
		from langgraph.checkpoint.memory import MemorySaver

		tools = []
		print(f'\033[96m[DEBUG] _create_workflow - Tools count: {len(tools)}\033[0m')
		memory = MemorySaver()
		print('\033[93m[DEBUG] _create_workflow - Creating react agent\033[0m')
		workflow = create_react_agent(llm, tools, checkpointer=memory, state_modifier=config.system_prompt)
		print('\033[92m[DEBUG] _create_workflow - Workflow created successfully\033[0m')
		return workflow

	def _prepare_workflow_input(self, context: dict) -> dict:
		print(f'\033[95m[DEBUG] _prepare_workflow_input - Preparing input for context with keys: {list(context.keys())}\033[0m')
		from langchain_core.messages import HumanMessage, SystemMessage

		messages = []
		if context['config'].get('system_prompt'):
			print(f'\033[96m[DEBUG] _prepare_workflow_input - Adding system prompt: {len(context["config"]["system_prompt"])} chars\033[0m')
			messages.append(SystemMessage(content=context['config']['system_prompt']))

		conversation_history = context.get('conversation_history', [])
		print(f'\033[96m[DEBUG] _prepare_workflow_input - Processing {len(conversation_history)} conversation history items\033[0m')
		for i, memory in enumerate(conversation_history):
			if memory.get('role') == 'user':
				print(f'\033[94m[DEBUG] _prepare_workflow_input - Adding user message #{i}: {len(memory["content"])} chars\033[0m')
				messages.append(HumanMessage(content=memory['content']))

		user_message = context['user_message']
		print(f'\033[96m[DEBUG] _prepare_workflow_input - Adding current user message: {len(user_message)} chars\033[0m')
		messages.append(HumanMessage(content=user_message))

		workflow_input = {'messages': messages, 'context': context}
		print(f'\033[92m[DEBUG] _prepare_workflow_input - Workflow input prepared with {len(messages)} total messages\033[0m')
		return workflow_input

	async def _execute_langgraph_workflow(self, workflow, workflow_input: dict) -> dict:
		print('\033[95m[DEBUG] _execute_langgraph_workflow - Starting workflow execution\033[0m')
		import time

		start_time = time.time()
		thread_id = workflow_input.get('context', {}).get('timestamp', 'default')
		print(f'\033[96m[DEBUG] _execute_langgraph_workflow - Using thread_id: {thread_id}\033[0m')
		config = {'configurable': {'thread_id': thread_id}}
		result = None
		chunk_count = 0

		print('\033[93m[DEBUG] _execute_langgraph_workflow - Starting workflow stream\033[0m')
		for chunk in workflow.stream(workflow_input, config):
			chunk_count += 1
			print(f'\033[94m[DEBUG] _execute_langgraph_workflow - Processing chunk #{chunk_count}: {list(chunk.keys())}\033[0m')
			if 'agent' in chunk:
				result = chunk['agent']['messages'][-1]
				print(f'\033[94m[DEBUG] _execute_langgraph_workflow - Found agent result in chunk #{chunk_count}\033[0m')

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)
		print(f'\033[96m[DEBUG] _execute_langgraph_workflow - Workflow completed in {response_time}ms with {chunk_count} chunks\033[0m')

		content = result.content if result else 'no_response_generated'
		tokens_used = getattr(result, 'usage_metadata', {}).get('total_tokens', 0) if result else 0

		final_result = {
			'content': content,
			'tokens_used': tokens_used,
			'response_time_ms': response_time,
		}
		print(f'\033[92m[DEBUG] _execute_langgraph_workflow - Result: content_length={len(content)}, tokens={tokens_used}, time={response_time}ms\033[0m')
		return final_result

	async def _execute_streaming_langgraph_workflow(self, workflow, workflow_input: dict):
		print('\033[95m[DEBUG] _execute_streaming_langgraph_workflow - Starting streaming execution\033[0m')
		import time

		start_time = time.time()
		thread_id = workflow_input.get('context', {}).get('timestamp', 'default')
		print(f'\033[96m[DEBUG] _execute_streaming_langgraph_workflow - Using thread_id: {thread_id}\033[0m')
		config = {'configurable': {'thread_id': thread_id}}
		full_content = ''
		token_count = 0
		chunk_count = 0

		print("\033[93m[DEBUG] _execute_streaming_langgraph_workflow - Starting workflow stream with mode 'values'\033[0m")
		for chunk in workflow.stream(workflow_input, config, stream_mode='values'):
			chunk_count += 1
			print(f'\033[94m[DEBUG] _execute_streaming_langgraph_workflow - Processing chunk #{chunk_count}: {list(chunk.keys())}\033[0m')

			if 'agent' in chunk and 'messages' in chunk['agent']:
				message = chunk['agent']['messages'][-1]
				print(f'\033[94m[DEBUG] _execute_streaming_langgraph_workflow - Found agent message in chunk #{chunk_count}\033[0m')

				if hasattr(message, 'content'):
					new_content = message.content[len(full_content) :]
					if new_content:
						full_content = message.content
						print(f'\033[96m[DEBUG] _execute_streaming_langgraph_workflow - New content: {len(new_content)} chars, total: {len(full_content)} chars\033[0m')
						yield {'type': 'content', 'content': new_content, 'total_content': full_content}

				if hasattr(message, 'usage_metadata'):
					token_count = message.usage_metadata.get('total_tokens', 0)
					print(f'\033[96m[DEBUG] _execute_streaming_langgraph_workflow - Token count updated: {token_count}\033[0m')

		end_time = time.time()
		response_time = int((end_time - start_time) * 1000)
		print(f'\033[92m[DEBUG] _execute_streaming_langgraph_workflow - Streaming completed: {chunk_count} chunks, {response_time}ms, {token_count} tokens\033[0m')

		metadata = {'tokens_used': token_count, 'response_time_ms': response_time, 'completed': True}
		print(f'\033[92m[DEBUG] _execute_streaming_langgraph_workflow - Yielding final metadata: {metadata}\033[0m')
		yield {'type': 'metadata', 'data': metadata}
