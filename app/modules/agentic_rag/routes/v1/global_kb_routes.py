import logging
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.modules.agentic_rag.repository.global_kb_repo import GlobalKBRepo
from app.modules.agentic_rag.schemas.global_kb_request import (
	CreateGlobalKBRequest,
	UpdateGlobalKBRequest,
	SearchGlobalKBRequest,
)
from app.modules.agentic_rag.schemas.global_kb_response import GlobalKBResponse
from app.utils.minio.minio_handler import minio_handler

logger = logging.getLogger(__name__)

route = APIRouter(prefix='/global-kb', tags=['global-kb-admin'])


@route.get('/', response_model=APIResponse)
@handle_exceptions
async def list_documents(repo: GlobalKBRepo = Depends()):
	logger.info('[GlobalKBRoutes] Starting list_documents request')
	try:
		logger.debug('[GlobalKBRoutes] Calling repo.list_documents()')
		docs = repo.list_documents()
		logger.info(f'[GlobalKBRoutes] Successfully retrieved {len(docs)} documents')

		logger.debug('[GlobalKBRoutes] Converting documents to response format')
		response_data = [GlobalKBResponse.model_validate(doc) for doc in docs]
		logger.debug(f'[GlobalKBRoutes] Converted {len(response_data)} documents to response format')

		logger.info('[GlobalKBRoutes] Completed list_documents request successfully')
		return APIResponse(
			error_code=0,
			message=_('success'),
			data=response_data,
		)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in list_documents: {str(e)}')
		raise


@route.get('/{doc_id}', response_model=APIResponse)
@handle_exceptions
async def get_document(doc_id: str, repo: GlobalKBRepo = Depends()):
	logger.info(f'[GlobalKBRoutes] Starting get_document request for doc_id: {doc_id}')
	try:
		logger.debug(f'[GlobalKBRoutes] Calling repo.get_document with doc_id: {doc_id}')
		doc = repo.get_document(doc_id)
		logger.info(f'[GlobalKBRoutes] Successfully retrieved document: {doc.title if hasattr(doc, "title") else "Unknown"}')

		logger.debug('[GlobalKBRoutes] Converting document to response format')
		response_data = GlobalKBResponse.model_validate(doc)
		logger.debug('[GlobalKBRoutes] Successfully converted document to response format')

		logger.info(f'[GlobalKBRoutes] Completed get_document request for doc_id: {doc_id}')
		return APIResponse(error_code=0, message=_('success'), data=response_data)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in get_document for doc_id {doc_id}: {str(e)}')
		raise


@route.post('/', response_model=APIResponse)
@handle_exceptions
async def create_document(request: CreateGlobalKBRequest, repo: GlobalKBRepo = Depends()):
	logger.info('[GlobalKBRoutes] Starting create_document request')
	try:
		logger.debug(f'[GlobalKBRoutes] Request data: {request.model_dump()}')
		request_data = request.model_dump()
		logger.debug(f'[GlobalKBRoutes] Dumped request data keys: {list(request_data.keys())}')

		logger.debug('[GlobalKBRoutes] Calling repo.create_document')
		doc = repo.create_document(request_data)
		logger.info(f'[GlobalKBRoutes] Successfully created document with ID: {doc.id if hasattr(doc, "id") else "Unknown"}')

		logger.debug('[GlobalKBRoutes] Converting created document to response format')
		response_data = GlobalKBResponse.model_validate(doc)
		logger.debug('[GlobalKBRoutes] Successfully converted created document to response format')

		logger.info('[GlobalKBRoutes] Completed create_document request successfully')
		return APIResponse(error_code=0, message=_('success'), data=response_data)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in create_document: {str(e)}')
		raise


@route.put('/{doc_id}', response_model=APIResponse)
@handle_exceptions
async def update_document(doc_id: str, request: UpdateGlobalKBRequest, repo: GlobalKBRepo = Depends()):
	logger.info(f'[GlobalKBRoutes] Starting update_document request for doc_id: {doc_id}')
	try:
		logger.debug(f'[GlobalKBRoutes] Request data: {request.model_dump(exclude_unset=True)}')
		request_data = request.model_dump(exclude_unset=True)
		logger.debug(f'[GlobalKBRoutes] Update data keys: {list(request_data.keys())}')

		logger.debug(f'[GlobalKBRoutes] Calling repo.update_document for doc_id: {doc_id}')
		doc = repo.update_document(doc_id, request_data)
		logger.info(f'[GlobalKBRoutes] Successfully updated document: {doc.title if hasattr(doc, "title") else "Unknown"}')

		logger.debug('[GlobalKBRoutes] Converting updated document to response format')
		response_data = GlobalKBResponse.model_validate(doc)
		logger.debug('[GlobalKBRoutes] Successfully converted updated document to response format')

		logger.info(f'[GlobalKBRoutes] Completed update_document request for doc_id: {doc_id}')
		return APIResponse(error_code=0, message=_('success'), data=response_data)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in update_document for doc_id {doc_id}: {str(e)}')
		raise


@route.delete('/{doc_id}', response_model=APIResponse)
@handle_exceptions
async def delete_document(doc_id: str, repo: GlobalKBRepo = Depends()):
	logger.info(f'[GlobalKBRoutes] Starting delete_document request for doc_id: {doc_id}')
	try:
		logger.debug(f'[GlobalKBRoutes] Calling repo.delete_document for doc_id: {doc_id}')
		repo.delete_document(doc_id)
		logger.info(f'[GlobalKBRoutes] Successfully deleted document with doc_id: {doc_id}')

		logger.info(f'[GlobalKBRoutes] Completed delete_document request for doc_id: {doc_id}')
		return APIResponse(error_code=0, message=_('success'), data=None)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in delete_document for doc_id {doc_id}: {str(e)}')
		raise


@route.post('/search', response_model=APIResponse)
@handle_exceptions
async def search_documents(request: SearchGlobalKBRequest, repo: GlobalKBRepo = Depends()):
	logger.info(f'[GlobalKBRoutes] Starting search_documents request')
	try:
		logger.debug(f"[GlobalKBRoutes] Search query: '{request.query}', top_k: {request.top_k}, category: {request.category}")

		logger.debug('[GlobalKBRoutes] Calling repo.search_documents')
		docs = repo.search_documents(request.query, request.top_k, request.category)
		logger.info(f'[GlobalKBRoutes] Search returned {len(docs)} documents')

		logger.debug('[GlobalKBRoutes] Converting search results to response format')
		response_data = [GlobalKBResponse.model_validate(doc) for doc in docs]
		logger.debug(f'[GlobalKBRoutes] Converted {len(response_data)} search results to response format')

		logger.info(f'[GlobalKBRoutes] Completed search_documents request with {len(response_data)} results')
		return APIResponse(
			error_code=0,
			message=_('success'),
			data=response_data,
		)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in search_documents: {str(e)}')
		raise


@route.get('/stats', response_model=APIResponse)
@handle_exceptions
async def get_stats(repo: GlobalKBRepo = Depends()):
	logger.info('[GlobalKBRoutes] Starting get_stats request')
	try:
		logger.debug('[GlobalKBRoutes] Calling repo.stats()')
		stats = repo.stats()
		logger.info(f'[GlobalKBRoutes] Successfully retrieved stats: {stats}')

		logger.info('[GlobalKBRoutes] Completed get_stats request successfully')
		return APIResponse(error_code=0, message=_('success'), data=stats)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in get_stats: {str(e)}')
		raise


@route.post('/upload', response_model=APIResponse)
@handle_exceptions
async def upload_global_kb_file(
	file: UploadFile = File(...),
	title: str = None,
	category: str = 'general',
	repo: GlobalKBRepo = Depends(),
):
	"""
	Upload file lên MinIO và index luôn vào Global KB vector database
	"""
	logger.info(f'[GlobalKBRoutes] Starting upload_global_kb_file request')
	logger.debug(f'[GlobalKBRoutes] File details - filename: {file.filename}, content_type: {file.content_type}, title: {title}, category: {category}')

	try:
		# 1. Upload file lên MinIO
		logger.debug('[GlobalKBRoutes] Starting file upload to MinIO')
		object_name = await minio_handler.upload_fastapi_file(file, meeting_id='global_kb', file_type='document')
		logger.info(f'[GlobalKBRoutes] Successfully uploaded file to MinIO with object_name: {object_name}')

		logger.debug(f'[GlobalKBRoutes] Getting file URL from MinIO for object_name: {object_name}')
		file_url = minio_handler.get_file_url(object_name)
		logger.info(f'[GlobalKBRoutes] Generated file URL: {file_url}')

		# 2. Tạo record trong database (chưa index)
		logger.debug('[GlobalKBRoutes] Creating database record for uploaded file')
		doc_data = {
			'title': title or file.filename,
			'file_name': file.filename,
			'file_type': file.content_type,
			'category': category,
			'source': file_url,
			'indexed': False,
			'index_status': 'pending',
		}
		logger.debug(f'[GlobalKBRoutes] Document data prepared: {doc_data}')

		logger.debug('[GlobalKBRoutes] Calling repo.create_document')
		doc = repo.create_document(doc_data)
		logger.info(f'[GlobalKBRoutes] Successfully created document record with ID: {doc.id if hasattr(doc, "id") else "Unknown"}')

		# 3. Extract text và index vào vector database
		logger.info('[GlobalKBRoutes] Starting text extraction and indexing process')
		try:
			# Reset file pointer để đọc lại content
			await file.seek(0)
			file_content = await file.read()
			logger.debug(f'[GlobalKBRoutes] Read {len(file_content)} bytes from uploaded file')

			# Extract text content từ file
			from app.modules.chat.services.file_extraction_service import (
				file_extraction_service,
			)

			logger.debug('[GlobalKBRoutes] Calling file_extraction_service.extract_text_from_file')
			extraction_result = file_extraction_service.extract_text_from_file(
				file_content=file_content,
				file_type=file.content_type or 'application/octet-stream',
				file_name=file.filename or 'unknown_file',
			)

			logger.info(f'[GlobalKBRoutes] Text extraction result - Success: {extraction_result["extraction_success"]}, Content length: {extraction_result["char_count"]}')

			if extraction_result['extraction_success'] and extraction_result['content'].strip():
				extracted_content = extraction_result['content']
				logger.info(f'[GlobalKBRoutes] Successfully extracted text content ({len(extracted_content)} characters)')

				# Index vào Global KB vector database
				logger.debug('[GlobalKBRoutes] Starting indexing to Global KB vector database')
				from app.modules.agentic_rag.services.global_kb_service import (
					GlobalKBService,
				)

				# Initialize service và index document
				global_kb_service = GlobalKBService(repo.db)

				# Prepare document data for indexing
				documents_data = [
					{
						'id': str(doc.id),
						'title': doc.title,
						'content': extracted_content,
						'category': doc.category,
						'tags': [],
						'source': doc.source,
						'file_name': doc.file_name,
						'file_type': doc.file_type,
					}
				]

				logger.debug('[GlobalKBRoutes] Calling global_kb_service.index_admin_documents')
				indexing_result = await global_kb_service.index_admin_documents(documents_data)
				logger.info(f'[GlobalKBRoutes] Indexing result: {indexing_result}')

				# Update document status based on indexing result
				if indexing_result['successful_docs']:
					logger.info('[GlobalKBRoutes] Successfully indexed document, updating status')
					repo.update_document(str(doc.id), {'indexed': True, 'index_status': 'success'})
				else:
					logger.warning('[GlobalKBRoutes] Failed to index document, updating status')
					repo.update_document(str(doc.id), {'indexed': False, 'index_status': 'failed'})

			else:
				logger.warning(f'[GlobalKBRoutes] Text extraction failed: {extraction_result.get("extraction_error", "Unknown error")}')
				# Update status to failed
				repo.update_document(str(doc.id), {'indexed': False, 'index_status': 'failed'})

		except Exception as e:
			logger.error(f'[GlobalKBRoutes] Error during indexing process: {str(e)}')
			# Update status to failed
			repo.update_document(str(doc.id), {'indexed': False, 'index_status': 'failed'})

		# 4. Trả về response
		logger.debug('[GlobalKBRoutes] Converting uploaded document to response format')
		# Get updated document
		updated_doc = repo.get_document(str(doc.id))
		response_data = GlobalKBResponse.model_validate(updated_doc)
		logger.debug('[GlobalKBRoutes] Successfully converted uploaded document to response format')

		logger.info(f'[GlobalKBRoutes] Completed upload_global_kb_file request successfully')
		api_response = APIResponse(error_code=0, message=_('success'), data=response_data)
		return api_response

	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in upload_global_kb_file: {str(e)}')
		raise


@route.delete('/file/{doc_id}', response_model=APIResponse)
@handle_exceptions
async def delete_global_kb_file(doc_id: str, repo: GlobalKBRepo = Depends()):
	logger.info(f'[GlobalKBRoutes] Starting delete_global_kb_file request for doc_id: {doc_id}')
	try:
		logger.debug(f'[GlobalKBRoutes] Getting document details for doc_id: {doc_id}')
		doc = repo.get_document(doc_id)
		logger.info(f'[GlobalKBRoutes] Retrieved document: {doc.title if hasattr(doc, "title") else "Unknown"}')

		if doc and doc.source:
			logger.debug(f'[GlobalKBRoutes] Document has source file: {doc.source}')
			# Xóa file trên MinIO nếu có
			from urllib.parse import urlparse

			logger.debug('[GlobalKBRoutes] Parsing source URL to get object name')
			object_name = urlparse(doc.source).path.lstrip('/')
			logger.info(f'[GlobalKBRoutes] Extracted object_name for deletion: {object_name}')

			logger.debug(f'[GlobalKBRoutes] Removing file from MinIO: {object_name}')
			minio_handler.remove_file(object_name)
			logger.info(f'[GlobalKBRoutes] Successfully removed file from MinIO: {object_name}')
		else:
			logger.warning(f'[GlobalKBRoutes] Document {doc_id} has no source file or document not found')

		logger.debug(f'[GlobalKBRoutes] Deleting document from database: {doc_id}')
		repo.delete_document(doc_id)
		logger.info(f'[GlobalKBRoutes] Successfully deleted document from database: {doc_id}')

		logger.info(f'[GlobalKBRoutes] Completed delete_global_kb_file request for doc_id: {doc_id}')
		return APIResponse(error_code=0, message=_('success'), data=None)
	except Exception as e:
		logger.error(f'[GlobalKBRoutes] Error in delete_global_kb_file for doc_id {doc_id}: {str(e)}')
		raise
