import logging
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agentic_rag.dal.global_kb_dal import GlobalKBDAL
from app.exceptions.exception import (
	NotFoundException,
	ValidationException,
	CustomHTTPException,
)
from app.middleware.translation_manager import _
from app.utils.minio.minio_handler import minio_handler
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class GlobalKBRepo:
	def __init__(self, db: Session = Depends(get_db)):
		logger.info('[GlobalKBRepo] Initializing GlobalKBRepo')
		self.db = db
		logger.info('[GlobalKBRepo] Creating GlobalKBDAL instance')
		self.global_kb_dal = GlobalKBDAL(db)
		logger.info('[GlobalKBRepo] GlobalKBRepo initialization completed')

	def list_documents(self):
		logger.info('[GlobalKBRepo] Starting list_documents operation')
		try:
			logger.info('[GlobalKBRepo] Calling global_kb_dal.get_all()')
			documents = self.global_kb_dal.get_all()
			logger.info(f'[GlobalKBRepo] Retrieved {len(documents)} documents from DAL')
			return documents
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in list_documents: {str(e)}')
			raise

	def get_document(self, doc_id: str):
		logger.info(f'[GlobalKBRepo] Starting get_document operation for doc_id: {doc_id}')
		try:
			logger.info(f'[GlobalKBRepo] Calling global_kb_dal.get_by_id with doc_id: {doc_id}')
			doc = self.global_kb_dal.get_by_id(doc_id)

			if not doc:
				logger.warning(f'[GlobalKBRepo] Document not found with doc_id: {doc_id}')
				raise NotFoundException(_('document_not_found'))

			logger.info(f'[GlobalKBRepo] Successfully retrieved document: {doc.title if hasattr(doc, "title") else "Unknown"}')
			return doc
		except NotFoundException:
			logger.error(f'[GlobalKBRepo] Document not found exception for doc_id: {doc_id}')
			raise
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in get_document for doc_id {doc_id}: {str(e)}')
			raise

	def create_document(self, data):
		logger.info('[GlobalKBRepo] Starting create_document operation')
		logger.info(f'[GlobalKBRepo] Input data keys: {list(data.keys())}')

		try:
			# Nếu có trường 'file' (object_name), lấy URL và lưu vào source
			if data.get('file'):
				logger.info(f'[GlobalKBRepo] File object_name found: {data["file"]}')
				logger.info('[GlobalKBRepo] Getting file URL from MinIO')
				file_url = minio_handler.get_file_url(data['file'])
				logger.info(f'[GlobalKBRepo] Generated file URL: {file_url}')
				data['source'] = file_url
				logger.info('[GlobalKBRepo] Added file URL to source field')

			logger.info('[GlobalKBRepo] Calling global_kb_dal.create with processed data')
			document = self.global_kb_dal.create(data)
			self.db.commit()  # Commit the transaction
			logger.info('[GlobalKBRepo] Committed the transaction after document creation')
			logger.info('[GlobalKBRepo] Document created successfully, refreshing instance')
			self.db.refresh(document)  # Refresh to get the latest state from the database
			logger.info('[GlobalKBRepo] Document refreshed successfully')
			logger.info(f'[GlobalKBRepo] Successfully created document with ID: {document.id if hasattr(document, "id") else "Unknown"}')
			return document
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in create_document: {str(e)}')
			raise

	def update_document(self, doc_id: str, data):
		logger.info(f'[GlobalKBRepo] Starting update_document operation for doc_id: {doc_id}')
		logger.info(f'[GlobalKBRepo] Update data keys: {list(data.keys())}')

		try:
			logger.info(f'[GlobalKBRepo] Checking if document exists with doc_id: {doc_id}')
			doc = self.global_kb_dal.get_by_id(doc_id)
			if not doc:
				logger.warning(f'[GlobalKBRepo] Document not found for update with doc_id: {doc_id}')
				raise NotFoundException(_('document_not_found'))

			logger.info(f'[GlobalKBRepo] Document found for update: {doc.title if hasattr(doc, "title") else "Unknown"}')

			logger.info(f'[GlobalKBRepo] Calling global_kb_dal.update with doc_id: {doc_id}')
			updated_document = self.global_kb_dal.update(doc_id, data)
			logger.info(f'[GlobalKBRepo] Successfully updated document with doc_id: {doc_id}')
			return updated_document
		except NotFoundException:
			logger.error(f'[GlobalKBRepo] Document not found exception for update doc_id: {doc_id}')
			raise
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in update_document for doc_id {doc_id}: {str(e)}')
			raise

	def delete_document(self, doc_id: str):
		logger.info(f'[GlobalKBRepo] Starting delete_document operation for doc_id: {doc_id}')

		try:
			logger.info(f'[GlobalKBRepo] Checking if document exists with doc_id: {doc_id}')
			doc = self.global_kb_dal.get_by_id(doc_id)
			if not doc:
				logger.warning(f'[GlobalKBRepo] Document not found for deletion with doc_id: {doc_id}')
				raise NotFoundException(_('document_not_found'))

			logger.info(f'[GlobalKBRepo] Document found for deletion: {doc.title if hasattr(doc, "title") else "Unknown"}')

			# Nếu có file, xóa trên MinIO
			if doc.source:
				logger.info(f'[GlobalKBRepo] Document has source file: {doc.source}')
				logger.info('[GlobalKBRepo] Parsing source URL to extract object name')
				object_name = urlparse(doc.source).path.lstrip('/')
				logger.info(f'[GlobalKBRepo] Extracted object_name for MinIO deletion: {object_name}')

				logger.info(f'[GlobalKBRepo] Removing file from MinIO: {object_name}')
				minio_handler.remove_file(object_name)
				logger.info(f'[GlobalKBRepo] Successfully removed file from MinIO: {object_name}')
			else:
				logger.info(f'[GlobalKBRepo] Document has no source file to delete')

			logger.info(f'[GlobalKBRepo] Calling global_kb_dal.delete with doc_id: {doc_id}')
			result = self.global_kb_dal.delete(doc_id)
			logger.info(f'[GlobalKBRepo] Successfully deleted document from database with doc_id: {doc_id}')
			return result
		except NotFoundException:
			logger.error(f'[GlobalKBRepo] Document not found exception for deletion doc_id: {doc_id}')
			raise
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in delete_document for doc_id {doc_id}: {str(e)}')
			raise

	def search_documents(self, query: str, top_k: int = 10, category: str = None):
		logger.info(f'[GlobalKBRepo] Starting search_documents operation')
		logger.info(f"[GlobalKBRepo] Search parameters - query: '{query}', top_k: {top_k}, category: {category}")

		try:
			logger.info('[GlobalKBRepo] Calling global_kb_dal.search')
			results = self.global_kb_dal.search(query, top_k, category)
			logger.info(f'[GlobalKBRepo] Search completed, found {len(results)} results')
			logger.info(f'[GlobalKBRepo] Search results count by type: {type(results)}')
			return results
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in search_documents: {str(e)}')
			raise

	def stats(self):
		logger.info('[GlobalKBRepo] Starting stats operation')
		try:
			logger.info('[GlobalKBRepo] Calling global_kb_dal.stats()')
			stats_data = self.global_kb_dal.stats()
			logger.info(f'[GlobalKBRepo] Successfully retrieved stats: {stats_data}')
			return stats_data
		except Exception as e:
			logger.error(f'[GlobalKBRepo] Error in stats: {str(e)}')
			raise
