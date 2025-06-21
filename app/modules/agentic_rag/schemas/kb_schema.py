# -*- coding: utf-8 -*-
"""
Pydantic models for Agentic RAG knowledge base operations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import RequestSchema


class DocumentModel(BaseModel):
	"""Model representing a document to be added to the knowledge base."""

	id: str = Field(..., description='Unique identifier for the document')
	content: str = Field(..., description='Content of the document')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata for the document')


class AddDocumentsRequest(RequestSchema):
	"""Schema for adding documents to the knowledge base."""

	documents: List[DocumentModel] = Field(..., description='List of documents to add to the knowledge base')


class QueryRequest(RequestSchema):
	"""Schema for querying the knowledge base."""

	query: str = Field(..., description='Query text to search in the knowledge base')
	top_k: int = Field(default=5, description='Number of top similar documents to retrieve')


class QueryResponseItem(BaseModel):
	"""Item representing a single query result."""

	id: Optional[str] = Field(None, description='Identifier of the matched document')
	content: Optional[str] = Field(None, description='Content of the matched document')
	score: Optional[float] = Field(None, description='Similarity score of the match')
	metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description='Metadata of the matched document')


class QueryResponse(BaseModel):
	"""Schema for query response containing multiple results."""

	results: List[QueryResponseItem] = Field(..., description='List of query response items')


class UploadDocumentResponse(BaseModel):
	"""Response model for file upload to the knowledge base."""

	id: str = Field(..., description='Unique identifier for the uploaded document')
	filename: str = Field(..., description='Name of the uploaded file')
	content_type: Optional[str] = Field(None, description='Content type of the uploaded file')
	size: Optional[int] = Field(None, description='Size of the uploaded file in bytes')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata for the document')


class ViewDocumentResponse(BaseModel):
	"""Response model for viewing a document from the knowledge base."""

	id: str = Field(..., description='Unique identifier for the document')
	content: str = Field(..., description='Content of the document')
	metadata: Dict[str, Any] = Field(default_factory=dict, description='Additional metadata for the document')
