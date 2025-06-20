from app.core.base_model import RequestSchema, FilterableRequestSchema
from typing import List, Optional


class CreateGlobalKBRequest(RequestSchema):
	title: str
	file_name: Optional[str] = None
	file_type: Optional[str] = None
	category: Optional[str] = 'general'
	source: Optional[str] = None


class UpdateGlobalKBRequest(RequestSchema):
	title: Optional[str] = None
	file_name: Optional[str] = None
	file_type: Optional[str] = None
	category: Optional[str] = None
	source: Optional[str] = None
	indexed: Optional[bool] = None
	index_status: Optional[str] = None


class SearchGlobalKBRequest(RequestSchema):
	query: Optional[str] = None
	category: Optional[str] = None
	top_k: Optional[int] = 10
