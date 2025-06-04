"""
Service for indexing conversation files into Qdrant for RAG functionality
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_core.documents import Document
from datetime import datetime

from app.modules.chat.services.file_extraction_service import file_extraction_service
from app.modules.agent.services.qdrant_service import QdrantService
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _

logger = logging.getLogger(__name__)


class ConversationFileIndexingService:
	"""Service để index files của conversation vào Qdrant"""

	def __init__(self, db: Session):
		self.db = db
		self.qdrant_service = QdrantService(db)

	def get_conversation_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name cho specific conversation"""
		return f'conversation_{conversation_id}'

	async def index_conversation_files(self, conversation_id: str, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""
		Index tất cả files của một conversation vào Qdrant

		Args:
		    conversation_id: ID của conversation
		    files_data: List files với format:
		        [
		            {
		                'file_id': str,
		                'file_name': str,
		                'file_type': str,
		                'file_content': bytes
		            }
		        ]

		Returns:
		    Dict chứa kết quả indexing
		"""
		try:
			logger.info(f'[FileIndexingService] Starting indexing {len(files_data)} files for conversation: {conversation_id}')

			collection_name = self.get_conversation_collection_name(conversation_id)

			# Extract text từ tất cả files
			documents = []
			successful_files = []
			failed_files = []

			for file_data in files_data:
				try:
					# Extract text từ file
					extraction_result = file_extraction_service.extract_text_from_file(
						file_content=file_data['file_content'],
						file_type=file_data['file_type'],
						file_name=file_data['file_name'],
					)

					if extraction_result['extraction_success'] and extraction_result['content'].strip():
						# Tạo document cho Qdrant
						doc = Document(
							page_content=extraction_result['content'],
							metadata={
								'file_id': file_data['file_id'],
								'file_name': file_data['file_name'],
								'file_type': file_data['file_type'],
								'conversation_id': conversation_id,
								'indexed_at': datetime.utcnow().isoformat(),
								'char_count': extraction_result['char_count'],
							},
						)
						documents.append(doc)
						successful_files.append(file_data['file_id'])

						logger.info(f'[FileIndexingService] Extracted {extraction_result["char_count"]} chars from {file_data["file_name"]}')
					else:
						failed_files.append({
							'file_id': file_data['file_id'],
							'error': extraction_result.get('extraction_error', 'No content extracted'),
						})
						logger.warning(f'[FileIndexingService] Failed to extract text from {file_data["file_name"]}')

				except Exception as e:
					logger.error(f'[FileIndexingService] Error processing file {file_data["file_name"]}: {str(e)}')
					failed_files.append({'file_id': file_data['file_id'], 'error': str(e)})

			# Index documents vào Qdrant nếu có
			indexing_result = {}
			if documents:
				indexing_result = self.qdrant_service.index_documents(documents, collection_name)
				logger.info(f'[FileIndexingService] Indexed {len(documents)} documents to collection: {collection_name}')
			else:
				logger.warning(f'[FileIndexingService] No documents to index for conversation: {conversation_id}')

			return {
				'conversation_id': conversation_id,
				'collection_name': collection_name,
				'total_files': len(files_data),
				'successful_files': len(successful_files),
				'failed_files': len(failed_files),
				'successful_file_ids': successful_files,
				'failed_file_details': failed_files,
				'indexing_result': indexing_result,
			}

		except Exception as e:
			logger.error(f'[FileIndexingService] Error indexing conversation files: {str(e)}')
			raise ValidationException(_('conversation_files_indexing_failed'))

	def search_conversation_context(
		self,
		conversation_id: str,
		query: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""
		Search trong files của conversation để lấy context cho RAG

		Args:
		    conversation_id: ID của conversation
		    query: Query để search
		    top_k: Số lượng documents trả về tối đa
		    score_threshold: Threshold cho similarity score

		Returns:
		    List documents liên quan
		"""
		try:
			collection_name = self.get_conversation_collection_name(conversation_id)

			# Search trong collection của conversation
			documents = self.qdrant_service.similarity_search(
				query=query,
				collection_name=collection_name,
				top_k=top_k,
				score_threshold=score_threshold,
			)

			logger.info(f'[FileIndexingService] Found {len(documents)} relevant documents for query in conversation: {conversation_id}')
			return documents

		except Exception as e:
			logger.error(f'[FileIndexingService] Error searching conversation context: {str(e)}')
			# Return empty list instead of raising exception để không break conversation flow
			return []

	def get_conversation_collection_stats(self, conversation_id: str) -> Dict[str, Any]:
		"""Get statistics của conversation collection"""
		try:
			collection_name = self.get_conversation_collection_name(conversation_id)
			return self.qdrant_service.get_collection_stats(collection_name)
		except Exception as e:
			logger.error(f'[FileIndexingService] Error getting collection stats: {str(e)}')
			return {
				'name': collection_name,
				'vectors_count': 0,
				'points_count': 0,
				'status': 'error',
			}

	def delete_conversation_collection(self, conversation_id: str) -> bool:
		"""Delete collection của conversation"""
		try:
			collection_name = self.get_conversation_collection_name(conversation_id)
			return self.qdrant_service.delete_documents(collection_name)
		except Exception as e:
			logger.error(f'[FileIndexingService] Error deleting conversation collection: {str(e)}')
			return False

	def check_collection_exists(self, conversation_id: str) -> bool:
		"""Check xem collection của conversation đã tồn tại chưa"""
		try:
			collection_name = self.get_conversation_collection_name(conversation_id)
			collections = self.qdrant_service.list_collections()
			return collection_name in collections
		except Exception as e:
			logger.error(f'[FileIndexingService] Error checking collection existence: {str(e)}')
			return False
