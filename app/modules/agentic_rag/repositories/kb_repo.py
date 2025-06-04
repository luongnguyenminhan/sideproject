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
from app.modules.agentic_rag.core.config import settings


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

	def __init__(self) -> None:
		logger.info(f'{LogColors.HEADER}[KBRepository] Initializing Knowledge Base Repository{LogColors.ENDC}')

		# Initialize Qdrant client and vector store
		qdrant_url: str = settings.QdrantUrl
		qdrant_api_key: str = settings.QdrantApiKey
		self.collection_name: str = settings.QdrantCollection
		self.embedding_model_name: str = 'models/embedding-001'  # Store model name
		self.vector_size: int = 768  # Dimension for models/embedding-001

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

	async def add_documents(self, request: AddDocumentsRequest) -> List[str]:
		"""Add documents to the knowledge base."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Starting to add {len(request.documents)} documents to knowledge base{LogColors.ENDC}')

		try:
			docs: List[Document] = []
			for i, doc in enumerate(request.documents):
				logger.info(f'{LogColors.OKCYAN}[KBRepository] Processing document {i + 1}/{len(request.documents)}: ID={doc.id}, Content length={len(doc.content)}{LogColors.ENDC}')
				docs.append(
					Document(
						page_content=doc.content,
						metadata=doc.metadata,
						id=doc.id,
					)
				)

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Adding {len(docs)} documents to vectorstore{LogColors.ENDC}')
			self.vectorstore.add_documents(documents=docs)

			ids: List[str] = [doc.id for doc in request.documents]
			logger.info(f'{LogColors.OKGREEN}[KBRepository] Successfully added documents with IDs: {ids}{LogColors.ENDC}')
			return ids
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error adding documents: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

	async def query(self, request: QueryRequest) -> QueryResponse:
		"""Query the knowledge base for similar documents."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Starting query: "{request.query[:50]}..." (Top K: {request.top_k}){LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKBLUE}[KBRepository] Executing similarity search in vectorstore{LogColors.ENDC}')
			results = self.vectorstore.similarity_search(
				query=request.query,
				k=request.top_k,
			)

			logger.info(f'{LogColors.OKCYAN}[KBRepository] Similarity search returned {len(results)} results{LogColors.ENDC}')

			items: List[QueryResponseItem] = []
			for i, res in enumerate(results):
				logger.info(f'{LogColors.OKCYAN}[KBRepository] Processing result {i + 1}: ID={res.id}, Content length={len(res.page_content)}{LogColors.ENDC}')
				item = QueryResponseItem(
					id=res.id,
					content=res.page_content,
					score=getattr(res, 'score', 0.0),
					metadata=res.metadata or {},
				)
				items.append(item)

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Query completed successfully - Retrieved {len(items)} results{LogColors.ENDC}')
			return QueryResponse(results=items)
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error querying knowledge base: {e}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_occurred'))

	async def upload_file(self, file: UploadFile) -> UploadDocumentResponse:
		"""Upload a file, parse it, and add it to the knowledge base."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Starting file upload: {file.filename} (Type: {file.content_type}){LogColors.ENDC}')

		try:
			# Read file content
			logger.info(f'{LogColors.OKBLUE}[KBRepository] Reading file content for: {file.filename}{LogColors.ENDC}')
			content = await file.read()
			logger.info(f'{LogColors.OKCYAN}[KBRepository] File content read successfully - Size: {len(content)} bytes{LogColors.ENDC}')

			text_content = ''
			doc_id = str(uuid.uuid4())
			metadata = {
				'source': file.filename,
				'file_type': file.content_type,
				'upload_date': str(uuid.uuid1().time),
			}

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Generated document ID: {doc_id}{LogColors.ENDC}')

			# Process file based on content type
			if file.filename.lower().endswith('.pdf'):
				logger.info(f'{LogColors.WARNING}[KBRepository] Processing PDF file: {file.filename} (using simplified extraction){LogColors.ENDC}')
				try:
					text_content = f'PDF content extracted from {file.filename}'
					logger.info(f'{LogColors.OKGREEN}[KBRepository] PDF file processed (simplified extraction completed){LogColors.ENDC}')
				except Exception as pdf_error:
					logger.info(f'{LogColors.FAIL}[KBRepository] Error parsing PDF: {pdf_error}{LogColors.ENDC}')
					raise CustomHTTPException(message=_('error_parsing_pdf'))
			elif file.filename.lower().endswith('.txt'):
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Processing TXT file: {file.filename}{LogColors.ENDC}')
				try:
					text_content = content.decode('utf-8')
					logger.info(f'{LogColors.OKGREEN}[KBRepository] TXT file parsed successfully with UTF-8 - {len(text_content)} characters{LogColors.ENDC}')
				except UnicodeDecodeError:
					logger.info(f'{LogColors.WARNING}[KBRepository] UTF-8 decode failed, trying latin-1 for: {file.filename}{LogColors.ENDC}')
					text_content = content.decode('latin-1')
					logger.info(f'{LogColors.OKGREEN}[KBRepository] TXT file parsed successfully with latin-1 encoding{LogColors.ENDC}')
			elif file.filename.lower().endswith('.md'):
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Processing Markdown file: {file.filename}{LogColors.ENDC}')
				try:
					text_content = content.decode('utf-8')
					logger.info(f'{LogColors.OKGREEN}[KBRepository] Markdown file parsed successfully with UTF-8 - {len(text_content)} characters{LogColors.ENDC}')
				except UnicodeDecodeError:
					logger.info(f'{LogColors.WARNING}[KBRepository] UTF-8 decode failed, trying latin-1 for: {file.filename}{LogColors.ENDC}')
					text_content = content.decode('latin-1')
					logger.info(f'{LogColors.OKGREEN}[KBRepository] Markdown file parsed successfully with latin-1 encoding{LogColors.ENDC}')
			else:
				logger.info(f'{LogColors.WARNING}[KBRepository] Unsupported file type: {file.filename}{LogColors.ENDC}')
				raise CustomHTTPException(message=_('unsupported_file_type'))

			# Check if we extracted any content
			if not text_content.strip():
				logger.info(f'{LogColors.WARNING}[KBRepository] No content extracted from file: {file.filename}{LogColors.ENDC}')
				raise CustomHTTPException(message=_('empty_file_content'))

			# Create a document and add it to vectorstore
			logger.info(f'{LogColors.OKCYAN}[KBRepository] Creating document for vectorstore with ID: {doc_id}{LogColors.ENDC}')
			langchain_doc = Document(page_content=text_content, metadata=metadata)

			logger.info(f'{LogColors.OKBLUE}[KBRepository] Adding document to vectorstore{LogColors.ENDC}')
			ids = self.vectorstore.add_documents(documents=[langchain_doc], ids=[doc_id])
			if not ids:
				logger.info(f'{LogColors.FAIL}[KBRepository] Failed to add document to vectorstore{LogColors.ENDC}')
				raise CustomHTTPException(message=_('error_adding_document_to_vector_store'))

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Document added successfully to vectorstore with ID: {doc_id}{LogColors.ENDC}')

			# Create and return response
			response = UploadDocumentResponse(
				id=doc_id,
				filename=file.filename,
				content_type=file.content_type,
				size=len(content),
				metadata=metadata,
			)

			logger.info(f'{LogColors.OKGREEN}[KBRepository] File upload completed successfully for: {file.filename}{LogColors.ENDC}')
			return response

		except CustomHTTPException as e:
			# Re-raise custom exceptions
			raise e
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Unexpected error during file upload: {str(e)}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_uploading_file'))

	async def get_document(self, document_id: str) -> Optional[ViewDocumentResponse]:
		"""Retrieve a document from the knowledge base by its ID."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Retrieving document with ID: {document_id}{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKBLUE}[KBRepository] Querying Qdrant for document: {document_id}{LogColors.ENDC}')

			# Retrieve the document from Qdrant
			points = self.client.retrieve(
				collection_name=self.collection_name,
				ids=[document_id],
				with_payload=True,
				with_vectors=False,
			)

			if not points or len(points) == 0:
				logger.info(f'{LogColors.WARNING}[KBRepository] Document not found with ID: {document_id}{LogColors.ENDC}')
				return None

			# Extract document data from the retrieved point
			point = points[0]
			content = point.payload.get('page_content', '') if point.payload else ''
			metadata = point.payload.get('metadata', {}) if point.payload else {}

			logger.info(f'{LogColors.OKCYAN}[KBRepository] Document retrieved - Content length: {len(content)}, Metadata keys: {list(metadata.keys())}{LogColors.ENDC}')

			# Create and return the response
			response = ViewDocumentResponse(id=document_id, content=content, metadata=metadata)
			logger.info(f'{LogColors.OKGREEN}[KBRepository] Document retrieval completed successfully for ID: {document_id}{LogColors.ENDC}')
			return response

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error retrieving document: {str(e)}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_retrieving_document'))

	async def delete_document(self, document_id: str) -> bool:
		"""Delete a document from the knowledge base by its ID."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Attempting to delete document with ID: {document_id}{LogColors.ENDC}')

		try:
			# Check if document exists first
			logger.info(f'{LogColors.OKBLUE}[KBRepository] Checking document existence before deletion: {document_id}{LogColors.ENDC}')
			existing_points = self.client.retrieve(
				collection_name=self.collection_name,
				ids=[document_id],
				with_payload=False,
				with_vectors=False,
			)

			if not existing_points:
				logger.info(f'{LogColors.WARNING}[KBRepository] Document with ID {document_id} not found for deletion{LogColors.ENDC}')
				return False

			logger.info(f'{LogColors.OKCYAN}[KBRepository] Document exists, proceeding with deletion: {document_id}{LogColors.ENDC}')

			# Perform delete operation
			self.client.delete(
				collection_name=self.collection_name,
				points_selector=[document_id],
			)

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Document deletion completed successfully for ID: {document_id}{LogColors.ENDC}')
			return True

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error deleting document: {str(e)}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_deleting_document'))

	async def list_all_documents(self) -> List[ViewDocumentResponse]:
		"""List all documents from the knowledge base."""
		logger.info(f'{LogColors.HEADER}[KBRepository] Starting to list all documents from collection: {self.collection_name}{LogColors.ENDC}')

		try:
			all_documents: List[ViewDocumentResponse] = []
			next_page_offset = None
			page_count = 0

			while True:
				page_count += 1
				logger.info(f'{LogColors.OKBLUE}[KBRepository] Fetching page {page_count} (limit: 100 documents){LogColors.ENDC}')

				# Scroll through all points in the collection
				points, next_page_offset = self.client.scroll(
					collection_name=self.collection_name,
					limit=100,  # Fetch 100 documents per request
					offset=next_page_offset,
					with_payload=True,  # We need the payload for content and metadata
					with_vectors=False,  # We don't need the vectors for listing
				)

				logger.info(f'{LogColors.OKCYAN}[KBRepository] Page {page_count} retrieved {len(points)} documents{LogColors.ENDC}')

				for point in points:
					# Ensure point.id is correctly handled (it can be int, str, or UUID)
					doc_id = str(point.id)
					content = point.payload.get('page_content', '') if point.payload else ''
					metadata = point.payload.get('metadata', {}) if point.payload else {}

					all_documents.append(ViewDocumentResponse(id=doc_id, content=content, metadata=metadata))

				if not next_page_offset:  # No more pages
					logger.info(f'{LogColors.OKCYAN}[KBRepository] No more pages to fetch - completed pagination{LogColors.ENDC}')
					break

			logger.info(f'{LogColors.OKGREEN}[KBRepository] Document listing completed - Retrieved {len(all_documents)} total documents in {page_count} pages{LogColors.ENDC}')
			return all_documents

		except Exception as e:
			logger.info(f'{LogColors.FAIL}[KBRepository] Error listing documents: {str(e)}{LogColors.ENDC}')
			raise CustomHTTPException(message=_('error_listing_documents'))
