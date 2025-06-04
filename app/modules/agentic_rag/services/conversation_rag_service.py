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


# Color codes for logging
class LogColors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'


class ConversationRAGService:
	"""Service để xử lý RAG cho conversation files"""

	def __init__(self, db: Session):
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Initializing service{LogColors.ENDC}')
		self.db = db
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Database session established{LogColors.ENDC}')

		self.kb_repo = KBRepository()
		logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] KBRepository initialized{LogColors.ENDC}')

		self.rag_agent = RAGAgentGraph(kb_repo=self.kb_repo)
		logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] RAGAgentGraph initialized with local Qdrant{LogColors.ENDC}')

	def get_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name cho conversation"""
		collection_name = f'conversation_{conversation_id}'
		logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Generated collection name: {collection_name} for conversation: {conversation_id}{LogColors.ENDC}')
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
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Starting indexing process for conversation: {conversation_id} with {len(files_data)} files{LogColors.ENDC}')

		try:
			collection_name = self.get_collection_name(conversation_id)
			logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Using collection: {collection_name}{LogColors.ENDC}')

			# Prepare documents for indexing
			documents = []
			successful_file_ids = []
			failed_file_details = []

			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Processing {len(files_data)} files for content extraction{LogColors.ENDC}')

			for i, file_data in enumerate(files_data):
				logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Processing file {i + 1}/{len(files_data)}: {file_data["file_name"]} (Type: {file_data["file_type"]}){LogColors.ENDC}')

				try:
					# Extract text content from file
					content = self._extract_text_content(
						file_data['file_content'],
						file_data['file_type'],
						file_data['file_name'],
					)

					if not content.strip():
						logger.info(f'{LogColors.WARNING}[ConversationRAGService] Empty content detected for file: {file_data["file_name"]}{LogColors.ENDC}')
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

					logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Successfully prepared document for file: {file_data["file_name"]} (Content length: {len(content)} chars){LogColors.ENDC}')

				except Exception as e:
					logger.info(f'{LogColors.FAIL}[ConversationRAGService] Failed to prepare file {file_data["file_name"]}: {str(e)}{LogColors.ENDC}')
					failed_file_details.append({'file_id': file_data['file_id'], 'error': str(e)})

			# Index documents to Qdrant
			if documents:
				logger.info(f'{LogColors.HEADER}[ConversationRAGService] Adding {len(documents)} documents to collection: {collection_name}{LogColors.ENDC}')

				# Tạo KB repo với collection name specific cho conversation
				conversation_kb_repo = self._get_conversation_kb_repo(collection_name)
				logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Created conversation-specific KB repository{LogColors.ENDC}')

				request = AddDocumentsRequest(documents=documents)
				indexed_ids = await conversation_kb_repo.add_documents(request)

				logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Successfully indexed {len(indexed_ids)} documents to Qdrant{LogColors.ENDC}')
			else:
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] No documents to index - all files failed processing{LogColors.ENDC}')

			result = {
				'successful_files': len(successful_file_ids),
				'failed_files': len(failed_file_details),
				'total_files': len(files_data),
				'successful_file_ids': successful_file_ids,
				'failed_file_details': failed_file_details,
				'collection_name': collection_name,
			}

			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Indexing completed - Success: {result["successful_files"]}, Failed: {result["failed_files"]}, Total: {result["total_files"]}{LogColors.ENDC}')
			return result

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[ConversationRAGService] Critical error during indexing conversation files: {str(e)}{LogColors.ENDC}')
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
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Starting context search for conversation: {conversation_id}{LogColors.ENDC}')
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Query: "{query[:100]}..." (truncated), Top K: {top_k}{LogColors.ENDC}')

		try:
			collection_name = self.get_collection_name(conversation_id)
			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Using collection: {collection_name}{LogColors.ENDC}')

			# Check if collection exists
			if not self._check_collection_exists(collection_name):
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] Collection not found: {collection_name} - returning empty results{LogColors.ENDC}')
				return []

			logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Collection exists, proceeding with search{LogColors.ENDC}')

			# Get conversation-specific KB repo
			conversation_kb_repo = self._get_conversation_kb_repo(collection_name)
			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Created conversation-specific KB repository for search{LogColors.ENDC}')

			# Query documents
			request = QueryRequest(query=query, top_k=top_k)
			response = await conversation_kb_repo.query(request)
			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Query executed, found {len(response.results)} raw results{LogColors.ENDC}')

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
				logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Formatted result {i + 1}: File ID: {item.id}, Score: {item.score or 0.0:.4f}, Content length: {len(item.content)} chars{LogColors.ENDC}')

			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Context search completed - Found {len(results)} context documents{LogColors.ENDC}')
			return results

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[ConversationRAGService] Error during context search: {str(e)}{LogColors.ENDC}')
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
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Starting RAG response generation for conversation: {conversation_id}{LogColors.ENDC}')
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] User query: "{query[:100]}..." (truncated){LogColors.ENDC}')

		try:
			collection_name = self.get_collection_name(conversation_id)
			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Using collection: {collection_name}{LogColors.ENDC}')

			# Check if collection exists
			if not self._check_collection_exists(collection_name):
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] No indexed files for conversation: {conversation_id} - returning fallback response{LogColors.ENDC}')
				return {
					'answer': 'Tôi không có thông tin từ các file đã upload để trả lời câu hỏi này.',
					'sources': [],
					'has_context': False,
				}

			logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Collection exists, proceeding with RAG generation{LogColors.ENDC}')

			# Use conversation-specific RAG agent
			conversation_rag_agent = self._get_conversation_rag_agent(collection_name)
			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Created conversation-specific RAG agent{LogColors.ENDC}')

			# Generate response
			logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Invoking RAG agent for answer generation{LogColors.ENDC}')
			result = await conversation_rag_agent.answer_query(query)

			sources_count = len(result.get('sources', []))
			answer_length = len(result.get('answer', ''))

			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] RAG response generated successfully - Answer length: {answer_length} chars, Sources: {sources_count}{LogColors.ENDC}')

			for i, source in enumerate(result.get('sources', [])):
				logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Source {i + 1}: ID: {source.get("id", "unknown")}, Score: {source.get("score", 0):.4f}{LogColors.ENDC}')

			final_result = {
				'answer': result.get('answer', ''),
				'sources': result.get('sources', []),
				'has_context': bool(result.get('sources')),
			}

			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] RAG response preparation completed - Has context: {final_result["has_context"]}{LogColors.ENDC}')
			return final_result

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[ConversationRAGService] Critical error during RAG response generation: {str(e)}{LogColors.ENDC}')
			raise ValidationException(f'Failed to generate RAG response: {str(e)}')

	def _extract_text_content(self, file_content: bytes, file_type: str, file_name: str) -> str:
		"""Extract text content từ file based on type"""
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Starting content extraction from {file_name} (Type: {file_type}, Size: {len(file_content)} bytes){LogColors.ENDC}')

		try:
			# Text files
			if file_type.startswith('text/') or file_name.lower().endswith(('.txt', '.md', '.csv')):
				logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Processing as text file: {file_name}{LogColors.ENDC}')
				try:
					content = file_content.decode('utf-8')
					logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Successfully decoded with UTF-8: {len(content)} characters extracted{LogColors.ENDC}')
				except UnicodeDecodeError:
					logger.info(f'{LogColors.WARNING}[ConversationRAGService] UTF-8 decode failed, trying latin-1 for: {file_name}{LogColors.ENDC}')
					content = file_content.decode('latin-1')
					logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Successfully decoded with latin-1: {len(content)} characters extracted{LogColors.ENDC}')
				return content

			# PDF files
			elif file_type == 'application/pdf' or file_name.lower().endswith('.pdf'):
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] PDF file detected: {file_name} - Using placeholder content (PDF extraction not implemented){LogColors.ENDC}')
				content = f'PDF content from {file_name} - Content extraction needs to be implemented'
				return content

			# Office documents
			elif file_type.startswith('application/vnd.openxmlformats') or file_name.lower().endswith(('.docx', '.xlsx', '.pptx')):
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] Office document detected: {file_name} - Using placeholder content (Office extraction not implemented){LogColors.ENDC}')
				content = f'Office document content from {file_name} - Content extraction needs to be implemented'
				return content

			# Fallback - try to decode as text
			else:
				logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Unknown file type, attempting text extraction fallback for: {file_name}{LogColors.ENDC}')
				try:
					content = file_content.decode('utf-8')
					logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Fallback UTF-8 decode successful: {len(content)} characters extracted{LogColors.ENDC}')
					return content
				except UnicodeDecodeError:
					logger.info(f'{LogColors.WARNING}[ConversationRAGService] Cannot extract text from binary file: {file_name}{LogColors.ENDC}')
					return f'Binary file {file_name} - Cannot extract text content'

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[ConversationRAGService] Content extraction failed for {file_name}: {str(e)}{LogColors.ENDC}')
			return f'Error extracting content from {file_name}: {str(e)}'

	def _get_conversation_kb_repo(self, collection_name: str) -> KBRepository:
		"""Get KBRepository với collection name specific"""
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Creating conversation-specific KB repository for collection: {collection_name}{LogColors.ENDC}')

		# Tạo KB repo mới với collection name khác
		kb_repo = KBRepository()
		kb_repo.collection_name = collection_name
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Base KB repository created, updating collection name{LogColors.ENDC}')

		# Recreate vectorstore với collection mới
		from app.modules.agentic_rag.core.config import settings
		from langchain_qdrant import QdrantVectorStore

		logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Recreating vectorstore with collection: {collection_name}{LogColors.ENDC}')

		kb_repo.vectorstore = QdrantVectorStore(
			client=kb_repo.client,
			collection_name=collection_name,
			embedding=kb_repo.embedding,
			metadata_payload_key='metadata',
		)

		logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Conversation-specific KB repository created successfully{LogColors.ENDC}')
		return kb_repo

	def _get_conversation_rag_agent(self, collection_name: str) -> RAGAgentGraph:
		"""Get RAG agent với conversation-specific KB repo"""
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Creating conversation-specific RAG agent for collection: {collection_name}{LogColors.ENDC}')

		conversation_kb_repo = self._get_conversation_kb_repo(collection_name)
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] KB repository created, initializing RAG agent{LogColors.ENDC}')

		rag_agent = RAGAgentGraph(kb_repo=conversation_kb_repo)
		logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Conversation-specific RAG agent created successfully{LogColors.ENDC}')

		return rag_agent

	def _check_collection_exists(self, collection_name: str) -> bool:
		"""Check if collection exists in Qdrant"""
		logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Checking if collection exists: {collection_name}{LogColors.ENDC}')

		try:
			self.kb_repo.client.get_collection(collection_name=collection_name)
			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Collection exists: {collection_name}{LogColors.ENDC}')
			return True
		except Exception:
			logger.info(f'{LogColors.WARNING}[ConversationRAGService] Collection does not exist: {collection_name}{LogColors.ENDC}')
			return False

	def get_conversation_collection_stats(self, conversation_id: str) -> Dict[str, Any]:
		"""Get statistics cho conversation collection"""
		logger.info(f'{LogColors.HEADER}[ConversationRAGService] Getting collection statistics for conversation: {conversation_id}{LogColors.ENDC}')

		try:
			collection_name = self.get_collection_name(conversation_id)
			logger.info(f'{LogColors.OKBLUE}[ConversationRAGService] Using collection: {collection_name}{LogColors.ENDC}')

			if not self._check_collection_exists(collection_name):
				logger.info(f'{LogColors.WARNING}[ConversationRAGService] Collection not found for stats: {collection_name}{LogColors.ENDC}')
				return {
					'conversation_id': conversation_id,
					'collection_name': collection_name,
					'exists': False,
					'vectors_count': 0,
					'points_count': 0,
					'status': 'not_found',
				}

			# Get collection info
			logger.info(f'{LogColors.OKCYAN}[ConversationRAGService] Retrieving collection information from Qdrant{LogColors.ENDC}')
			collection_info = self.kb_repo.client.get_collection(collection_name=collection_name)

			stats = {
				'conversation_id': conversation_id,
				'collection_name': collection_name,
				'exists': True,
				'vectors_count': collection_info.vectors_count,
				'points_count': collection_info.points_count,
				'status': (collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status)),
			}

			logger.info(f'{LogColors.OKGREEN}[ConversationRAGService] Collection stats retrieved - Vectors: {stats["vectors_count"]}, Points: {stats["points_count"]}, Status: {stats["status"]}{LogColors.ENDC}')
			return stats

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[ConversationRAGService] Error getting collection stats: {str(e)}{LogColors.ENDC}')
			return {
				'conversation_id': conversation_id,
				'error': str(e),
				'vectors_count': 0,
				'points_count': 0,
				'status': 'error',
			}
