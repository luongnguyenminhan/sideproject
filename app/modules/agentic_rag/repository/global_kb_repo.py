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


class GlobalKBRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.global_kb_dal = GlobalKBDAL(db)

	def list_documents(self):
		return self.global_kb_dal.get_all()

	def get_document(self, doc_id: str):
		doc = self.global_kb_dal.get_by_id(doc_id)
		if not doc:
			raise NotFoundException(_('document_not_found'))
		return doc

	def create_document(self, data):
		# Nếu có trường 'file' (object_name), lấy URL và lưu vào source
		if data.get('file'):
			file_url = minio_handler.get_file_url(data['file'])
			data['source'] = file_url
		return self.global_kb_dal.create(data)

	def update_document(self, doc_id: str, data):
		doc = self.global_kb_dal.get_by_id(doc_id)
		if not doc:
			raise NotFoundException(_('document_not_found'))
		return self.global_kb_dal.update(doc_id, data)

	def delete_document(self, doc_id: str):
		doc = self.global_kb_dal.get_by_id(doc_id)
		if not doc:
			raise NotFoundException(_('document_not_found'))
		# Nếu có file, xóa trên MinIO
		if doc.source:
			object_name = urlparse(doc.source).path.lstrip('/')
			minio_handler.remove_file(object_name)
		return self.global_kb_dal.delete(doc_id)

	def search_documents(self, query: str, top_k: int = 10, category: str = None):
		return self.global_kb_dal.search(query, top_k, category)

	def stats(self):
		return self.global_kb_dal.stats()
