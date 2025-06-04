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
import time

logger = logging.getLogger(__name__)


class QdrantService:
	"""Service for handling document indexing and retrieval using QdrantDB"""

	def __init__(self, db: Session):
		logger.info('QdrantService - Initializing service instance')
		self.db = db
		self.client = None
		self.embeddings = None
		self.vector_size = 768  # Google embedding size
		logger.info(f'QdrantService - Default vector size set to: {self.vector_size}')
		self._initialize_client()

	def _initialize_client(self):
		"""Initialize QdrantDB client and embeddings"""
		start_time = time.time()
		logger.info('QdrantService - Starting client initialization')

		try:
			# Use local persistent storage instead of memory
			qdrant_path = os.getenv('QDRANT_PATH', './qdrant_storage')
			qdrant_host = os.getenv('QDRANT_HOST')
			qdrant_port = int(os.getenv('QDRANT_PORT', 6333))

			logger.info(f'QdrantService - Configuration: host={qdrant_host}, port={qdrant_port}, path={qdrant_path}')

			if qdrant_host:
				# Connect to local Qdrant server
				logger.info(f'QdrantService - Attempting connection to Qdrant server at {qdrant_host}:{qdrant_port}')
				self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
				logger.info(f'QdrantService - Successfully connected to Qdrant server at {qdrant_host}:{qdrant_port}')
			else:
				# Use local file-based storage
				logger.info(f'QdrantService - Attempting to use local storage at: {qdrant_path}')
				self.client = QdrantClient(path=qdrant_path)
				logger.info(f'QdrantService - Successfully initialized local storage at: {qdrant_path}')

			# Initialize embeddings
			logger.info('QdrantService - Initializing Google Generative AI embeddings')
			self.embeddings = GoogleGenerativeAIEmbeddings(model='models/text-embedding-004')
			logger.info('QdrantService - Google embeddings initialized successfully')

			initialization_time = time.time() - start_time
			logger.info(f'QdrantService - Client and embeddings initialized successfully in {initialization_time:.2f}s')

		except Exception as e:
			initialization_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to initialize client after {initialization_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('qdrant_initialization_failed'))

	def initialize_collection(self, collection_name: str, vector_size: int = None) -> bool:
		"""Initialize collection in QdrantDB"""
		start_time = time.time()
		logger.info(f"QdrantService - Starting collection initialization for: '{collection_name}'")

		try:
			if vector_size:
				old_size = self.vector_size
				self.vector_size = vector_size
				logger.info(f'QdrantService - Vector size changed from {old_size} to {self.vector_size}')

			# Check if collection exists
			logger.info('QdrantService - Fetching existing collections')
			collections = self.client.get_collections()
			existing_names = [col.name for col in collections.collections]
			logger.info(f'QdrantService - Found {len(existing_names)} existing collections: {existing_names}')

			if collection_name not in existing_names:
				logger.info(f"QdrantService - Creating new collection '{collection_name}' with vector size {self.vector_size}")
				self.client.create_collection(
					collection_name=collection_name,
					vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
				)
				creation_time = time.time() - start_time
				logger.info(f"QdrantService - Collection '{collection_name}' created successfully in {creation_time:.2f}s")
			else:
				logger.info(f"QdrantService - Collection '{collection_name}' already exists, skipping creation")

			return True
		except Exception as e:
			initialization_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to initialize collection "{collection_name}" after {initialization_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('collection_initialization_failed'))

	def _generate_document_id(self, content: str) -> str:
		"""Generate unique ID for document based on content"""
		content_length = len(content)
		content_hash = hashlib.md5(content.encode()).hexdigest()
		doc_id = str(uuid.UUID(content_hash))
		logger.info(f'QdrantService - Generated document ID {doc_id[:8]}... for content length {content_length}')
		return doc_id

	def index_documents(self, documents: List[Document], collection_name: str, batch_size: int = 50) -> Dict[str, Any]:
		"""Index documents into QdrantDB collection"""
		start_time = time.time()
		logger.info(f'QdrantService - Starting document indexing: {len(documents)} documents to collection "{collection_name}"')
		logger.info(f'QdrantService - Indexing parameters: batch_size={batch_size}')

		try:
			# Ensure collection exists
			self.initialize_collection(collection_name)

			# Text splitter for large documents
			text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=200, length_function=len)
			logger.info('QdrantService - Text splitter configured: chunk_size=5000, chunk_overlap=200')

			# Split documents into chunks
			logger.info('QdrantService - Starting document chunking process')
			chunk_start_time = time.time()
			doc_chunks = []
			for i, doc in enumerate(documents):
				chunks = text_splitter.split_documents([doc])
				doc_chunks.extend(chunks)
				logger.info(f'QdrantService - Document {i + 1} split into {len(chunks)} chunks')

			chunk_time = time.time() - chunk_start_time
			logger.info(f'QdrantService - Split {len(documents)} documents into {len(doc_chunks)} chunks in {chunk_time:.2f}s')

			# Process documents in batches
			total_indexed = 0
			total_batches = (len(doc_chunks) + batch_size - 1) // batch_size
			logger.info(f'QdrantService - Processing {total_batches} batches')

			for i in range(0, len(doc_chunks), batch_size):
				batch_start_time = time.time()
				batch_num = i // batch_size + 1
				batch = doc_chunks[i : i + batch_size]

				logger.info(f'QdrantService - Processing batch {batch_num}/{total_batches} with {len(batch)} chunks')

				# Generate embeddings for batch
				logger.info(f'QdrantService - Generating embeddings for batch {batch_num}')
				embedding_start_time = time.time()
				texts = [chunk.page_content for chunk in batch]
				embeddings = self.embeddings.embed_documents(texts)
				embedding_time = time.time() - embedding_start_time
				logger.info(f'QdrantService - Generated {len(embeddings)} embeddings in {embedding_time:.2f}s')

				# Create points for QdrantDB
				logger.info(f'QdrantService - Creating points for batch {batch_num}')
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
				logger.info(f'QdrantService - Upserting {len(points)} points to collection "{collection_name}"')
				upsert_start_time = time.time()
				self.client.upsert(collection_name=collection_name, points=points)
				upsert_time = time.time() - upsert_start_time

				total_indexed += len(points)
				batch_time = time.time() - batch_start_time

				logger.info(f'QdrantService - Batch {batch_num}/{total_batches} completed in {batch_time:.2f}s (embedding: {embedding_time:.2f}s, upsert: {upsert_time:.2f}s), total indexed: {total_indexed}')

			total_time = time.time() - start_time
			result = {'total_documents': len(documents), 'total_chunks': len(doc_chunks), 'total_indexed': total_indexed, 'collection': collection_name, 'processing_time_seconds': round(total_time, 2)}

			logger.info(f'QdrantService - Document indexing completed successfully in {total_time:.2f}s: {result}')
			return result

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to index documents after {total_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('document_indexing_failed'))

	def similarity_search(
		self,
		query: str,
		collection_name: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""Perform similarity search in QdrantDB collection"""
		start_time = time.time()
		query_preview = query[:100] + '...' if len(query) > 100 else query
		logger.info(f'QdrantService - Starting similarity search in collection "{collection_name}"')
		logger.info(f'QdrantService - Search parameters: top_k={top_k}, score_threshold={score_threshold}')
		logger.info(f'QdrantService - Query preview: "{query_preview}"')

		try:
			# Generate query embedding
			logger.info('QdrantService - Generating query embedding')
			embedding_start_time = time.time()
			query_embedding = self.embeddings.embed_query(query)
			embedding_time = time.time() - embedding_start_time
			logger.info(f'QdrantService - Query embedding generated in {embedding_time:.2f}s')

			# Search in QdrantDB
			logger.info(f'QdrantService - Performing vector search in collection "{collection_name}"')
			search_start_time = time.time()
			search_result = self.client.search(
				collection_name=collection_name,
				query_vector=query_embedding,
				limit=top_k,
				score_threshold=score_threshold,
			)
			search_time = time.time() - search_start_time
			logger.info(f'QdrantService - Vector search completed in {search_time:.2f}s, found {len(search_result)} results')

			# Convert results to Document objects
			documents = []
			for i, result in enumerate(search_result):
				doc = Document(
					page_content=result.payload['content'],
					metadata={
						**result.payload['metadata'],
						'similarity_score': result.score,
						'chunk_index': result.payload.get('chunk_index'),
					},
				)
				documents.append(doc)
				logger.info(f'QdrantService - Result {i + 1}: score={result.score:.3f}, chunk_index={result.payload.get("chunk_index")}')

			total_time = time.time() - start_time
			logger.info(f'QdrantService - Similarity search completed in {total_time:.2f}s: found {len(documents)} documents (embedding: {embedding_time:.2f}s, search: {search_time:.2f}s)')
			return documents

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to perform similarity search after {total_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('similarity_search_failed'))

	def delete_documents(self, collection_name: str, document_ids: List[str] = None) -> bool:
		"""Delete documents from collection"""
		start_time = time.time()
		if document_ids:
			logger.info(f'QdrantService - Deleting {len(document_ids)} specific documents from collection "{collection_name}"')
			logger.info(f'QdrantService - Document IDs to delete: {[doc_id[:8] + "..." for doc_id in document_ids[:5]]}{"..." if len(document_ids) > 5 else ""}')
		else:
			logger.info(f'QdrantService - Deleting entire collection "{collection_name}"')

		try:
			if document_ids:
				# Delete specific documents
				self.client.delete(
					collection_name=collection_name,
					points_selector=models.PointIdsList(points=document_ids),
				)
				deletion_time = time.time() - start_time
				logger.info(f'QdrantService - Successfully deleted {len(document_ids)} documents in {deletion_time:.2f}s')
			else:
				# Delete entire collection
				self.client.delete_collection(collection_name=collection_name)
				deletion_time = time.time() - start_time
				logger.info(f'QdrantService - Successfully deleted collection "{collection_name}" in {deletion_time:.2f}s')

			return True

		except Exception as e:
			deletion_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to delete documents after {deletion_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('document_deletion_failed'))

	def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
		"""Get collection statistics"""
		start_time = time.time()
		logger.info(f'QdrantService - Retrieving statistics for collection "{collection_name}"')

		try:
			collection_info = self.client.get_collection(collection_name=collection_name)
			stats_time = time.time() - start_time

			stats = {
				'name': collection_name,
				'vectors_count': collection_info.vectors_count,
				'indexed_vectors_count': collection_info.indexed_vectors_count,
				'points_count': collection_info.points_count,
				'segments_count': collection_info.segments_count,
				'status': collection_info.status,
			}

			logger.info(f'QdrantService - Collection stats retrieved in {stats_time:.2f}s: {stats}')
			return stats

		except Exception as e:
			stats_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to get collection stats after {stats_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('collection_stats_failed'))

	def list_collections(self) -> List[str]:
		"""List all available collections"""
		start_time = time.time()
		logger.info('QdrantService - Retrieving list of all collections')

		try:
			collections = self.client.get_collections()
			collection_names = [col.name for col in collections.collections]
			list_time = time.time() - start_time

			logger.info(f'QdrantService - Found {len(collection_names)} collections in {list_time:.2f}s: {collection_names}')
			return collection_names

		except Exception as e:
			list_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to list collections after {list_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('list_collections_failed'))

	def get_conversation_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name for a specific conversation"""
		collection_name = f'conversation_{conversation_id}'
		logger.info(f'QdrantService - Generated collection name "{collection_name}" for conversation ID: {conversation_id}')
		return collection_name

	def index_conversation_files(self, conversation_id: str, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""Index files for a specific conversation"""
		start_time = time.time()
		logger.info(f'QdrantService - Starting file indexing for conversation "{conversation_id}" with {len(files_data)} files')

		try:
			collection_name = self.get_conversation_collection_name(conversation_id)

			# Convert files data to Document objects
			documents = []
			for i, file_data in enumerate(files_data):
				doc = Document(
					page_content=file_data['content'],
					metadata={
						'file_id': file_data['file_id'],
						'file_name': file_data['file_name'],
						'file_type': file_data['file_type'],
						'conversation_id': conversation_id,
						'indexed_at': file_data.get('indexed_at'),
					},
				)
				documents.append(doc)
				logger.info(f'QdrantService - Prepared document {i + 1}: file_id={file_data["file_id"]}, file_name={file_data["file_name"]}, content_length={len(file_data["content"])}')

			# Index documents
			logger.info(f'QdrantService - Indexing {len(documents)} documents to collection "{collection_name}"')
			result = self.index_documents(documents, collection_name)

			total_time = time.time() - start_time
			result['conversation_indexing_time_seconds'] = round(total_time, 2)

			logger.info(f'QdrantService - Successfully indexed {len(documents)} files for conversation "{conversation_id}" in {total_time:.2f}s')
			return result

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to index conversation files after {total_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('conversation_files_indexing_failed'))

	def search_conversation_files(self, conversation_id: str, query: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Document]:
		"""Search files within a specific conversation"""
		start_time = time.time()
		query_preview = query[:100] + '...' if len(query) > 100 else query
		logger.info(f'QdrantService - Starting file search in conversation "{conversation_id}"')
		logger.info(f'QdrantService - Search query preview: "{query_preview}"')

		try:
			collection_name = self.get_conversation_collection_name(conversation_id)

			# Check if collection exists
			logger.info(f'QdrantService - Checking if collection "{collection_name}" exists')
			collections = self.client.get_collections()
			existing_names = [col.name for col in collections.collections]

			if collection_name not in existing_names:
				search_time = time.time() - start_time
				logger.info(f'QdrantService - No indexed files found for conversation "{conversation_id}" (collection not found) - search completed in {search_time:.2f}s')
				return []

			# Perform search
			logger.info(f'QdrantService - Collection "{collection_name}" found, performing similarity search')
			documents = self.similarity_search(query, collection_name, top_k, score_threshold)

			total_time = time.time() - start_time
			logger.info(f'QdrantService - Found {len(documents)} relevant files for query in conversation "{conversation_id}" in {total_time:.2f}s')

			# Log file details found
			for i, doc in enumerate(documents):
				file_name = doc.metadata.get('file_name', 'unknown')
				similarity_score = doc.metadata.get('similarity_score', 0)
				logger.info(f'QdrantService - Result {i + 1}: file="{file_name}", score={similarity_score:.3f}')

			return documents

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to search conversation files after {total_time:.2f}s: {str(e)}', exc_info=True)
			raise ValidationException(_('conversation_files_search_failed'))

	def delete_conversation_collection(self, conversation_id: str) -> bool:
		"""Delete all indexed files for a conversation"""
		start_time = time.time()
		logger.info(f'QdrantService - Deleting all indexed files for conversation "{conversation_id}"')

		try:
			collection_name = self.get_conversation_collection_name(conversation_id)
			result = self.delete_documents(collection_name)

			deletion_time = time.time() - start_time
			if result:
				logger.info(f'QdrantService - Successfully deleted conversation collection "{conversation_id}" in {deletion_time:.2f}s')
			else:
				logger.warning(f'QdrantService - Failed to delete conversation collection "{conversation_id}" after {deletion_time:.2f}s')

			return result

		except Exception as e:
			deletion_time = time.time() - start_time
			logger.error(f'QdrantService - Failed to delete conversation collection "{conversation_id}" after {deletion_time:.2f}s: {str(e)}', exc_info=True)
			return False
