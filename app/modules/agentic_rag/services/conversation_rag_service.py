"""
Service để tích hợp agentic RAG với conversation files.
Kết nối với file indexing system hiện tại.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.modules.agentic_rag.repositories.kb_repo import KBRepository
from app.modules.agentic_rag.schemas.kb_schema import (
	AddDocumentsRequest,
	DocumentModel,
	QueryRequest,
)
from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
from app.middleware.translation_manager import _
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)




class ConversationRAGService:
	"""Service để xử lý RAG cho conversation files"""

	def __init__(self, db: Session):
		self.db = db

		self.kb_repo = KBRepository()

		self.rag_agent = RAGAgentGraph(kb_repo=self.kb_repo)

	def get_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name cho conversation"""
		collection_name = f'conversation_{conversation_id}'
		return collection_name

	async def index_conversation_files(self, conversation_id: str, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""
		Index files vào Qdrant collection cho conversation

		Args:
		        conversation_id: ID của conversation
		        files_data: List files data với format:
		                [{
		                        'file_id': str,
		                        'file_name': str,
		                        'file_type': str,
		                        'file_content': bytes
		                }]

		Returns:
		        Dict với kết quả indexing
		"""

		try:
			collection_name = self.get_collection_name(conversation_id)

			# Prepare documents for indexing
			documents = []
			successful_file_ids = []
			failed_file_details = []


			for i, file_data in enumerate(files_data):

				try:
					# Extract text content from file
					content = self._extract_text_content(
						file_data['file_content'],
						file_data['file_type'],
						file_data['file_name'],
					)

					if not content.strip():
						failed_file_details.append({
							'file_id': file_data['file_id'],
							'error': 'Empty content after extraction',
						})
						continue

					# Create document
					doc = DocumentModel(
						id=file_data['file_id'],
						content=content,
						metadata={
							'file_name': file_data['file_name'],
							'file_type': file_data['file_type'],
							'conversation_id': conversation_id,
							'source': 'file_upload',
						},
					)
					documents.append(doc)
					successful_file_ids.append(file_data['file_id'])


				except Exception as e:
					failed_file_details.append({'file_id': file_data['file_id'], 'error': str(e)})

			# Index documents to Qdrant
			if documents:

				# Tạo KB repo với collection name specific cho conversation
				conversation_kb_repo = self._get_conversation_kb_repo(collection_name)

				request = AddDocumentsRequest(documents=documents)
				indexed_ids = await conversation_kb_repo.add_documents(request)

			else:
				indexed_ids = []

			result = {
				'successful_files': len(successful_file_ids),
				'failed_files': len(failed_file_details),
				'total_files': len(files_data),
				'successful_file_ids': successful_file_ids,
				'failed_file_details': failed_file_details,
				'collection_name': collection_name,
			}

			return result

		except Exception as e:
			raise ValidationException(f'Failed to index conversation files: {str(e)}')

	async def search_conversation_context(self, conversation_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
		"""
		Search context trong conversation files

		Args:
		        conversation_id: ID của conversation
		        query: Query để search
		        top_k: Số lượng kết quả trả về

		Returns:
		        List documents tìm được
		"""

		try:
			collection_name = self.get_collection_name(conversation_id)

			# Check if collection exists
			if not self._check_collection_exists(collection_name):
				return []


			# Get conversation-specific KB repo
			conversation_kb_repo = self._get_conversation_kb_repo(collection_name)

			# Query documents
			request = QueryRequest(query=query, top_k=top_k)
			response = await conversation_kb_repo.query(request)

			# Format results
			results = []
			for i, item in enumerate(response.results):
				result = {
					'content': item.content,
					'metadata': item.metadata or {},
					'similarity_score': item.score or 0.0,
					'file_id': item.id,
				}
				results.append(result)

			return results

		except Exception as e:
			return []

	async def generate_rag_response(self, conversation_id: str, query: str) -> Dict[str, Any]:
		"""
		Generate RAG response cho conversation

		Args:
		        conversation_id: ID của conversation
		        query: User query

		Returns:
		        Dict với answer và sources
		"""

		try:
			collection_name = self.get_collection_name(conversation_id)

			# Check if collection exists
			if not self._check_collection_exists(collection_name):
				return {
					'answer': 'Tôi không có thông tin từ các file đã upload để trả lời câu hỏi này.',
					'sources': [],
					'has_context': False,
				}


			# Use conversation-specific RAG agent
			conversation_rag_agent = self._get_conversation_rag_agent(collection_name)

			# Generate response
			result = await conversation_rag_agent.answer_query(query)

			sources_count = len(result.get('sources', []))
			answer_length = len(result.get('answer', ''))


			for i, source in enumerate(result.get('sources', [])):
				pass

			final_result = {
				'answer': result.get('answer', ''),
				'sources': result.get('sources', []),
				'has_context': bool(result.get('sources')),
			}

			return final_result

		except Exception as e:
			raise ValidationException(f'Failed to generate RAG response: {str(e)}')

	def _extract_text_content(self, file_content: bytes, file_type: str, file_name: str) -> str:
		"""Extract text content từ file based on type"""

		try:
			# Text files
			if file_type.startswith('text/') or file_name.lower().endswith(('.txt', '.md', '.csv')):
				try:
					content = file_content.decode('utf-8')
				except UnicodeDecodeError:
					content = file_content.decode('latin-1')
				return content

			# PDF files
			elif file_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
				content = f'PDF content from {file_name} - Content extraction needs to be implemented'
				return content

			# Office documents
			elif file_type.startswith('application/vnd.openxmlformats') or file_name.lower().endswith(('.docx', '.xlsx', '.pptx')):
				content = f'Office document content from {file_name} - Content extraction needs to be implemented'
				return content

			# Fallback - try to decode as text
			else:
				try:
					content = file_content.decode('utf-8')
					return content
				except UnicodeDecodeError:
					return f'Binary file {file_name} - Cannot extract text content'

		except Exception as e:
			return f'Error extracting content from {file_name}: {str(e)}'

	def _get_conversation_kb_repo(self, collection_name: str) -> KBRepository:
		"""Get KBRepository với collection name specific"""

		# Tạo KB repo mới với collection name khác
		kb_repo = KBRepository()
		kb_repo.collection_name = collection_name

		return kb_repo

	def _get_conversation_rag_agent(self, collection_name: str) -> RAGAgentGraph:
		"""Get RAG agent với conversation-specific KB repo"""

		conversation_kb_repo = self._get_conversation_kb_repo(collection_name)

		rag_agent = RAGAgentGraph(kb_repo=conversation_kb_repo)

		return rag_agent

	def _check_collection_exists(self, collection_name: str) -> bool:
		"""Check if collection exists in Qdrant"""

		try:
			self.kb_repo.client.get_collection(collection_name=collection_name)
			return True
		except Exception:
			return False

	def get_conversation_collection_stats(self, conversation_id: str) -> Dict[str, Any]:
		"""Get statistics cho conversation collection"""

		try:
			collection_name = self.get_collection_name(conversation_id)

			if not self._check_collection_exists(collection_name):
				return {
					'conversation_id': conversation_id,
					'collection_name': collection_name,
					'exists': False,
					'vectors_count': 0,
					'points_count': 0,
					'status': 'not_found',
				}

			# Get collection info
			collection_info = self.kb_repo.client.get_collection(collection_name=collection_name)

			stats = {
				'conversation_id': conversation_id,
				'collection_name': collection_name,
				'exists': True,
				'vectors_count': collection_info.vectors_count,
				'points_count': collection_info.points_count,
				'status': (collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status)),
			}

			return stats

		except Exception as e:
			return {
				'conversation_id': conversation_id,
				'error': str(e),
				'vectors_count': 0,
				'points_count': 0,
				'status': 'error',
			}
