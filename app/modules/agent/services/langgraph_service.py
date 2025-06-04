"""
Optimized LangGraph service with global workflow caching and simplified execution.
Uses basic workflow without complex RAG functionality.
"""

import os
from typing import Dict, Any, List, Optional
import logging
import time

from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
from app.modules.agent.models.agent import Agent
from app.modules.agent.services.qdrant_service import QdrantService
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
	"""Optimized LangGraph service with global caching and simplified execution"""

	# Global workflow cache - shared across all instances
	_global_workflow = None
	_qdrant_service = None
	_file_indexing_service = None
	_file_repo = None

	def __init__(self, db: Session):
		logger.info('LangGraphService.__init__ - Initializing optimized service')
		logger.info(f'LangGraphService.__init__ - Using database session: {db}')
		self.db = db
		# Initialize global workflow if not exists
		logger.info('LangGraphService.__init__ - Checking global workflow initialization')
		if LangGraphService._global_workflow is None:
			logger.info('LangGraphService.__init__ - Global workflow not initialized, initializing now')
			LangGraphService._init_global_workflow(db)
		else:
			logger.info('LangGraphService.__init__ - Global workflow already initialized')

		# Initialize shared services
		if LangGraphService._qdrant_service is None:
			LangGraphService._qdrant_service = QdrantService(db)
		if LangGraphService._file_indexing_service is None:
			LangGraphService._file_indexing_service = ConversationFileIndexingService(db)
		if LangGraphService._file_repo is None:
			LangGraphService._file_repo = FileRepo(db)

		logger.info('LangGraphService.__init__ - Service initialized successfully')

	@classmethod
	def _init_global_workflow(cls, db_session: Session):
		"""Initialize global workflow instance once"""
		try:
			from app.modules.agent.workflows.chat_workflow import get_compiled_workflow

			cls._global_workflow = get_compiled_workflow(db_session=db_session, config=WorkflowConfig())
			logger.info('Global workflow initialized successfully')
		except Exception as e:
			logger.error(f'Failed to initialize global workflow: {str(e)}')
			raise ValidationException(f'Workflow initialization failed: {str(e)}')

	async def _ensure_conversation_files_indexed(self, conversation_id: str):
		"""Ensure all files in conversation are indexed in Qdrant"""
		try:
			logger.info(f'[LangGraphService] Checking file indexing for conversation: {conversation_id}')

			# Check if collection already exists
			if LangGraphService._file_indexing_service.check_collection_exists(conversation_id):
				logger.info(f'[LangGraphService] Collection already exists for conversation: {conversation_id}')
				return

			# Get files to index
			files_data = await LangGraphService._file_repo.get_files_for_indexing(conversation_id)

			if not files_data:
				logger.info(f'[LangGraphService] No files to index for conversation: {conversation_id}')
				return

			# Index files
			logger.info(f'[LangGraphService] Starting indexing {len(files_data)} files for conversation: {conversation_id}')
			result = await LangGraphService._file_indexing_service.index_conversation_files(conversation_id, files_data)

			# Mark files as indexed in database
			if result['successful_file_ids']:
				LangGraphService._file_repo.bulk_mark_files_as_indexed(result['successful_file_ids'], success=True)

			logger.info(f'[LangGraphService] File indexing completed for conversation {conversation_id}: {result["successful_files"]}/{result["total_files"]} files indexed')

		except Exception as e:
			logger.error(f'[LangGraphService] Error ensuring files indexed: {str(e)}')
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
		"""Execute conversation using basic workflow"""
		start_time = time.time()

		try:
			# Ensure conversation files are indexed for RAG
			await self._ensure_conversation_files_indexed(conversation_id)

			# Prepare system prompt
			system_prompt = conversation_system_prompt or agent.default_system_prompt

			# Prepare messages
			messages = self._prepare_messages(system_prompt, user_message, conversation_history or [])

			# Execute workflow - use ainvoke instead of astream to avoid __end__ issues
			config = {
				'configurable': {
					'thread_id': conversation_id,
					'system_prompt': system_prompt,
				}
			}

			workflow_input = {'messages': messages}

			# Get result from global workflow (using ainvoke for direct result)
			final_state = await LangGraphService._global_workflow.ainvoke(workflow_input, config)

			# Extract response from final state
			content = self._extract_response_content(final_state)
			tokens_used = self._get_tokens_used(final_state)

			end_time = time.time()
			response_time = int((end_time - start_time) * 1000)

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
			logger.error(f'Error in execute_conversation: {str(e)}')
			raise ValidationException(f'{_("conversation_execution_failed")}: {str(e)}')

	def _extract_response_content(self, final_state: Dict[str, Any]) -> str:
		"""Extract response content from final state"""
		try:
			messages = final_state.get('messages', [])
			if not messages:
				return 'Không thể tạo phản hồi.'

			# Get last AI message
			for message in reversed(messages):
				if hasattr(message, 'content') and message.content:
					content = message.content
					if content and content.strip():
						return content

			return 'Phản hồi không khả dụng.'
		except Exception as e:
			logger.error(f'Error extracting response content: {str(e)}')
			return 'Lỗi khi trích xuất phản hồi.'

	def _get_tokens_used(self, final_state: Dict[str, Any]) -> int:
		"""Extract tokens used from final state"""
		try:
			messages = final_state.get('messages', [])
			if messages:
				last_message = messages[-1]
				if hasattr(last_message, 'usage_metadata'):
					return getattr(last_message, 'usage_metadata', {}).get('total_tokens', 0)
			return 0
		except Exception as e:
			logger.error(f'Error extracting tokens used: {str(e)}')
			return 0

	# File indexing and search methods
	def search_conversation_context(self, conversation_id: str, query: str, top_k: int = 5) -> List[Dict]:
		"""Search for context in conversation files"""
		try:
			documents = LangGraphService._file_indexing_service.search_conversation_context(conversation_id, query, top_k)

			# Format results for workflow
			results = []
			for doc in documents:
				result = {
					'content': doc.page_content,
					'metadata': doc.metadata,
					'similarity_score': doc.metadata.get('similarity_score', 0),
				}
				results.append(result)

			return results

		except Exception as e:
			logger.error(f'Error searching conversation context: {str(e)}')
			return []

	# QdrantDB methods - delegate to shared service
	def search_documents(self, query: str, collection_name: str = 'default_collection', top_k: int = 5) -> List[Dict]:
		"""Search documents in QdrantDB"""
		return LangGraphService._qdrant_service.search_documents(query, collection_name, top_k)

	def index_documents(self, documents: List[Dict], collection_name: str = 'default_collection') -> Dict[str, Any]:
		"""Index documents to QdrantDB"""
		return LangGraphService._qdrant_service.index_documents(documents, collection_name)

	def get_collection_stats(self, collection_name: str = 'default_collection') -> Dict[str, Any]:
		"""Get collection statistics from QdrantDB"""
		return LangGraphService._qdrant_service.get_collection_stats(collection_name)

	@classmethod
	def reset_global_cache(cls):
		"""Reset global cache - useful for testing"""
		cls._global_workflow = None
		cls._qdrant_service = None
		cls._file_indexing_service = None
		cls._file_repo = None
		logger.info('Global cache reset')
