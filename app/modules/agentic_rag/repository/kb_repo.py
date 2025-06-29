import io
import logging
import time
import uuid
from typing import List, Optional

from fastapi import UploadFile
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

# Added imports for collection creation
from qdrant_client.http.models import (
	CollectionStatus,
	Distance,
	PointStruct,
	VectorParams,
)

from app.core.config import GOOGLE_API_KEY
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _
from app.modules.agentic_rag.core.config import (
	COLLECTION_PREFIX,
	DEFAULT_COLLECTION,
	MAX_FILE_SIZE,
	SUPPORTED_FILE_TYPES,
	settings,
)
from app.modules.agentic_rag.schemas.kb_schema import (
	AddDocumentsRequest,
	QueryRequest,
	QueryResponse,
	QueryResponseItem,
	UploadDocumentResponse,
	ViewDocumentResponse,
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
		# Initialize Qdrant client and vector store
		qdrant_url: str = settings.QdrantUrl
		qdrant_api_key: str = settings.QdrantApiKey
		self.collection_name: str = collection_name or DEFAULT_COLLECTION
		# Add collection prefix for better organization
		if not self.collection_name.startswith(COLLECTION_PREFIX):
			self.collection_name = f'{COLLECTION_PREFIX}{self.collection_name}'

		self.embedding_model_name: str = 'models/embedding-001'
		self.vector_size: int = 768

		# Add retry logic for Docker networking issues
		max_retries = 5
		retry_delay = 3  # seconds

		for attempt in range(max_retries):
			try:
				# Initialize Qdrant client
				self.client: QdrantClient = QdrantClient(url=qdrant_url, api_key=qdrant_api_key if qdrant_api_key else None)
				break
			except Exception as e:
				print(e)
				if attempt < max_retries - 1:
					time.sleep(retry_delay)
				else:
					raise CustomHTTPException(status_code=500, message=_('error_initializing_qdrant_client'))

		# Initialize embeddings using Google's GenerativeAI embeddings
		try:
			self.embedding = GoogleGenerativeAIEmbeddings(model=self.embedding_model_name, google_api_key=GOOGLE_API_KEY)
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_occurred'))

		# Initialize file extraction service
		try:
			self.file_extraction = file_extraction_service
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_initializing_file_extraction'))

		# Ensure collection exists
		try:
			collection_exists = False
			try:
				collection_info = self.client.get_collection(collection_name=self.collection_name)
				if collection_info.status == CollectionStatus.GREEN:
					collection_exists = True
			except Exception as e:
				print(e)
				print(f'\033[93m[KBRepository] Collection {self.collection_name} does not exist, creating...\033[0m')

			if not collection_exists:
				self.client.create_collection(
					collection_name=self.collection_name,
					vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
				)

		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_creating_or_checking_collection'))

		try:
			# Create or load existing Qdrant collection via LangChain wrapper

			# Add retry logic for collection creation/connection
			for attempt in range(max_retries):
				try:
					self.vectorstore = QdrantVectorStore(
						client=self.client,
						collection_name=self.collection_name,
						embedding=self.embedding,
						metadata_payload_key='metadata',
					)
					break
				except Exception as e:
					print(e)
					if attempt < max_retries - 1:
						time.sleep(retry_delay)
					else:
						raise
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_occurred'))

	def _get_full_collection_name(self, collection_id: str) -> str:
		"""Get full collection name with prefix."""
		if collection_id.startswith(COLLECTION_PREFIX):
			return collection_id
		return f'{COLLECTION_PREFIX}{collection_id}'

	def create_collection(self, collection_id: str) -> bool:
		"""Create a new collection."""
		collection_name = self._get_full_collection_name(collection_id)

		try:
			self.client.create_collection(
				collection_name=collection_name,
				vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
			)
			return True
		except Exception as e:
			print(e)
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

		return QdrantVectorStore(
			client=self.client,
			collection_name=collection_name,
			embedding=self.embedding,
			metadata_payload_key='metadata',
		)

	async def add_documents(self, request: AddDocumentsRequest, collection_id: str = None) -> List[str]:
		"""Add documents to the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION

		try:
			# Ensure collection exists
			if not self.collection_exists(collection_id):
				self.create_collection(collection_id)

			# Get collection-specific vectorstore
			vectorstore = self._get_collection_vectorstore(collection_id)

			docs: List[Document] = []
			for i, doc in enumerate(request.documents):
				docs.append(
					Document(
						page_content=doc.content,
						metadata={**doc.metadata, 'collection_id': collection_id},
						id=doc.id,
					)
				)

			vectorstore.add_documents(documents=docs)

			ids: List[str] = [doc.id for doc in request.documents]
			return ids
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_occurred'))

	async def query(self, request: QueryRequest, collection_id: str = None) -> QueryResponse:
		"""Query the knowledge base for similar documents."""
		collection_id = collection_id or DEFAULT_COLLECTION

		try:
			# Check if collection exists
			if not self.collection_exists(collection_id):
				return QueryResponse(results=[])

			# Get collection-specific vectorstore
			vectorstore = self._get_collection_vectorstore(collection_id)

			results = vectorstore.similarity_search(
				query=request.query,
				k=request.top_k,
			)

			items: List[QueryResponseItem] = []
			for i, res in enumerate(results):
				item = QueryResponseItem(
					id=res.id,
					content=res.page_content,
					score=getattr(res, 'score', 0.0),
					metadata=res.metadata or {},
				)
				items.append(item)

			return QueryResponse(results=items)
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_occurred'))

	async def upload_file(self, file: UploadFile, collection_id: str = None) -> UploadDocumentResponse:
		"""Upload a file, parse it, and add it to the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION

		try:
			# Validate file size
			content = await file.read()
			if len(content) > MAX_FILE_SIZE:
				raise CustomHTTPException(message=_('file_too_large'))

			# Validate file type
			if file.content_type not in SUPPORTED_FILE_TYPES:
				raise CustomHTTPException(message=_('unsupported_file_type'))

			# Extract text content using file extraction service
			extraction_result = self.file_extraction.extract_text_from_file(
				file_content=content,
				file_type=file.content_type,
				file_name=file.filename,
			)

			if not extraction_result['extraction_success']:
				raise CustomHTTPException(message=_('error_extracting_text'))

			text_content = extraction_result['content']
			if not text_content.strip():
				raise CustomHTTPException(message=_('empty_file_content'))

			# Ensure collection exists
			if not self.collection_exists(collection_id):
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

			return response

		except CustomHTTPException:
			raise
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_uploading_file'))

	async def get_document(self, document_id: str, collection_id: str = None) -> Optional[ViewDocumentResponse]:
		"""Retrieve a document from the knowledge base by its ID."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)

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
			print(e)
			raise CustomHTTPException(message=_('error_retrieving_document'))

	async def delete_document(self, document_id: str, collection_id: str = None) -> bool:
		"""Delete a document from the knowledge base by its ID."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)

		try:
			self.client.delete(
				collection_name=collection_name,
				points_selector=[document_id],
			)
			return True
		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_deleting_document'))

	async def list_all_documents(self, collection_id: str = None) -> List[ViewDocumentResponse]:
		"""List all documents from the knowledge base."""
		collection_id = collection_id or DEFAULT_COLLECTION
		collection_name = self._get_full_collection_name(collection_id)

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

			return all_documents

		except Exception as e:
			print(e)
			raise CustomHTTPException(message=_('error_listing_documents'))

	def list_collections(self) -> List[str]:
		"""List all available collections."""

		try:
			collections = self.client.get_collections().collections
			collection_names = [col.name for col in collections if col.name.startswith(COLLECTION_PREFIX)]
			# Remove prefix for user-friendly names
			clean_names = [name.replace(COLLECTION_PREFIX, '') for name in collection_names]

			return clean_names
		except Exception as e:
			print(e)
			return []
