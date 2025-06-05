import logging
from typing import List, Optional
import uuid
import io
import time

from qdrant_client import QdrantClient
from fastapi import UploadFile

# Added imports for collection creation
from qdrant_client.http.models import (
	Distance,
	VectorParams,
	CollectionStatus,
	PointStruct,
)
from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.modules.agentic_rag.schemas.kb_schema import (
	AddDocumentsRequest,
	QueryRequest,
	QueryResponse,
	QueryResponseItem,
	UploadDocumentResponse,
	ViewDocumentResponse,
)
from app.core.config import GOOGLE_API_KEY
from app.modules.agentic_rag.core.config import (
	settings,
	DEFAULT_COLLECTION,
	COLLECTION_PREFIX,
	MAX_FILE_SIZE,
	SUPPORTED_FILE_TYPES,
)
from app.modules.chat.services.file_extraction_service import file_extraction_service


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


class KBRepository:
	"""Repository for interacting with the Qdrant knowledge base."""

	def __init__(self, collection_name: str = None) -> None:
		logger.info(f'{LogColors.HEADER}[KBRepository] Initializing Knowledge Base Repository{LogColors.ENDC}')

		# Initialize Qdrant client and vector store
		qdrant_url: str = settings.QdrantUrl
		qdrant_api_key: str = settings.QdrantApiKey
		self.collection_name: str = collection_name or DEFAULT_COLLECTION
		# Add collection prefix for better organization
		if not self.collection_name.startswith(COLLECTION_PREFIX):
			self.collection_name = f'{COLLECTION_PREFIX}{self.collection_name}'

		self.embedding_model_name: str = 'models/embedding-001'
		self.vector_size: int = 768

		logger.info(f'{LogColors.OKBLUE}[KBRepository] Configuration - URL: {qdrant_url}, Collection: {self.collection_name}, Vector Size: {self.vector_size}{LogColors.ENDC}')

		# Add retry logic for Docker networking issues
		max_retries = 5
		retry_delay = 3  # seconds

		for attempt in range(max_retries):
			try:
				logger.info(f'{LogColors.OKCYAN}[KBRepository] Attempting Qdrant client connection (attempt {attempt + 1}/{max_retries}){LogColors.ENDC}')
				# Initialize Qdrant client
				self.client: QdrantClient = QdrantClient(url=qdrant_url, api_key=qdrant_api_key if qdrant_api_key else None)
				logger.info(f'{LogColors.OKGREEN}[KBRepository] Qdrant client initialized successfully{LogColors.ENDC}')
				break
			except Exception as e:
				if attempt < max_retries - 1:
					logger.info(f'{LogColors.WARNING}[KBRepository] Qdrant client connection failed (attempt {attempt + 1}/{max_retries}): {e}{LogColors.ENDC}')
					logger.info(f'{LogColors.OKBLUE}[KBRepository] Retrying in {retry_delay} seconds...{LogColors.ENDC}')
					time.sleep(retry_delay)
				else:
					logger.info(f'{LogColors.FAIL}[KBRepository] Qdrant client connection failed after {max_retries} attempts: {e}{LogColors.ENDC}')
					raise CustomHTTPException(status_code=500, message=_('error_initializing_qdrant_client'))

		# Initialize embeddings using Google's GenerativeAI embeddings
		try:
			logger.info(f'{LogColors.OKCYAN}[KBRepository] Initializing Google GenerativeAI embeddings with model: {self.embedding_model_name}{LogColors.ENDC}')
			self.embedding = GoogleGenerativeAIEmbeddings(model=self.embedding_model_name, google_api_key=GOOGLE_API_KEY)
			logger.info(f'{LogColors.OKGREEN}[KBRepository] Google GenerativeAI embeddings initialized successfully{LogColors.ENDC}')
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error initializing embeddings: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

		# Ensure collection exists
		try:
			logger.info(f'{LogColors.OKCYAN}[KBRepository] Checking collection existence: {self.collection_name}{LogColors.ENDC}')
			collection_exists = False
			try:
				collection_info = self.client.get_collection(collection_name=self.collection_name)
				if collection_info.status == CollectionStatus.GREEN:
					collection_exists = True
					logger.info(f'{LogColors.OKGREEN}[KBRepository] Collection {self.collection_name} exists and is ready (Status: GREEN){LogColors.ENDC}')
			except Exception as e:
				logger.info(f'{LogColors.WARNING}[KBRepository] Collection {self.collection_name} not found or error checking: {e}. Will attempt creation{LogColors.ENDC}')

			if not collection_exists:
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Creating new collection: {self.collection_name} with vector size: {self.vector_size}{LogColors.ENDC}')
				self.client.create_collection(
					collection_name=self.collection_name,
					vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
				)
				logger.info(f'{LogColors.OKGREEN}[KBRepository] Collection {self.collection_name} created successfully{LogColors.ENDC}')

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error ensuring collection {self.collection_name} exists: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_creating_or_checking_collection'))

		try:
			# Create or load existing Qdrant collection via LangChain wrapper
			logger.info(f'{LogColors.OKCYAN}[KBRepository] Creating vectorstore connection for collection: {self.collection_name}{LogColors.ENDC}')

			# Add retry logic for collection creation/connection
			for attempt in range(max_retries):
				try:
					self.vectorstore = QdrantVectorStore(
						client=self.client,
						collection_name=self.collection_name,
						embedding=self.embedding,
						metadata_payload_key='metadata',
					)
					logger.info(f'{LogColors.OKGREEN}[KBRepository] Vectorstore connected successfully to collection {self.collection_name} at {qdrant_url}{LogColors.ENDC}')
					break
				except Exception as e:
					if attempt < max_retries - 1:
						logger.info(f'{LogColors.WARNING}[KBRepository] Vectorstore connection failed (attempt {attempt + 1}/{max_retries}): {e}{LogColors.ENDC}')
						logger.info(f'{LogColors.OKBLUE}[KBRepository] Retrying vectorstore connection in {retry_delay} seconds...{LogColors.ENDC}')
						time.sleep(retry_delay)
					else:
						raise
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error initializing Qdrant vector store: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

	def _get_full_collection_name(self, collection_id: str) -> str:
		"""Get full collection name with prefix."""
		if collection_id.startswith(COLLECTION_PREFIX):
			return collection_id
		return f'{COLLECTION_PREFIX}{collection_id}'

	def create_collection(self, collection_id: str) -> bool:
		"""Create a new collection."""
		collection_name = self._get_full_collection_name(collection_id)
		logger.info(f'{LogColors.HEADER}[KBRepository] Creating collection: {collection_name}{LogColors.ENDC}')

		try:
			self.client.create_collection(
				collection_name=collection_name,
				vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
			)
			logger.info(f'{LogColors.OKGREEN}[KBRepository] Collection created successfully: {collection_name}{LogColors.ENDC}')
			return True
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error creating collection {collection_name}: {e}{LogColors.ENDC}')
			return False

	def collection_exists(self, collection_id: str) -> bool:
		"""Check if collection exists."""
		collection_name = self._get_full_collection_name(collection_id)
		try:
			self.client.get_collection(collection_name=collection_name)
			return True
		except Exception:
			return False

	def _get_collection_vectorstore(self, collection_id: str) -> QdrantVectorStore:
		"""Get vectorstore for specific collection."""
		collection_name = self._get_full_collection_name(collection_id)
		logger.info(f'{LogColors.OKCYAN}[KBRepository] Creating vectorstore for collection: {collection_name}{LogColors.ENDC}')

		return QdrantVectorStore(
			client=self.client,
			collection_name=collection_name,
			embedding=self.embedding,
			metadata_payload_key='metadata',
		)

	async def add_documents(self, request: AddDocumentsRequest, collection_id: str = None) -> List[str]:
		"""Add documents to the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION
		logger.info(f'{LogColors.HEADER}[KBRepository] Adding {len(request.documents)} documents to collection: {collection_id}{LogColors.ENDC}')

		try:
			# Ensure collection exists
			if not self.collection_exists(collection_id):
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Collection does not exist, creating: {collection_id}{LogColors.ENDC}')
				self.create_collection(collection_id)

			# Get collection-specific vectorstore
			vectorstore = self._get_collection_vectorstore(collection_id)

			docs: List[Document] = []
			for i, doc in enumerate(request.documents):
				logger.info(f'{LogColors.OKCYAN}[KBRepository] Processing document {i + 1}/{len(request.documents)}: ID={doc.id}{LogColors.ENDC}')
				docs.append(
					Document(
						page_content=doc.content,
						metadata={**doc.metadata, 'collection_id': collection_id},
						id=doc.id,
					)
				)

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Adding {len(docs)} documents to vectorstore{LogColors.ENDC}')
			vectorstore.add_documents(documents=docs)

			ids: List[str] = [doc.id for doc in request.documents]
			logger.info(f'{LogColors.OKGREEN}[KBRepository] Successfully added documents to collection {collection_id}: {ids}{LogColors.ENDC}')
			return ids
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error adding documents to collection {collection_id}: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

	async def query(self, request: QueryRequest, collection_id: str = None) -> QueryResponse:
		"""Query the knowledge base for similar documents."""
		collection_id = collection_id or DEFAULT_COLLECTION
		logger.info(f'{LogColors.HEADER}[KBRepository] Querying collection {collection_id}: "{request.query[:50]}..."{LogColors.ENDC}')

		try:
			# Check if collection exists
			if not self.collection_exists(collection_id):
				logger.info(f'{LogColors.WARNING}[KBRepository] Collection not found: {collection_id}{LogColors.ENDC}')
				return QueryResponse(results=[])

			# Get collection-specific vectorstore
			vectorstore = self._get_collection_vectorstore(collection_id)

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Executing similarity search in collection: {collection_id}{LogColors.ENDC}')
			results = vectorstore.similarity_search(
				query=request.query,
				k=request.top_k,
			)

			items: List[QueryResponseItem] = []
			for i, res in enumerate(results):
				logger.info(f'{LogColors.OKCYAN}[KBRepository] Processing result {i + 1}: ID={res.id}{LogColors.ENDC}')
				item = QueryResponseItem(
					id=res.id,
					content=res.page_content,
					score=getattr(res, 'score', 0.0),
					metadata=res.metadata or {},
				)
				items.append(item)

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Query completed for collection {collection_id} - Retrieved {len(items)} results{LogColors.ENDC}')
			return QueryResponse(results=items)
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error querying collection {collection_id}: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

	async def upload_file(self, file: UploadFile, collection_id: str = None) -> UploadDocumentResponse:
		"""Upload a file, parse it, and add it to the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION
		logger.info(f'{LogColors.HEADER}[KBRepository] Uploading file {file.filename} to collection: {collection_id}{LogColors.ENDC}')

		try:
			# Validate file size
			content = await file.read()
			if len(content) > MAX_FILE_SIZE:
				logger.info(f'{LogColors.FAIL}[KBRepository] File too large: {len(content)} bytes > {MAX_FILE_SIZE}{LogColors.ENDC}')
				raise CustomHTTPException(message=_('file_too_large'))

			# Validate file type
			if file.content_type not in SUPPORTED_FILE_TYPES:
				logger.info(f'{LogColors.FAIL}[KBRepository] Unsupported file type: {file.content_type}{LogColors.ENDC}')
				raise CustomHTTPException(message=_('unsupported_file_type'))

			# Extract text content using file extraction service
			logger.info(f'{LogColors.OKBLUE}[KBRepository] Extracting text content from file{LogColors.ENDC}')
			extraction_result = self.file_extraction.extract_text_from_file(
				file_content=content,
				file_type=file.content_type,
				file_name=file.filename,
			)

			if not extraction_result['extraction_success']:
				logger.info(f'{LogColors.FAIL}[KBRepository] Text extraction failed: {extraction_result["extraction_error"]}{LogColors.ENDC}')
				raise CustomHTTPException(message=_('error_extracting_text'))

			text_content = extraction_result['content']
			if not text_content.strip():
				logger.info(f'{LogColors.WARNING}[KBRepository] No content extracted from file{LogColors.ENDC}')
				raise CustomHTTPException(message=_('empty_file_content'))

			# Ensure collection exists
			if not self.collection_exists(collection_id):
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Creating collection: {collection_id}{LogColors.ENDC}')
				self.create_collection(collection_id)

			# Get collection-specific vectorstore
			vectorstore = self._get_collection_vectorstore(collection_id)

			doc_id = str(uuid.uuid4())
			metadata = {
				'source': file.filename,
				'file_type': file.content_type,
				'upload_date': str(uuid.uuid1().time),
				'collection_id': collection_id,
				'char_count': extraction_result['char_count'],
			}

			# Create document
			langchain_doc = Document(page_content=text_content, metadata=metadata)

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Adding document to collection: {collection_id}{LogColors.ENDC}')
			ids = vectorstore.add_documents(documents=[langchain_doc], ids=[doc_id])

			if not ids:
				raise CustomHTTPException(message=_('error_adding_document_to_vector_store'))

			response = UploadDocumentResponse(
				id=doc_id,
				filename=file.filename,
				content_type=file.content_type,
				size=len(content),
				metadata=metadata,
			)

			logger.info(f'{LogColors.OKGREEN}[KBRepository] File uploaded successfully to collection {collection_id}: {file.filename}{LogColors.ENDC}')
			return response

		except CustomHTTPException:
			raise
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error uploading file: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_uploading_file'))

	async def get_document(self, document_id: str, collection_id: str = None) -> Optional[ViewDocumentResponse]:
		"""Retrieve a document from the knowledge base by its ID."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)
		logger.info(f'{LogColors.HEADER}[KBRepository] Retrieving document {document_id} from collection: {collection_id}{LogColors.ENDC}')

		try:
			points = self.client.retrieve(
				collection_name=collection_name,
				ids=[document_id],
				with_payload=True,
				with_vectors=False,
			)

			if not points:
				return None

			point = points[0]
			content = point.payload.get('page_content', '') if point.payload else ''
			metadata = point.payload.get('metadata', {}) if point.payload else {}

			return ViewDocumentResponse(id=document_id, content=content, metadata=metadata)

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error retrieving document: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_retrieving_document'))

	async def delete_document(self, document_id: str, collection_id: str = None) -> bool:
		"""Delete a document from the knowledge base by its ID."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)
		logger.info(f'{LogColors.HEADER}[KBRepository] Deleting document {document_id} from collection: {collection_id}{LogColors.ENDC}')

		try:
			self.client.delete(
				collection_name=collection_name,
				points_selector=[document_id],
			)
			return True
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error deleting document: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_deleting_document'))

	async def list_all_documents(self, collection_id: str = None) -> List[ViewDocumentResponse]:
		"""List all documents from the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)
		logger.info(f'{LogColors.HEADER}[KBRepository] Listing documents from collection: {collection_id}{LogColors.ENDC}')

		try:
			all_documents: List[ViewDocumentResponse] = []
			next_page_offset = None

			while True:
				points, next_page_offset = self.client.scroll(
					collection_name=collection_name,
					limit=100,
					offset=next_page_offset,
					with_payload=True,
					with_vectors=False,
				)

				for point in points:
					doc_id = str(point.id)
					content = point.payload.get('page_content', '') if point.payload else ''
					metadata = point.payload.get('metadata', {}) if point.payload else {}
					all_documents.append(ViewDocumentResponse(id=doc_id, content=content, metadata=metadata))

				if not next_page_offset:
					break

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Listed {len(all_documents)} documents from collection: {collection_id}{LogColors.ENDC}')
			return all_documents

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error listing documents: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_listing_documents'))

	def list_collections(self) -> List[str]:
		"""List all available collections."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Listing all collections{LogColors.ENDC}')

		try:
			collections = self.client.get_collections().collections
			collection_names = [col.name for col in collections if col.name.startswith(COLLECTION_PREFIX)]
			# Remove prefix for user-friendly names
			clean_names = [name.replace(COLLECTION_PREFIX, '') for name in collection_names]

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Found {len(clean_names)} collections: {clean_names}{LogColors.ENDC}')
			return clean_names
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error listing collections: {e}{LogColors.ENDC}')
			return []
