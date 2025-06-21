"""Agentic RAG Agent routes."""

from fastapi import APIRouter, Depends

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import APIResponse

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.handlers import handle_exceptions
from ...schemas.rag_schema import RAGRequest
from ...agent.rag_graph import RAGAgentGraph
from ...repository.kb_repo import KBRepository
from ...core.config import DEFAULT_COLLECTION

# Router for Agentic RAG agent operations
route: APIRouter = APIRouter(prefix='/agent', tags=['Agentic RAG'])


def get_kb_repo(collection_id: str = DEFAULT_COLLECTION):
	"""Dependency to get KB repository instance for specific collection."""
	return KBRepository(collection_name=collection_id)


@route.post('/collections/{collection_id}/answer', response_model=APIResponse)
@handle_exceptions
async def answer_query_collection(
	collection_id: str,
	request: RAGRequest,
	kb_repo: KBRepository = Depends(lambda: KBRepository()),
) -> APIResponse:
	"""Generate a response using a LangGraph-based agent with knowledge base for specific collection."""
	# Initialize the agent with our KB repository for the specific collection
	agent = RAGAgentGraph(kb_repo=kb_repo, collection_id=collection_id)

	# Process the query
	result = await agent.answer_query(request.query, collection_id=collection_id)

	print(f'[DEBUG] answer_query_collection: Generated response for collection {collection_id} with {len(result.get("sources", []))} sources')
	return APIResponse(
		error_code=0,
		message=_('response_generated_successfully'),
		data={**result, 'collection_id': collection_id},
	)


@route.post('/answer', response_model=APIResponse)
@handle_exceptions
async def answer_query(
	request: RAGRequest,
	kb_repo: KBRepository = Depends(get_kb_repo),
) -> APIResponse:
	"""Generate a response using a LangGraph-based agent with knowledge base (default collection)."""
	# Initialize the agent with our KB repository
	agent = RAGAgentGraph(kb_repo=kb_repo)

	# Process the query
	result = await agent.answer_query(request.query)

	print(f'[DEBUG] answer_query: Generated response with {len(result.get("sources", []))} sources')
	return APIResponse(error_code=0, message=_('response_generated_successfully'), data=result)
