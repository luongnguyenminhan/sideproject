"""
File indexing events - Handle real-time file indexing when files are uploaded
"""

import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.modules.agent.services.file_indexing_service import (
	ConversationFileIndexingService,
)
from app.modules.agentic_rag.services.conversation_rag_service import ConversationRAGService
from app.modules.chat.repository.file_repo import FileRepo
from app.modules.chat.models.file import File

logger = logging.getLogger(__name__)


class FileIndexingEventHandler:
	"""Event handler cho file indexing khi upload"""

	def __init__(self, db: Session):
		self.db = db
		self.file_indexing_service = ConversationFileIndexingService(db)
		self.conversation_rag_service = ConversationRAGService(db)  # Add agentic RAG service
		self.file_repo = FileRepo(db)

	async def handle_file_uploaded(self, file_id: str, conversation_id: str, user_id: str) -> Dict[str, Any]:
		"""
		Handle event khi có file được upload - index ngay lập tức

		Args:
		    file_id: ID của file vừa upload
		    conversation_id: ID của conversation
		    user_id: ID của user

		Returns:
		    Dict chứa kết quả indexing
		"""
		try:
			logger.info(f'\033[94m[FileIndexingEventHandler] Processing file upload event: {file_id} in conversation: {conversation_id}\033[0m')

			# Get file data cho indexing
			try:
				file_content = await self.file_repo.get_file_content(file_id, user_id)
				file = self.file_repo.get_file_by_id(file_id, user_id)

				files_data = [
					{
						'file_id': file.id,
						'file_name': file.original_name,
						'file_type': file.type,
						'file_content': file_content,
					}
				]

				logger.info(f'\033[96m[FileIndexingEventHandler] Prepared file data for indexing: {file.original_name} ({len(file_content)} bytes)\033[0m')

			except Exception as e:
				logger.error(f'\033[91m[FileIndexingEventHandler] Error preparing file data: {str(e)}\033[0m')
				return {
					'success': False,
					'error': f'Failed to prepare file data: {str(e)}',
					'file_id': file_id,
				}

			# Index file vào cả legacy service và agentic RAG
			try:
				logger.info(f'\033[95m[FileIndexingEventHandler] Starting indexing for file: {file_id}\033[0m')

				# Index vào legacy Qdrant service (giữ lại để backward compatibility)
				legacy_result = await self.file_indexing_service.index_conversation_files(conversation_id, files_data)

				# Index vào agentic RAG service với local Qdrant
				logger.info(f'\033[96m[FileIndexingEventHandler] Starting agentic RAG indexing for file: {file_id}\033[0m')
				rag_result = await self.conversation_rag_service.index_conversation_files(conversation_id, files_data)

				# Combine results (prioritize agentic RAG result)
				result = rag_result if rag_result['successful_files'] > 0 else legacy_result

				# Mark file as indexed
				if result['successful_file_ids']:
					self.file_repo.bulk_mark_files_as_indexed(result['successful_file_ids'], success=True)
					logger.info(f'\033[92m[FileIndexingEventHandler] File marked as indexed: {file_id}\033[0m')

				# Mark failed files
				if result['failed_file_details']:
					failed_file_ids = [f['file_id'] for f in result['failed_file_details']]
					for failed_id in failed_file_ids:
						error_msg = next(
							(f['error'] for f in result['failed_file_details'] if f['file_id'] == failed_id),
							'Unknown error',
						)
						self.file_repo.mark_file_as_indexed(failed_id, success=False, error_message=error_msg)

				logger.info(f'\033[92m[FileIndexingEventHandler] File indexing completed: {result["successful_files"]}/{result["total_files"]} files indexed\033[0m')

				return {
					'success': True,
					'result': result,
					'file_id': file_id,
					'conversation_id': conversation_id,
				}

			except Exception as e:
				logger.error(f'\033[91m[FileIndexingEventHandler] Error indexing file: {str(e)}\033[0m')
				# Mark file as failed indexing
				self.file_repo.mark_file_as_indexed(file_id, success=False, error_message=str(e))

				return {
					'success': False,
					'error': f'Indexing failed: {str(e)}',
					'file_id': file_id,
				}

		except Exception as e:
			logger.error(f'\033[91m[FileIndexingEventHandler] Error handling file upload event: {str(e)}\033[0m')
			return {
				'success': False,
				'error': f'Event handling failed: {str(e)}',
				'file_id': file_id,
			}

	async def handle_multiple_files_uploaded(self, file_ids: List[str], conversation_id: str, user_id: str) -> Dict[str, Any]:
		"""
		Handle event khi có nhiều files được upload cùng lúc

		Args:
		    file_ids: List IDs của files vừa upload
		    conversation_id: ID của conversation
		    user_id: ID của user

		Returns:
		    Dict chứa kết quả indexing tổng hợp
		"""
		try:
			logger.info(f'\033[94m[FileIndexingEventHandler] Processing multiple files upload event: {len(file_ids)} files in conversation: {conversation_id}\033[0m')

			# Prepare all files data
			files_data = []
			failed_files = []

			for file_id in file_ids:
				try:
					file_content = await self.file_repo.get_file_content(file_id, user_id)
					file = self.file_repo.get_file_by_id(file_id, user_id)

					file_data = {
						'file_id': file.id,
						'file_name': file.original_name,
						'file_type': file.type,
						'file_content': file_content,
					}
					files_data.append(file_data)
					logger.info(f'\033[96m[FileIndexingEventHandler] Prepared file: {file.original_name} ({len(file_content)} bytes)\033[0m')

				except Exception as e:
					logger.error(f'\033[91m[FileIndexingEventHandler] Error preparing file {file_id}: {str(e)}\033[0m')
					failed_files.append({'file_id': file_id, 'error': str(e)})

			if not files_data:
				logger.warning(f'\033[93m[FileIndexingEventHandler] No files to index\033[0m')
				return {
					'success': False,
					'error': 'No files could be prepared for indexing',
					'failed_files': failed_files,
				}

			# Index all files at once (both legacy and agentic RAG)
			try:
				logger.info(f'\033[95m[FileIndexingEventHandler] Starting batch indexing for {len(files_data)} files\033[0m')

				# Index vào legacy service
				legacy_result = await self.file_indexing_service.index_conversation_files(conversation_id, files_data)

				# Index vào agentic RAG service
				logger.info(f'\033[96m[FileIndexingEventHandler] Starting agentic RAG batch indexing\033[0m')
				rag_result = await self.conversation_rag_service.index_conversation_files(conversation_id, files_data)

				# Combine results
				result = rag_result if rag_result['successful_files'] > 0 else legacy_result

				# Mark files as indexed
				if result['successful_file_ids']:
					self.file_repo.bulk_mark_files_as_indexed(result['successful_file_ids'], success=True)
					logger.info(f'\033[92m[FileIndexingEventHandler] {len(result["successful_file_ids"])} files marked as indexed\033[0m')

				# Mark failed files
				if result['failed_file_details']:
					for failed_detail in result['failed_file_details']:
						self.file_repo.mark_file_as_indexed(
							failed_detail['file_id'],
							success=False,
							error_message=failed_detail['error'],
						)

				logger.info(f'\033[92m[FileIndexingEventHandler] Batch file indexing completed: {result["successful_files"]}/{result["total_files"]} files indexed\033[0m')

				return {
					'success': True,
					'result': result,
					'file_ids': file_ids,
					'conversation_id': conversation_id,
					'preparation_failed': failed_files,
				}

			except Exception as e:
				logger.error(f'\033[91m[FileIndexingEventHandler] Error in batch indexing: {str(e)}\033[0m')
				# Mark all files as failed
				for file_id in file_ids:
					self.file_repo.mark_file_as_indexed(file_id, success=False, error_message=str(e))

				return {
					'success': False,
					'error': f'Batch indexing failed: {str(e)}',
					'file_ids': file_ids,
				}

		except Exception as e:
			logger.error(f'\033[91m[FileIndexingEventHandler] Error handling multiple files upload event: {str(e)}\033[0m')
			return {
				'success': False,
				'error': f'Event handling failed: {str(e)}',
				'file_ids': file_ids,
			}

	def get_conversation_collection_stats(self, conversation_id: str) -> Dict[str, Any]:
		"""Get statistics của conversation collection (both legacy and agentic RAG)"""
		try:
			logger.info(f'\033[96m[FileIndexingEventHandler] Getting stats for conversation: {conversation_id}\033[0m')

			# Get stats from both services
			legacy_stats = self.file_indexing_service.get_conversation_collection_stats(conversation_id)
			rag_stats = self.conversation_rag_service.get_conversation_collection_stats(conversation_id)

			return {'conversation_id': conversation_id, 'legacy_service': legacy_stats, 'agentic_rag_service': rag_stats, 'primary_service': 'agentic_rag'}

		except Exception as e:
			logger.error(f'\033[91m[FileIndexingEventHandler] Error getting collection stats: {str(e)}\033[0m')
			return {
				'error': str(e),
				'conversation_id': conversation_id,
				'vectors_count': 0,
				'points_count': 0,
				'status': 'error',
			}


# Singleton instance
file_indexing_event_handler = None


def get_file_indexing_event_handler(db: Session) -> FileIndexingEventHandler:
	"""Get singleton instance của FileIndexingEventHandler"""
	global file_indexing_event_handler
	if file_indexing_event_handler is None:
		file_indexing_event_handler = FileIndexingEventHandler(db)
	return file_indexing_event_handler
