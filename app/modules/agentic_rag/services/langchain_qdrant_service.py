"""
LangChain Qdrant Service for Agentic RAG
Using langchain-qdrant QdrantVectorStore for vector operations
"""

import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
import uuid
import time

logger = logging.getLogger(__name__)


class LangChainQdrantService:
	"""Service using LangChain QdrantVectorStore for Agentic RAG"""

	def __init__(self, db: Session):
		logger.info('LangChainQdrantService - Initializing with LangChain Qdrant integration')
		self.db = db
		self.client = None
		self.embeddings = None
		self.vector_stores = {}  # Cache vector stores by collection
		self.vector_size = 768  # Google embedding size
		logger.info(f'LangChainQdrantService - Vector size: {self.vector_size}')
		self._initialize_client()

	def _initialize_client(self):
		"""Initialize Qdrant client and embeddings for LangChain"""
		start_time = time.time()
		logger.info('LangChainQdrantService - Starting LangChain Qdrant initialization')

		try:
			# Qdrant connection setup
			qdrant_path = os.getenv('QDRANT_PATH', './qdrant_storage')
			qdrant_host = os.getenv('QDRANT_HOST')
			qdrant_port = int(os.getenv('QDRANT_PORT', 6333))

			logger.info(f'LangChainQdrantService - Config: host={qdrant_host}, port={qdrant_port}, path={qdrant_path}')

			if qdrant_host:
				# Remote Qdrant server
				logger.info(f'LangChainQdrantService - Connecting to Qdrant server at {qdrant_host}:{qdrant_port}')
				self.qdrant_url = f'http://{qdrant_host}:{qdrant_port}'
				self.client = QdrantClient(host=qdrant_host, port=qdrant_port)
			else:
				# Local storage
				logger.info(f'LangChainQdrantService - Using local storage at: {qdrant_path}')
				self.qdrant_url = None
				self.qdrant_path = qdrant_path
				self.client = QdrantClient(path=qdrant_path)

			# Initialize Google embeddings
			logger.info('LangChainQdrantService - Initializing Google Generative AI embeddings')
			self.embeddings = GoogleGenerativeAIEmbeddings(model='models/text-embedding-004')
			logger.info('LangChainQdrantService - Google embeddings initialized successfully')

			initialization_time = time.time() - start_time
			logger.info(f'LangChainQdrantService - LangChain Qdrant initialized successfully in {initialization_time:.2f}s')

		except Exception as e:
			initialization_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to initialize after {initialization_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('langchain_qdrant_initialization_failed'))

	def get_vector_store(self, collection_name: str) -> QdrantVectorStore:
		"""Get or create QdrantVectorStore for collection"""
		logger.info(f"LangChainQdrantService - Getting vector store for collection: '{collection_name}'")

		if collection_name in self.vector_stores:
			logger.info(f"LangChainQdrantService - Using cached vector store for '{collection_name}'")
			return self.vector_stores[collection_name]

		try:
			# Create QdrantVectorStore instance
			if self.qdrant_url:
				# Remote connection
				vector_store = QdrantVectorStore.from_existing_collection(
					embedding=self.embeddings,
					collection_name=collection_name,
					url=self.qdrant_url,
				)
				logger.info(f"LangChainQdrantService - Connected to remote collection '{collection_name}' at {self.qdrant_url}")
			else:
				# Local storage
				vector_store = QdrantVectorStore.from_existing_collection(
					embedding=self.embeddings,
					collection_name=collection_name,
					path=self.qdrant_path,
				)
				logger.info(f"LangChainQdrantService - Connected to local collection '{collection_name}' at {self.qdrant_path}")

			# Cache the vector store
			self.vector_stores[collection_name] = vector_store
			logger.info(f"LangChainQdrantService - Vector store cached for '{collection_name}'")

			return vector_store

		except Exception as e:
			logger.error(
				f"LangChainQdrantService - Failed to get vector store for '{collection_name}': {str(e)}",
				exc_info=True,
			)
			# Try to create new collection if it doesn't exist
			return self._create_vector_store(collection_name)

	def _create_vector_store(self, collection_name: str) -> QdrantVectorStore:
		"""Create new QdrantVectorStore collection"""
		logger.info(f"LangChainQdrantService - Creating new vector store collection: '{collection_name}'")

		try:
			if self.qdrant_url:
				# Remote connection
				vector_store = QdrantVectorStore(
					client=self.client,
					collection_name=collection_name,
					embeddings=self.embeddings,
				)
				logger.info(f"LangChainQdrantService - Created remote collection '{collection_name}'")
			else:
				# Local storage
				vector_store = QdrantVectorStore(
					client=self.client,
					collection_name=collection_name,
					embeddings=self.embeddings,
				)
				logger.info(f"LangChainQdrantService - Created local collection '{collection_name}'")

			# Cache the vector store
			self.vector_stores[collection_name] = vector_store
			logger.info(f"LangChainQdrantService - New vector store cached for '{collection_name}'")

			return vector_store

		except Exception as e:
			logger.error(
				f"LangChainQdrantService - Failed to create vector store for '{collection_name}': {str(e)}",
				exc_info=True,
			)
			raise ValidationException(_('vector_store_creation_failed'))

	def index_documents(self, documents: List[Document], collection_name: str, batch_size: int = 50) -> Dict[str, Any]:
		"""Index documents using LangChain QdrantVectorStore"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Starting document indexing: {len(documents)} documents to collection "{collection_name}"')

		try:
			# Text splitter for large documents
			text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
			logger.info('LangChainQdrantService - Text splitter configured: chunk_size=1000, chunk_overlap=200')

			# Split documents
			logger.info('LangChainQdrantService - Starting document chunking')
			chunk_start_time = time.time()
			doc_chunks = []
			for i, doc in enumerate(documents):
				chunks = text_splitter.split_documents([doc])
				doc_chunks.extend(chunks)
				logger.info(f'LangChainQdrantService - Document {i + 1} split into {len(chunks)} chunks')

			chunk_time = time.time() - chunk_start_time
			logger.info(f'LangChainQdrantService - Split {len(documents)} documents into {len(doc_chunks)} chunks in {chunk_time:.2f}s')

			# Get or create vector store
			vector_store = self.get_vector_store(collection_name)

			# Add documents to vector store
			logger.info(f'LangChainQdrantService - Adding {len(doc_chunks)} chunks to vector store')
			indexing_start_time = time.time()

			# Process in batches
			total_indexed = 0
			for i in range(0, len(doc_chunks), batch_size):
				batch = doc_chunks[i : i + batch_size]
				batch_num = i // batch_size + 1
				total_batches = (len(doc_chunks) + batch_size - 1) // batch_size

				logger.info(f'LangChainQdrantService - Processing batch {batch_num}/{total_batches} with {len(batch)} chunks')

				# Add documents to vector store
				texts = [doc.page_content for doc in batch]
				metadatas = [doc.metadata for doc in batch]

				vector_store.add_texts(texts=texts, metadatas=metadatas)
				total_indexed += len(batch)

				logger.info(f'LangChainQdrantService - Batch {batch_num} indexed, total: {total_indexed}')

			indexing_time = time.time() - indexing_start_time
			total_time = time.time() - start_time

			result = {
				'total_documents': len(documents),
				'total_chunks': len(doc_chunks),
				'total_indexed': total_indexed,
				'collection': collection_name,
				'indexing_time_seconds': round(indexing_time, 2),
				'total_time_seconds': round(total_time, 2),
			}

			logger.info(f'LangChainQdrantService - Document indexing completed successfully in {total_time:.2f}s: {result}')
			return result

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to index documents after {total_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('document_indexing_failed'))

	def similarity_search(
		self,
		query: str,
		collection_name: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""Perform similarity search using LangChain QdrantVectorStore"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Starting similarity search in collection "{collection_name}"')
		logger.info(f'LangChainQdrantService - Search parameters: top_k={top_k}, score_threshold={score_threshold}')

		try:
			# Get vector store
			vector_store = self.get_vector_store(collection_name)

			# Perform similarity search with score
			logger.info(f'LangChainQdrantService - Performing similarity search')
			search_start_time = time.time()

			results_with_scores = vector_store.similarity_search_with_score(query=query, k=top_k)

			search_time = time.time() - search_start_time
			logger.info(f'LangChainQdrantService - Search completed in {search_time:.2f}s, found {len(results_with_scores)} results')

			# Filter by score threshold and convert to documents
			documents = []
			for doc, score in results_with_scores:
				if score >= score_threshold:
					# Add similarity score to metadata
					doc.metadata['similarity_score'] = score
					documents.append(doc)
					logger.info(f'LangChainQdrantService - Result: score={score:.3f}, content_length={len(doc.page_content)}')

			total_time = time.time() - start_time
			logger.info(f'LangChainQdrantService - Similarity search completed in {total_time:.2f}s: found {len(documents)} documents above threshold')
			return documents

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to perform similarity search after {total_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('similarity_search_failed'))

	def get_retriever(self, collection_name: str, search_kwargs: Dict[str, Any] = None) -> Any:
		"""Get LangChain retriever for RAG"""
		logger.info(f'LangChainQdrantService - Creating retriever for collection "{collection_name}"')

		try:
			vector_store = self.get_vector_store(collection_name)

			# Default search kwargs
			default_kwargs = {'k': 5, 'score_threshold': 0.7}
			if search_kwargs:
				default_kwargs.update(search_kwargs)

			# Create retriever with similarity search with score threshold
			retriever = vector_store.as_retriever(search_type='similarity_score_threshold', search_kwargs=default_kwargs)

			logger.info(f'LangChainQdrantService - Retriever created for "{collection_name}" with kwargs: {default_kwargs}')
			return retriever

		except Exception as e:
			logger.error(
				f'LangChainQdrantService - Failed to create retriever for "{collection_name}": {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('retriever_creation_failed'))

	def delete_collection(self, collection_name: str) -> bool:
		"""Delete collection"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Deleting collection "{collection_name}"')

		try:
			# Remove from cache
			if collection_name in self.vector_stores:
				del self.vector_stores[collection_name]

			# Delete from Qdrant
			self.client.delete_collection(collection_name=collection_name)

			deletion_time = time.time() - start_time
			logger.info(f'LangChainQdrantService - Successfully deleted collection "{collection_name}" in {deletion_time:.2f}s')
			return True

		except Exception as e:
			deletion_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to delete collection "{collection_name}" after {deletion_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			return False

	def list_collections(self) -> List[str]:
		"""List all collections"""
		start_time = time.time()
		logger.info('LangChainQdrantService - Listing all collections')

		try:
			collections = self.client.get_collections()
			collection_names = [col.name for col in collections.collections]

			list_time = time.time() - start_time
			logger.info(f'LangChainQdrantService - Found {len(collection_names)} collections in {list_time:.2f}s: {collection_names}')
			return collection_names

		except Exception as e:
			list_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to list collections after {list_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			return []

	def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
		"""Get collection statistics"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Getting stats for collection "{collection_name}"')

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

			logger.info(f'LangChainQdrantService - Collection stats retrieved in {stats_time:.2f}s: {stats}')
			return stats

		except Exception as e:
			stats_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to get collection stats after {stats_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('collection_stats_failed'))

	def get_conversation_collection_name(self, conversation_id: str) -> str:
		"""Generate collection name for conversation"""
		collection_name = f'conversation_{conversation_id}'
		logger.info(f'LangChainQdrantService - Generated collection name "{collection_name}" for conversation: {conversation_id}')
		return collection_name

	def index_conversation_files(self, conversation_id: str, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""Index files for conversation using LangChain"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Starting file indexing for conversation "{conversation_id}" with {len(files_data)} files')

		try:
			collection_name = self.get_conversation_collection_name(conversation_id)

			# Convert files to Document objects
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
				logger.info(f'LangChainQdrantService - Prepared document {i + 1}: {file_data["file_name"]}')

			# Index documents
			result = self.index_documents(documents, collection_name)

			total_time = time.time() - start_time
			result['conversation_indexing_time_seconds'] = round(total_time, 2)

			logger.info(f'LangChainQdrantService - Successfully indexed {len(documents)} files for conversation "{conversation_id}" in {total_time:.2f}s')
			return result

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to index conversation files after {total_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			raise ValidationException(_('conversation_files_indexing_failed'))

	def search_conversation_files(
		self,
		conversation_id: str,
		query: str,
		top_k: int = 5,
		score_threshold: float = 0.7,
	) -> List[Document]:
		"""Search files in conversation using LangChain"""
		start_time = time.time()
		logger.info(f'LangChainQdrantService - Starting file search in conversation "{conversation_id}"')

		try:
			collection_name = self.get_conversation_collection_name(conversation_id)

			# Check if collection exists
			collections = self.list_collections()
			if collection_name not in collections:
				logger.info(f'LangChainQdrantService - No files indexed for conversation "{conversation_id}"')
				return []

			# Perform search
			documents = self.similarity_search(query, collection_name, top_k, score_threshold)

			total_time = time.time() - start_time
			logger.info(f'LangChainQdrantService - Found {len(documents)} relevant files in conversation "{conversation_id}" in {total_time:.2f}s')

			return documents

		except Exception as e:
			total_time = time.time() - start_time
			logger.error(
				f'LangChainQdrantService - Failed to search conversation files after {total_time:.2f}s: {str(e)}',
				exc_info=True,
			)
			return []
