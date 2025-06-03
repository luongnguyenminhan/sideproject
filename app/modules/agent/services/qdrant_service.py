import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
import uuid
import hashlib

logger = logging.getLogger(__name__)


class QdrantService:
	"""Service for handling document indexing and retrieval using QdrantDB"""

	def __init__(self, db: Session):
		self.db = db
		self.client = None
		self.embeddings = None
		self.vector_size = 768  # Google embedding size
		self._initialize_client()

	def _initialize_client(self):
		"""Initialize QdrantDB client and embeddings"""
		try:
			# Use local persistent storage instead of memory
			qdrant_path = os.getenv('QDRANT_PATH', './qdrant_storage')
			qdrant_host = os.getenv('QDRANT_HOST')
			qdrant_port = int(os.getenv('QDRANT_PORT', 6333))

			if qdrant_host:
				# Connect to local Qdrant server
				self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
				logger.info(f'QdrantService - Connected to Qdrant server at {qdrant_host}:{qdrant_port}')
			else:
				# Use local file-based storage
				self.client = QdrantClient(path=qdrant_path)
				logger.info(f'QdrantService - Using local storage at: {qdrant_path}')

			# Initialize embeddings
			self.embeddings = GoogleGenerativeAIEmbeddings(model='models/gemini-embedding-exp-03-07')

			logger.info('QdrantService - Client and embeddings initialized successfully')
		except Exception as e:
			logger.error(f'QdrantService - Failed to initialize client: {str(e)}')
			raise ValidationException(_('qdrant_initialization_failed'))

	def initialize_collection(self, collection_name: str, vector_size: int = None) -> bool:
		"""Initialize collection in QdrantDB"""
		try:
			if vector_size:
				self.vector_size = vector_size

			# Check if collection exists
			collections = self.client.get_collections()
			existing_names = [col.name for col in collections.collections]

			if collection_name not in existing_names:
				self.client.create_collection(
					collection_name=collection_name,
					vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
				)
				logger.info(f"QdrantService - Collection '{collection_name}' created successfully")
			else:
				logger.info(f"QdrantService - Collection '{collection_name}' already exists")

			return True
		except Exception as e:
			logger.error(f'QdrantService - Failed to initialize collection: {str(e)}')
			raise ValidationException(_('collection_initialization_failed'))

	def _generate_document_id(self, content: str) -> str:
		"""Generate unique ID for document based on content"""
		content_hash = hashlib.md5(content.encode()).hexdigest()
		return str(uuid.UUID(content_hash))

	def index_documents(self, documents: List[Document], collection_name: str, batch_size: int = 50) -> Dict[str, Any]:
		"""Index documents into QdrantDB collection"""
		try:
			# Ensure collection exists
			self.initialize_collection(collection_name)

			# Text splitter for large documents
			text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)

			# Split documents into chunks
			doc_chunks = []
			for doc in documents:
				chunks = text_splitter.split_documents([doc])
				doc_chunks.extend(chunks)

			logger.info(f'QdrantService - Split {len(documents)} documents into {len(doc_chunks)} chunks')

			# Process documents in batches
			total_indexed = 0
			for i in range(0, len(doc_chunks), batch_size):
				batch = doc_chunks[i : i + batch_size]

				# Generate embeddings for batch
				texts = [chunk.page_content for chunk in batch]
				embeddings = self.embeddings.embed_documents(texts)

				# Create points for QdrantDB
				points = []
				for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
					doc_id = self._generate_document_id(chunk.page_content)

					point = PointStruct(
						id=doc_id,
						vector=embedding,
						payload={
							'content': chunk.page_content,
							'metadata': chunk.metadata,
							'chunk_index': i + j,
						},
					)
					points.append(point)

				# Upsert points to collection
				self.client.upsert(collection_name=collection_name, points=points)

				total_indexed += len(points)
				logger.info(f'QdrantService - Indexed batch {i // batch_size + 1}, total: {total_indexed}')

			return {
				'total_documents': len(documents),
				'total_chunks': len(doc_chunks),
				'total_indexed': total_indexed,
				'collection': collection_name,
			}

		except Exception as e:
			logger.error(f'QdrantService - Failed to index documents: {str(e)}')
			raise ValidationException(_('document_indexing_failed'))

	def similarity_search(
		self,
		query: str,
		collection_name: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""Perform similarity search in QdrantDB collection"""
		try:
			# Generate query embedding
			query_embedding = self.embeddings.embed_query(query)

			# Search in QdrantDB
			search_result = self.client.search(
				collection_name=collection_name,
				query_vector=query_embedding,
				limit=top_k,
				score_threshold=score_threshold,
			)

			# Convert results to Document objects
			documents = []
			for result in search_result:
				doc = Document(
					page_content=result.payload['content'],
					metadata={
						**result.payload['metadata'],
						'similarity_score': result.score,
						'chunk_index': result.payload.get('chunk_index'),
					},
				)
				documents.append(doc)

			logger.info(f'QdrantService - Found {len(documents)} similar documents for query')
			return documents

		except Exception as e:
			logger.error(f'QdrantService - Failed to perform similarity search: {str(e)}')
			raise ValidationException(_('similarity_search_failed'))

	def delete_documents(self, collection_name: str, document_ids: List[str] = None) -> bool:
		"""Delete documents from collection"""
		try:
			if document_ids:
				# Delete specific documents
				self.client.delete(
					collection_name=collection_name,
					points_selector=models.PointIdsList(points=document_ids),
				)
				logger.info(f'QdrantService - Deleted {len(document_ids)} documents')
			else:
				# Delete entire collection
				self.client.delete_collection(collection_name=collection_name)
				logger.info(f"QdrantService - Deleted collection '{collection_name}'")

			return True

		except Exception as e:
			logger.error(f'QdrantService - Failed to delete documents: {str(e)}')
			raise ValidationException(_('document_deletion_failed'))

	def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
		"""Get collection statistics"""
		try:
			collection_info = self.client.get_collection(collection_name=collection_name)

			return {
				'name': collection_name,
				'vectors_count': collection_info.vectors_count,
				'indexed_vectors_count': collection_info.indexed_vectors_count,
				'points_count': collection_info.points_count,
				'segments_count': collection_info.segments_count,
				'status': collection_info.status,
			}

		except Exception as e:
			logger.error(f'QdrantService - Failed to get collection stats: {str(e)}')
			raise ValidationException(_('collection_stats_failed'))

	def list_collections(self) -> List[str]:
		"""List all available collections"""
		try:
			collections = self.client.get_collections()
			return [col.name for col in collections.collections]
		except Exception as e:
			logger.error(f'QdrantService - Failed to list collections: {str(e)}')
			raise ValidationException(_('list_collections_failed'))
