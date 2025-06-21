"""
LangGraph-based chat service with conversation memory and RAG functionality
Enhanced with Agentic RAG capabilities via KBRepository
"""

import asyncio
import json
import logging
import os
import time
from typing import List, Dict, Any, AsyncGenerator, Optional

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import ValidationException

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _
from .models.agent import Agent
from .services.file_indexing_service import (
	ConversationFileIndexingService,
)

## IMPORT NGOÀI MODULE CẦN XỬ LÍ - Cross module import
from app.modules.chat.repository.file_repo import FileRepo
from sqlalchemy.orm import Session

from .workflows.chat_workflow.config.workflow_config import (
	WorkflowConfig,
)

logger = logging.getLogger(__name__)


class LangGraphService(object):
	"""Optimized LangGraph service with Agentic RAG integration via KBRepository"""

	# Global workflow cache - shared across all instances
	_global_workflow = None
	_file_indexing_service = None
	_file_repo = None

	def __init__(self, db: Session):
		self.db = db
		# Initialize global workflow if not exists
		if LangGraphService._global_workflow is None:
			LangGraphService._init_global_workflow(db)
		else:
			pass
		# Initialize shared services (only file indexing with Agentic RAG)
		if LangGraphService._file_indexing_service is None:
			LangGraphService._file_indexing_service = ConversationFileIndexingService(db)
		if LangGraphService._file_repo is None:
			LangGraphService._file_repo = FileRepo(db)

	@classmethod
	def _init_global_workflow(cls, db_session: Session):
		"""Initialize global workflow instance once"""
		try:
			from .workflows.chat_workflow import get_compiled_workflow

			cls._global_workflow = get_compiled_workflow(db_session=db_session, config=WorkflowConfig())
		except Exception as e:
			logger.error(f'\033[91m[_init_global_workflow] Failed to initialize global workflow: {str(e)}\033[0m')
			raise ValidationException(f'Workflow initialization failed: {str(e)}')

	async def _ensure_conversation_files_indexed(self, conversation_id: str):
		"""Ensure all files in conversation are indexed in Agentic RAG"""
		try:
			# Check if collection already exists
			if LangGraphService._file_indexing_service.check_collection_exists(conversation_id):
				return

			# Get files to index
			files_data = await LangGraphService._file_repo.get_files_for_indexing(conversation_id)

			if not files_data:
				return

			# Index files via Agentic RAG
			result = await LangGraphService._file_indexing_service.index_conversation_files(conversation_id, files_data)

			# Mark files as indexed in database
			if result['successful_file_ids']:
				LangGraphService._file_repo.bulk_mark_files_as_indexed(result['successful_file_ids'], success=True)

		except Exception as e:
			logger.error(f'\033[91m[_ensure_conversation_files_indexed] Error ensuring files indexed via Agentic RAG: {str(e)}\033[0m')
			# Don't raise exception - let conversation continue without RAG

	def _prepare_messages(
		self,
		system_prompt: str,
		user_message: str,
		conversation_history: List[Dict[str, Any]],
	) -> List:
		"""Prepare messages for workflow execution"""
		from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

		messages = []

		# Add system prompt
		if system_prompt:
			messages.append(SystemMessage(content=system_prompt))

		# Add conversation history
		if conversation_history:
			for msg in conversation_history:
				if msg.get('role') == 'user':
					messages.append(HumanMessage(content=msg['content']))
				elif msg.get('role') == 'assistant':
					messages.append(AIMessage(content=msg['content']))

		# Add current user message
		messages.append(HumanMessage(content=user_message))

		return messages

	async def execute_conversation(
		self,
		agent: Agent,
		conversation_id: str,
		user_message: str,
		conversation_system_prompt: str = None,
		conversation_history: List[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Execute conversation using basic workflow with Agentic RAG"""
		start_time = time.time()

		try:
			print(f'[LangGraphService] Starting conversation execution for conversation_id={conversation_id}')

			# Note: Files are now indexed automatically on upload via events to Agentic RAG

			# Prepare system prompt
			system_prompt = conversation_system_prompt or agent.default_system_prompt

			# Prepare messages
			messages = self._prepare_messages(system_prompt, user_message, conversation_history or [])

			print(f'[LangGraphService] Prepared messages: {messages}')

			# Execute workflow - use ainvoke instead of astream to avoid __end__ issues
			config = {
				'configurable': {
					'thread_id': conversation_id,
					'system_prompt': system_prompt,
				}
			}

			workflow_input = {'messages': messages}

			print(f'[LangGraphService] Invoking workflow with input: {workflow_input} and config: {config}')

			# Get result from global workflow (using ainvoke for direct result)
			final_state = await LangGraphService._global_workflow.ainvoke(workflow_input, config)

			print(f'[LangGraphService] Workflow execution completed. Final state: {final_state}')

			# Extract response from final state
			content = self._extract_response_content(final_state)
			tokens_used = self._get_tokens_used(final_state)

			end_time = time.time()
			response_time = int((end_time - start_time) * 1000)

			print(f'[LangGraphService] Response content: {content}, tokens used: {tokens_used}, response time: {response_time}ms')

			return {
				'content': content,
				'metadata': {
					'model_used': f'{agent.model_provider.value}:{agent.model_name}',
					'tokens_used': tokens_used,
					'response_time_ms': response_time,
					'conversation_id': conversation_id,
				},
			}

		except Exception as e:
			logger.error(f'\033[91m[execute_conversation] Error executing conversation: {str(e)}\033[0m')
			print(f'[LangGraphService] Exception occurred: {str(e)}')
			raise ValidationException(f'Conversation execution failed: {str(e)}')

	def _extract_response_content(self, final_state: Dict[str, Any]) -> str:
		"""Extract the AI response content from workflow final state"""
		try:
			messages = final_state.get('messages', [])
			if not messages:
				logger.warning('\033[93m[_extract_response_content] No messages in final state\033[0m')
				return 'No response generated'

			# Get the last message which should be the AI response
			last_message = messages[-1]

			# Handle different message types
			if hasattr(last_message, 'content'):
				content = last_message.content
			elif isinstance(last_message, dict):
				content = last_message.get('content', 'No content available')
			else:
				content = str(last_message)

			return content

		except Exception as e:
			logger.error(f'\033[91m[_extract_response_content] Error extracting response: {str(e)}\033[0m')
			return f'Error extracting response: {str(e)}'

	def _get_tokens_used(self, final_state: Dict[str, Any]) -> int:
		"""Get tokens used from final state"""
		try:
			# Try to extract from metadata if available
			metadata = final_state.get('metadata', {})
			return metadata.get('tokens_used', 0)
		except:
			# Fallback: estimate based on content length
			messages = final_state.get('messages', [])
			total_chars = sum(len(str(msg)) for msg in messages)
			return total_chars // 4  # Rough estimation

	def search_conversation_context(self, conversation_id: str, query: str, top_k: int = 5) -> List[Dict]:
		"""Search conversation context using Agentic RAG file indexing service"""
		try:
			# Search via file indexing service
			documents = LangGraphService._file_indexing_service.search_conversation_context(
				conversation_id=conversation_id,
				query=query,
				top_k=top_k,
			)

			# Convert to dict format
			results = []
			for doc in documents:
				results.append({
					'content': doc.page_content,
					'metadata': doc.metadata,
				})

			return results

		except Exception as e:
			logger.error(f'\033[91m[search_conversation_context] Error searching conversation context: {str(e)}\033[0m')
			return []

	@classmethod
	def reset_global_cache(cls):
		"""Reset global workflow cache for testing or reinitialization"""
		cls._global_workflow = None
		cls._file_indexing_service = None
		cls._file_repo = None
