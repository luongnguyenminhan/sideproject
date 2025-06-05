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

from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from app.modules.agent.models.agent import Agent
from app.modules.agent.services.file_indexing_service import (
	ConversationFileIndexingService,
)
from app.modules.chat.repository.file_repo import FileRepo
from sqlalchemy.orm import Session

from app.modules.agent.workflows.chat_workflow.config.workflow_config import (
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
		logger.info('\033[94m[LangGraphService.__init__] Initializing optimized service with Agentic RAG\033[0m')
		logger.info(f'\033[96m[LangGraphService.__init__] Using database session: {db}\033[0m')
		self.db = db
		# Initialize global workflow if not exists
		logger.info('\033[95m[LangGraphService.__init__] Checking global workflow initialization\033[0m')
		if LangGraphService._global_workflow is None:
			logger.info('\033[93m[LangGraphService.__init__] Global workflow not initialized, initializing now\033[0m')
			LangGraphService._init_global_workflow(db)
		else:
			logger.info('\033[92m[LangGraphService.__init__] Global workflow already initialized\033[0m')

		# Initialize shared services (only file indexing with Agentic RAG)
		if LangGraphService._file_indexing_service is None:
			logger.info('\033[95m[LangGraphService.__init__] Initializing Agentic RAG file indexing service\033[0m')
			LangGraphService._file_indexing_service = ConversationFileIndexingService(db)
		if LangGraphService._file_repo is None:
			logger.info('\033[95m[LangGraphService.__init__] Initializing file repository\033[0m')
			LangGraphService._file_repo = FileRepo(db)

		logger.info('\033[92m[LangGraphService.__init__] Service initialized successfully with Agentic RAG\033[0m')

	@classmethod
	def _init_global_workflow(cls, db_session: Session):
		"""Initialize global workflow instance once"""
		try:
			logger.info('\033[96m[_init_global_workflow] Starting global workflow initialization\033[0m')
			from app.modules.agent.workflows.chat_workflow import get_compiled_workflow

			cls._global_workflow = get_compiled_workflow(db_session=db_session, config=WorkflowConfig())
			logger.info('\033[92m[_init_global_workflow] Global workflow initialized successfully\033[0m')
		except Exception as e:
			logger.error(f'\033[91m[_init_global_workflow] Failed to initialize global workflow: {str(e)}\033[0m')
			raise ValidationException(f'Workflow initialization failed: {str(e)}')

	async def _ensure_conversation_files_indexed(self, conversation_id: str):
		"""Ensure all files in conversation are indexed in Agentic RAG"""
		try:
			logger.info(f'\033[94m[_ensure_conversation_files_indexed] Checking Agentic RAG file indexing for conversation: {conversation_id}\033[0m')

			# Check if collection already exists
			if LangGraphService._file_indexing_service.check_collection_exists(conversation_id):
				logger.info(f'\033[92m[_ensure_conversation_files_indexed] Agentic RAG collection already exists for conversation: {conversation_id}\033[0m')
				return

			# Get files to index
			logger.info(f'\033[96m[_ensure_conversation_files_indexed] Getting files for Agentic RAG indexing\033[0m')
			files_data = await LangGraphService._file_repo.get_files_for_indexing(conversation_id)

			if not files_data:
				logger.info(f'\033[93m[_ensure_conversation_files_indexed] No files to index for conversation: {conversation_id}\033[0m')
				return

			# Index files via Agentic RAG
			logger.info(f'\033[95m[_ensure_conversation_files_indexed] Starting Agentic RAG indexing {len(files_data)} files for conversation: {conversation_id}\033[0m')
			result = await LangGraphService._file_indexing_service.index_conversation_files(conversation_id, files_data)

			# Mark files as indexed in database
			if result['successful_file_ids']:
				logger.info(f'\033[96m[_ensure_conversation_files_indexed] Marking {len(result["successful_file_ids"])} files as indexed\033[0m')
				LangGraphService._file_repo.bulk_mark_files_as_indexed(result['successful_file_ids'], success=True)

			logger.info(f'\033[92m[_ensure_conversation_files_indexed] Agentic RAG file indexing completed for conversation {conversation_id}: {result["successful_files"]}/{result["total_files"]} files indexed\033[0m')

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

		logger.info('\033[96m[_prepare_messages] Preparing messages for workflow execution\033[0m')
		messages = []

		# Add system prompt
		if system_prompt:
			logger.info('\033[95m[_prepare_messages] Adding system prompt to messages\033[0m')
			messages.append(SystemMessage(content=system_prompt))

		# Add conversation history
		if conversation_history:
			logger.info(f'\033[94m[_prepare_messages] Adding {len(conversation_history)} history messages\033[0m')
			for msg in conversation_history:
				if msg.get('role') == 'user':
					messages.append(HumanMessage(content=msg['content']))
				elif msg.get('role') == 'assistant':
					messages.append(AIMessage(content=msg['content']))

		# Add current user message
		logger.info('\033[96m[_prepare_messages] Adding current user message\033[0m')
		messages.append(HumanMessage(content=user_message))

		logger.info(f'\033[92m[_prepare_messages] Prepared {len(messages)} messages for workflow\033[0m')
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
			logger.info(f'\033[94m[execute_conversation] Starting conversation execution with Agentic RAG for: {conversation_id}\033[0m')

			# Note: Files are now indexed automatically on upload via events to Agentic RAG
			logger.info(f'\033[95m[execute_conversation] Files should already be indexed via upload events to Agentic RAG\033[0m')

			# Prepare system prompt
			system_prompt = conversation_system_prompt or agent.default_system_prompt
			logger.info(f'\033[96m[execute_conversation] Using system prompt: {"custom" if conversation_system_prompt else "default"}\033[0m')

			# Prepare messages
			logger.info(f'\033[94m[execute_conversation] Preparing messages for workflow\033[0m')
			messages = self._prepare_messages(system_prompt, user_message, conversation_history or [])

			# Execute workflow - use ainvoke instead of astream to avoid __end__ issues
			config = {
				'configurable': {
					'thread_id': conversation_id,
					'system_prompt': system_prompt,
				}
			}

			workflow_input = {'messages': messages}

			logger.info(f'\033[95m[execute_conversation] Executing workflow with {len(messages)} messages\033[0m')
			# Get result from global workflow (using ainvoke for direct result)
			final_state = await LangGraphService._global_workflow.ainvoke(workflow_input, config)

			# Extract response from final state
			logger.info(f'\033[96m[execute_conversation] Extracting response content from final state\033[0m')
			content = self._extract_response_content(final_state)
			tokens_used = self._get_tokens_used(final_state)

			end_time = time.time()
			response_time = int((end_time - start_time) * 1000)

			logger.info(f'\033[92m[execute_conversation] Conversation execution completed in {response_time}ms, tokens used: {tokens_used}\033[0m')

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
			raise ValidationException(f'Conversation execution failed: {str(e)}')

	def _extract_response_content(self, final_state: Dict[str, Any]) -> str:
		"""Extract the AI response content from workflow final state"""
		try:
			logger.info('\033[96m[_extract_response_content] Extracting response content from final state\033[0m')

			messages = final_state.get('messages', [])
			if not messages:
				logger.warning('\033[93m[_extract_response_content] No messages in final state\033[0m')
				return 'No response generated'

			# Get the last message which should be the AI response
			last_message = messages[-1]
			logger.info(f'\033[95m[_extract_response_content] Last message type: {type(last_message)}\033[0m')

			# Handle different message types
			if hasattr(last_message, 'content'):
				content = last_message.content
			elif isinstance(last_message, dict):
				content = last_message.get('content', 'No content available')
			else:
				content = str(last_message)

			logger.info(f'\033[92m[_extract_response_content] Extracted content length: {len(content)} characters\033[0m')
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
			logger.info(f'\033[94m[search_conversation_context] Searching Agentic RAG context for conversation: {conversation_id}\033[0m')

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

			logger.info(f'\033[92m[search_conversation_context] Found {len(results)} relevant documents via Agentic RAG\033[0m')
			return results

		except Exception as e:
			logger.error(f'\033[91m[search_conversation_context] Error searching conversation context: {str(e)}\033[0m')
			return []

	@classmethod
	def reset_global_cache(cls):
		"""Reset global workflow cache for testing or reinitialization"""
		logger.info('\033[96m[reset_global_cache] Resetting global workflow cache\033[0m')
		cls._global_workflow = None
		cls._file_indexing_service = None
		cls._file_repo = None
		logger.info('\033[92m[reset_global_cache] Global cache reset completed\033[0m')
