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
class RAGVectorDAL:
	"""DAL for RAG vector operations với Qdrant"""

	def __init__(self, db: Session):
		self.db = db

		self.kb_repo = KBRepository()

	def create_collection(self, collection_name: str) -> bool:
		"""Create new collection trong Qdrant"""

		try:
			from qdrant_client.http.models import Distance, VectorParams


			self.kb_repo.client.create_collection(
				collection_name=collection_name,
				vectors_config=VectorParams(size=self.kb_repo.vector_size, distance=Distance.COSINE),
			)

			return True
		except Exception as e:
			return False

	def collection_exists(self, collection_name: str) -> bool:
		"""Check if collection exists"""

		try:
			self.kb_repo.client.get_collection(collection_name=collection_name)
			return True
		except Exception:
			return False

	async def add_documents_to_collection(self, collection_name: str, documents: List[DocumentModel]) -> List[str]:
		"""Add documents to specific collection"""

		try:
			# Create conversation-specific KB repo
			conversation_kb_repo = self._get_collection_kb_repo(collection_name)

			# Add documents
			request = AddDocumentsRequest(documents=documents)

			ids = await conversation_kb_repo.add_documents(request)

			return ids
		except Exception as e:
			raise

	async def search_in_collection(self, collection_name: str, query: str, top_k: int = 5) -> QueryResponse:
		"""Search documents trong specific collection"""

		try:
			# Create conversation-specific KB repo
			conversation_kb_repo = self._get_collection_kb_repo(collection_name)

			# Query documents
			request = QueryRequest(query=query, top_k=top_k)

			response = await conversation_kb_repo.query(request)

			return response
		except Exception as e:
			raise

	def delete_collection(self, collection_name: str) -> bool:
		"""Delete collection"""

		try:
			self.kb_repo.client.delete_collection(collection_name=collection_name)
			return True
		except Exception as e:
			return False

	def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
		"""Get collection statistics"""

		try:
			collection_info = self.kb_repo.client.get_collection(collection_name=collection_name)

			stats = {'collection_name': collection_name, 'vectors_count': collection_info.vectors_count, 'points_count': collection_info.points_count, 'status': collection_info.status.value if hasattr(collection_info.status, 'value') else str(collection_info.status), 'exists': True}

			return stats
		except Exception as e:
			return {'collection_name': collection_name, 'error': str(e), 'exists': False, 'vectors_count': 0, 'points_count': 0, 'status': 'error'}

	def delete_documents_from_collection(self, collection_name: str, document_ids: List[str]) -> bool:
		"""Delete specific documents từ collection"""

		try:
			self.kb_repo.client.delete(
				collection_name=collection_name,
				points_selector=document_ids,
			)
			return True
		except Exception as e:
			return False

	def _get_collection_kb_repo(self, collection_name: str) -> KBRepository:
		"""Get KBRepository configured for specific collection"""

		# Create new KB repo instance với custom collection name
		kb_repo = KBRepository()
		kb_repo.collection_name = collection_name

		# Ensure collection exists trước khi tạo vectorstore
		if not self.collection_exists(collection_name):
			self.create_collection(collection_name)

		# Recreate vectorstore với collection name mới
		from langchain_qdrant import QdrantVectorStore

		kb_repo.vectorstore = QdrantVectorStore(
			client=kb_repo.client,
			collection_name=collection_name,
			embedding=kb_repo.embedding,
			metadata_payload_key='metadata',
		)

		return kb_repo

	def list_collections(self) -> List[str]:
		"""List all collections trong Qdrant"""

		try:
			collections = self.kb_repo.client.get_collections()

			collection_names = [col.name for col in collections.collections]

			return collection_names
		except Exception as e:
			return []
