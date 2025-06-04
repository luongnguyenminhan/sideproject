"""Agentic RAG LLM routes."""

from fastapi import APIRouter, Depends

from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.handlers import handle_exceptions
from app.modules.agentic_rag.schemas.rag_schema import RAGRequest
from app.modules.agentic_rag.repositories.rag_repo import RAGRepo

# Router for Agentic RAG operations
route: APIRouter = APIRouter(prefix='/rag', tags=['Agentic RAG'])


@route.post('/generate', response_model=APIResponse)
@handle_exceptions
async def generate_rag_response(
	request: RAGRequest,
	rag_repo: RAGRepo = Depends(),
) -> APIResponse:
	"""Generate an LLM response using RAG with document retrieval."""
	result = await rag_repo.generate(request)
	print(f'[DEBUG] generate_rag_response: Generated response with {len(result.sources)} sources')
	return APIResponse(error_code=0, message=_('response_generated_successfully'), data=result)
