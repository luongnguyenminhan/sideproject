"""Agentic RAG Knowledge Base routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.modules.agentic_rag.schemas.kb_schema import (
	AddDocumentsRequest,
	QueryRequest,
	UploadDocumentResponse,
	ViewDocumentResponse,
)
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

# Router for Agentic RAG knowledge base operations
route: APIRouter = APIRouter(prefix='/kb', tags=['Agentic RAG'])


def get_kb_repo(collection_id: str = 'global'):
	"""Dependency to get KB repository instance for specific collection."""
	return KBRepository(collection_name=collection_id)


@route.post('/collections/{collection_id}/documents', response_model=APIResponse)
@handle_exceptions
async def add_documents(
	collection_id: str,
	request: AddDocumentsRequest,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Add a list of documents to the specified collection."""
	ids: List[str] = await kb_repo.add_documents(request, collection_id=collection_id)
	print(f'[DEBUG] add_documents: Added document IDs to collection {collection_id}: {ids}')
	return APIResponse(
		error_code=0,
		message=_('documents_added_successfully'),
		data={'ids': ids, 'collection_id': collection_id},
	)


@route.post('/collections/{collection_id}/query', response_model=APIResponse)
@handle_exceptions
async def query_kb(
	collection_id: str,
	request: QueryRequest,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Query the specified collection for similar documents."""
	result = await kb_repo.query(request, collection_id=collection_id)
	print(f'[DEBUG] query_kb: Retrieved results from collection {collection_id}: {len(result.results)} documents')
	return APIResponse(
		error_code=0,
		message=_('query_successful'),
		data={'results': result, 'collection_id': collection_id},
	)


@route.post('/collections/{collection_id}/upload', response_model=APIResponse)
@handle_exceptions
async def upload_document(
	collection_id: str,
	file: UploadFile = File(...),
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Upload a file to the specified collection."""
	print(f'[DEBUG] upload_document: Uploading {file.filename} to collection {collection_id}')
	document_response: UploadDocumentResponse = await kb_repo.upload_file(file, collection_id=collection_id)
	print(f'[DEBUG] upload_document: File uploaded to collection {collection_id} with ID: {document_response.id}')
	return APIResponse(
		error_code=0,
		message=_('file_uploaded_successfully'),
		data={**document_response.model_dump(), 'collection_id': collection_id},
	)


@route.get('/collections/{collection_id}/documents/{document_id}', response_model=APIResponse)
@handle_exceptions
async def get_document(
	collection_id: str,
	document_id: str,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Retrieve a document from the specified collection."""
	print(f'[DEBUG] get_document: Retrieving document {document_id} from collection {collection_id}')
	document: Optional[ViewDocumentResponse] = await kb_repo.get_document(document_id, collection_id=collection_id)

	if document is None:
		raise NotFoundException(resource_name='document')

	return APIResponse(
		error_code=0,
		message=_('document_retrieved_successfully'),
		data={**document.model_dump(), 'collection_id': collection_id},
	)


@route.delete('/collections/{collection_id}/documents/{document_id}', response_model=APIResponse)
@handle_exceptions
async def delete_document(
	collection_id: str,
	document_id: str,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Delete a document from the specified collection."""
	print(f'[DEBUG] delete_document: Deleting document {document_id} from collection {collection_id}')

	existing_document = await kb_repo.get_document(document_id, collection_id=collection_id)
	if not existing_document:
		raise NotFoundException(resource_name='document')

	success = await kb_repo.delete_document(document_id, collection_id=collection_id)
	if not success:
		raise CustomHTTPException(message=_('error_deleting_document'))

	return APIResponse(
		error_code=0,
		message=_('document_deleted_successfully'),
		data={'collection_id': collection_id},
	)


@route.get('/collections/{collection_id}/documents', response_model=APIResponse)
@handle_exceptions
async def list_collection_documents(
	collection_id: str,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""List all documents in the specified collection."""
	print(f'[DEBUG] list_collection_documents: Listing documents from collection {collection_id}')
	documents: List[ViewDocumentResponse] = await kb_repo.list_all_documents(collection_id=collection_id)

	response_data = [doc.model_dump() for doc in documents]
	return APIResponse(
		error_code=0,
		message=_('documents_listed_successfully'),
		data={
			'documents': response_data,
			'collection_id': collection_id,
			'count': len(documents),
		},
	)


@route.get('/collections', response_model=APIResponse)
@handle_exceptions
async def list_collections(
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""List all available collections."""
	print('[DEBUG] list_collections: Listing all collections')
	collections = kb_repo.list_collections()

	return APIResponse(
		error_code=0,
		message=_('collections_listed_successfully'),
		data={'collections': collections, 'count': len(collections)},
	)
