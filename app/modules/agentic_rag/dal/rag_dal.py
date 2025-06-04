"""
DAL layer cho agentic RAG operations với local Qdrant
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.agentic_rag.repositories.kb_repo import KBRepository
from app.modules.agentic_rag.schemas.kb_schema import AddDocumentsRequest, DocumentModel, QueryRequest, QueryResponse

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


class RAGVectorDAL:
	"""DAL for RAG vector operations với Qdrant"""

	def __init__(self, db: Session):
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Initializing RAG Vector Data Access Layer{LogColors.ENDC}')
		self.db = db
		logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Database session established{LogColors.ENDC}')

		self.kb_repo = KBRepository()
		logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] KBRepository initialized with local Qdrant{LogColors.ENDC}')

	def create_collection(self, collection_name: str) -> bool:
		"""Create new collection trong Qdrant"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Creating new collection: {collection_name}{LogColors.ENDC}')

		try:
			from qdrant_client.http.models import Distance, VectorParams

			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Configuring collection with vector size: {self.kb_repo.vector_size}, distance: COSINE{LogColors.ENDC}')

			self.kb_repo.client.create_collection(
				collection_name=collection_name,
				vectors_config=VectorParams(size=self.kb_repo.vector_size, distance=Distance.COSINE),
			)

			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Collection created successfully: {collection_name}{LogColors.ENDC}')
			return True
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error creating collection {collection_name}: {str(e)}{LogColors.ENDC}')
			return False

	def collection_exists(self, collection_name: str) -> bool:
		"""Check if collection exists"""
		logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Checking existence of collection: {collection_name}{LogColors.ENDC}')

		try:
			self.kb_repo.client.get_collection(collection_name=collection_name)
			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Collection exists: {collection_name}{LogColors.ENDC}')
			return True
		except Exception:
			logger.info(f'{LogColors.WARNING}[RAGVectorDAL] Collection does not exist: {collection_name}{LogColors.ENDC}')
			return False

	async def add_documents_to_collection(self, collection_name: str, documents: List[DocumentModel]) -> List[str]:
		"""Add documents to specific collection"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Adding {len(documents)} documents to collection: {collection_name}{LogColors.ENDC}')

		try:
			# Create conversation-specific KB repo
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Creating collection-specific KB repository{LogColors.ENDC}')
			conversation_kb_repo = self._get_collection_kb_repo(collection_name)
			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Collection-specific KB repository created{LogColors.ENDC}')

			# Add documents
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Preparing documents request for addition{LogColors.ENDC}')
			request = AddDocumentsRequest(documents=documents)

			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Executing document addition to vectorstore{LogColors.ENDC}')
			ids = await conversation_kb_repo.add_documents(request)

			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Successfully added {len(ids)} documents to collection: {collection_name}{LogColors.ENDC}')
			return ids
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error adding documents to {collection_name}: {str(e)}{LogColors.ENDC}')
			raise

	async def search_in_collection(self, collection_name: str, query: str, top_k: int = 5) -> QueryResponse:
		"""Search documents trong specific collection"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Searching in collection: {collection_name} with query: "{query[:50]}..." (Top K: {top_k}){LogColors.ENDC}')

		try:
			# Create conversation-specific KB repo
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Creating collection-specific KB repository for search{LogColors.ENDC}')
			conversation_kb_repo = self._get_collection_kb_repo(collection_name)
			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Collection-specific KB repository created for search{LogColors.ENDC}')

			# Query documents
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Preparing query request{LogColors.ENDC}')
			request = QueryRequest(query=query, top_k=top_k)

			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Executing search in vectorstore{LogColors.ENDC}')
			response = await conversation_kb_repo.query(request)

			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Search completed - Found {len(response.results)} results in collection: {collection_name}{LogColors.ENDC}')
			return response
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error searching in {collection_name}: {str(e)}{LogColors.ENDC}')
			raise

	def delete_collection(self, collection_name: str) -> bool:
		"""Delete collection"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Deleting collection: {collection_name}{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Executing collection deletion in Qdrant{LogColors.ENDC}')
			self.kb_repo.client.delete_collection(collection_name=collection_name)
			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Collection deleted successfully: {collection_name}{LogColors.ENDC}')
			return True
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error deleting collection {collection_name}: {str(e)}{LogColors.ENDC}')
			return False

	def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
		"""Get collection statistics"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Getting statistics for collection: {collection_name}{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Retrieving collection information from Qdrant{LogColors.ENDC}')
			collection_info = self.kb_repo.client.get_collection(collection_name=collection_name)

			stats = {'collection_name': collection_name, 'vectors_count': collection_info.vectors_count, 'points_count': collection_info.points_count, 'status': collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status), 'exists': True}

			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Statistics retrieved for collection: {collection_name} - Vectors: {stats["vectors_count"]}, Points: {stats["points_count"]}, Status: {stats["status"]}{LogColors.ENDC}')
			return stats
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error getting stats for {collection_name}: {str(e)}{LogColors.ENDC}')
			return {'collection_name': collection_name, 'error': str(e), 'exists': False, 'vectors_count': 0, 'points_count': 0, 'status': 'error'}

	def delete_documents_from_collection(self, collection_name: str, document_ids: List[str]) -> bool:
		"""Delete specific documents từ collection"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Deleting {len(document_ids)} documents from collection: {collection_name}{LogColors.ENDC}')
		logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Document IDs to delete: {document_ids}{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Executing document deletion in Qdrant{LogColors.ENDC}')
			self.kb_repo.client.delete(
				collection_name=collection_name,
				points_selector=document_ids,
			)
			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Successfully deleted {len(document_ids)} documents from collection: {collection_name}{LogColors.ENDC}')
			return True
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error deleting documents from {collection_name}: {str(e)}{LogColors.ENDC}')
			return False

	def _get_collection_kb_repo(self, collection_name: str) -> KBRepository:
		"""Get KBRepository configured for specific collection"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Creating KBRepository for collection: {collection_name}{LogColors.ENDC}')

		# Create new KB repo instance với custom collection name
		logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Initializing new KBRepository instance{LogColors.ENDC}')
		kb_repo = KBRepository()
		kb_repo.collection_name = collection_name
		logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Updated collection name to: {collection_name}{LogColors.ENDC}')

		# Ensure collection exists trước khi tạo vectorstore
		if not self.collection_exists(collection_name):
			logger.info(f'{LogColors.WARNING}[RAGVectorDAL] Collection does not exist, creating: {collection_name}{LogColors.ENDC}')
			self.create_collection(collection_name)

		# Recreate vectorstore với collection name mới
		logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Recreating vectorstore for collection: {collection_name}{LogColors.ENDC}')
		from langchain_qdrant import QdrantVectorStore

		kb_repo.vectorstore = QdrantVectorStore(
			client=kb_repo.client,
			collection_name=collection_name,
			embedding=kb_repo.embedding,
			metadata_payload_key='metadata',
		)

		logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] KBRepository configured successfully for collection: {collection_name}{LogColors.ENDC}')
		return kb_repo

	def list_collections(self) -> List[str]:
		"""List all collections trong Qdrant"""
		logger.info(f'{LogColors.HEADER}[RAGVectorDAL] Listing all collections in Qdrant{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKBLUE}[RAGVectorDAL] Retrieving collections from Qdrant client{LogColors.ENDC}')
			collections = self.kb_repo.client.get_collections()

			collection_names = [col.name for col in collections.collections]
			logger.info(f'{LogColors.OKCYAN}[RAGVectorDAL] Retrieved collection names: {collection_names}{LogColors.ENDC}')

			logger.info(f'{LogColors.OKGREEN}[RAGVectorDAL] Collection listing completed - Found {len(collection_names)} collections{LogColors.ENDC}')
			return collection_names
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGVectorDAL] Error listing collections: {str(e)}{LogColors.ENDC}')
			return []
