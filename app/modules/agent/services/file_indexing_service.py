"""
Service for indexing conversation files into Qdrant for RAG functionality via Agentic RAG KBRepository
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_core.documents import Document
from datetime import datetime

from app.modules.chat.services.file_extraction_service import file_extraction_service
from app.modules.agentic_rag.repository.kb_repo import KBRepository
from app.modules.agentic_rag.schemas.kb_schema import (
	AddDocumentsRequest,
	DocumentModel,
	QueryRequest,
)
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _

logger = logging.getLogger(__name__)


class ConversationFileIndexingService:
	"""Service để index files của conversation vào Agentic RAG KBRepository"""

	def __init__(self, db: Session):
		self.db = db

	def get_conversation_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name cho specific conversation"""
		return f'conversation_{conversation_id}'

	async def index_conversation_files(self, conversation_id: str, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""
		Index tất cả files của một conversation vào Agentic RAG KBRepository

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
			collection_id = self.get_conversation_collection_name(conversation_id)

			# Extract text từ tất cả files
			documents_to_add = []
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
						# Tạo document model cho KBRepository với UUID hợp lệ
						doc_id = str(uuid.uuid4())  # Tạo UUID mới cho document
						doc = DocumentModel(
							id=doc_id,
							content=extraction_result['content'],
							metadata={
								'file_id': file_data['file_id'],
								'file_name': file_data['file_name'],
								'file_type': file_data['file_type'],
								'conversation_id': conversation_id,
								'indexed_at': datetime.utcnow().isoformat(),
								'char_count': extraction_result['char_count'],
								'original_file_id': file_data['file_id'],  # Lưu original file_id để reference
							},
						)
						documents_to_add.append(doc)
						successful_files.append(file_data['file_id'])

					else:
						failed_files.append({
							'file_id': file_data['file_id'],
							'error': extraction_result.get('extraction_error', 'No content extracted'),
						})
						logger.warning(f'[FileIndexingService] Failed to extract text from {file_data["file_name"]}')

				except Exception as e:
					logger.error(f'[FileIndexingService] Error processing file {file_data["file_name"]}: {str(e)}')
					failed_files.append({'file_id': file_data['file_id'], 'error': str(e)})

			# Index documents vào Agentic RAG KBRepository nếu có
			indexing_result = {}
			if documents_to_add:
				try:
					# Initialize KBRepository for this collection
					kb_repo = KBRepository()

					# Prepare AddDocumentsRequest
					add_request = AddDocumentsRequest(documents=documents_to_add)

					# Add documents via KBRepository
					document_ids = await kb_repo.add_documents(add_request, collection_id=collection_id)
					indexing_result = {
						'indexed_count': len(document_ids),
						'document_ids': document_ids,
						'collection_id': collection_id,
					}

				except Exception as e:
					logger.error(f'[FileIndexingService] Error indexing documents to Agentic RAG: {str(e)}')
					# Move successful files to failed
					for file_id in successful_files:
						failed_files.append({'file_id': file_id, 'error': f'Indexing failed: {str(e)}'})
					successful_files = []
					indexing_result = {'error': str(e)}
			else:
				logger.warning(f'[FileIndexingService] No documents to index for conversation: {conversation_id}')

			return {
				'conversation_id': conversation_id,
				'collection_name': collection_id,
				'total_files': len(files_data),
				'successful_files': len(successful_files),
				'failed_files': len(failed_files),
				'successful_file_ids': successful_files,
				'failed_file_details': failed_files,
				'indexing_result': indexing_result,
				'indexing_method': 'agentic_rag_kb_repository',
			}

		except Exception as e:
			logger.error(f'[FileIndexingService] Error indexing conversation files via Agentic RAG: {str(e)}')
			raise ValidationException(_('conversation_files_indexing_failed'))

	def search_conversation_context(
		self,
		conversation_id: str,
		query: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""
		Search trong files của conversation để lấy context cho RAG via Agentic RAG KBRepository

		Args:
		    conversation_id: ID của conversation
		    query: Query để search
		    top_k: Số lượng documents trả về tối đa
		    score_threshold: Threshold cho similarity score

		Returns:
		    List documents liên quan
		"""
		try:
			collection_id = self.get_conversation_collection_name(conversation_id)

			# Initialize KBRepository
			kb_repo = KBRepository()

			# Prepare query request
			query_request = QueryRequest(query=query, top_k=top_k)

			# Search trong collection của conversation via KBRepository
			query_response = kb_repo.query(query_request, collection_id=collection_id)

			# Convert QueryResponseItems to Documents
			documents = []
			for item in query_response.results:
				if item.score and item.score >= score_threshold:
					doc = Document(
						page_content=item.content or '',
						metadata=item.metadata or {},
					)
					documents.append(doc)

			return documents

		except Exception as e:
			logger.error(f'[FileIndexingService] Error searching conversation context via Agentic RAG: {str(e)}')
			# Return empty list instead of raising exception để không break conversation flow
			return []

	def get_conversation_collection_stats(self, conversation_id: str) -> Dict[str, Any]:
		"""Get statistics của conversation collection từ Agentic RAG"""
		try:
			collection_id = self.get_conversation_collection_name(conversation_id)

			# Initialize KBRepository
			kb_repo = KBRepository()

			# Get documents from collection
			documents = kb_repo.list_all_documents(collection_id=collection_id)

			return {
				'name': collection_id,
				'documents_count': len(documents),
				'status': 'ready',
				'indexing_method': 'agentic_rag_kb_repository',
			}

		except Exception as e:
			logger.error(f'[FileIndexingService] Error getting Agentic RAG collection stats: {str(e)}')
			return {
				'name': collection_id,
				'documents_count': 0,
				'status': 'error',
				'error': str(e),
			}

	def delete_conversation_collection(self, conversation_id: str) -> bool:
		"""Delete collection của conversation từ Agentic RAG"""
		try:
			collection_id = self.get_conversation_collection_name(conversation_id)

			# Initialize KBRepository
			kb_repo = KBRepository()

			# Get all documents in collection and delete them
			documents = kb_repo.list_all_documents(collection_id=collection_id)

			# Delete each document
			for doc in documents:
				kb_repo.delete_document(doc.id, collection_id=collection_id)

			return True

		except Exception as e:
			logger.error(f'[FileIndexingService] Error deleting Agentic RAG conversation collection: {str(e)}')
			return False

	def check_collection_exists(self, conversation_id: str) -> bool:
		"""Check xem collection của conversation đã tồn tại chưa trong Agentic RAG"""
		try:
			collection_id = self.get_conversation_collection_name(conversation_id)

			# Initialize KBRepository
			kb_repo = KBRepository()

			# Check if collection exists by trying to list documents
			documents = kb_repo.list_all_documents(collection_id=collection_id)
			return True  # If no exception, collection exists

		except Exception as e:
			logger.error(f'[FileIndexingService] Error checking Agentic RAG collection existence: {str(e)}')
			return False
