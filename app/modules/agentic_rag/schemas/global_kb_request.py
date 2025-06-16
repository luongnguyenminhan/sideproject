from app.core.base_model import RequestSchema, FilterableRequestSchema
from typing import List, Optional

class CreateGlobalKBRequest(RequestSchema):
    title: str
    content: str
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []
    source: Optional[str] = None

class UpdateGlobalKBRequest(RequestSchema):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None

class SearchGlobalKBRequest(FilterableRequestSchema):
    query: Optional[str] = None
    category: Optional[str] = None
    top_k: Optional[int] = 10
