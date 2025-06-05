"""
Simple calculation tools for basic workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool
from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

logger = logging.getLogger(__name__)


@tool(return_direct=False)
def add(a: float, b: float) -> float:
	"""Add two numbers together."""
	return a + b


@tool(return_direct=False)
def subtract(a: float, b: float) -> float:
	"""Subtract second number from first number."""
	return a - b


@tool(return_direct=False)
def multiply(a: float, b: float) -> float:
	"""Multiply two numbers together."""
	return a * b


@tool(return_direct=False)
def divide(a: float, b: float) -> float:
	"""Divide first number by second number."""
	if b == 0:
		return float('inf')
	return a / b


@tool(return_direct=False)
async def answer_query_collection(query: str, conversation_id: str = 'global') -> str:
	"""Answer a query from the specified knowledge base collection using RAG.

	Args:
	        query: The question or query to answer
	        conversation_id: The conversation ID which corresponds to the collection ID to search in (defaults to "global")

	Returns:
	        A comprehensive answer with sources from the knowledge base
	"""
	logger.info(f"[RAGTool] Processing RAG query for conversation '{conversation_id}': {query}")

	try:
		# Initialize RAG agent for the specified collection (using conversation_id as collection_id)
		kb_repo = KBRepository(collection_name=conversation_id)
		rag_agent = RAGAgentGraph(kb_repo=kb_repo, collection_id=conversation_id)

		# Process the query
		result = await rag_agent.answer_query(query=query, collection_id=conversation_id)

		# Format the response with answer and sources
		answer = result.get('answer', 'No answer found')
		sources = result.get('sources', [])

		# Create a formatted response that includes source information
		formatted_response = answer

		if sources:
			formatted_response += '\n\n📚 Sources:'
			for i, source in enumerate(sources, 1):
				source_info = f'\n{i}. Document ID: {source.get("id", "Unknown")}'
				if 'metadata' in source and 'source' in source['metadata']:
					source_info += f' (File: {source["metadata"]["source"]})'
				formatted_response += source_info

		logger.info(f"[RAGTool] RAG query completed for conversation '{conversation_id}' with {len(sources)} sources")
		return formatted_response

	except Exception as e:
		logger.error(f"[RAGTool] Error processing RAG query for conversation '{conversation_id}': {str(e)}")
		return f'I apologize, but I encountered an error while searching the knowledge base: {str(e)}'


@tool(return_direct=False)
async def search_knowledge_base(query: str, collection_id: str = 'global', top_k: int = 3) -> str:
	"""Search the knowledge base for information related to the query.

	Args:
	        query: The search query
	        collection_id: The collection to search in (defaults to "global")
	        top_k: Number of top results to return (defaults to 3)

	Returns:
	        Relevant information from the knowledge base
	"""
	logger.info(f"[SearchTool] Searching knowledge base in collection '{collection_id}' for: {query}")

	try:
		from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

		# Initialize KB repository
		kb_repo = KBRepository(collection_name=collection_id)

		# Search for documents
		query_request = QueryRequest(query=query, top_k=top_k)
		results = await kb_repo.query(query_request, collection_id=collection_id)

		if not results.results:
			return f"No relevant information found in collection '{collection_id}' for your query."

		# Format the search results
		formatted_results = f"Found {len(results.results)} relevant documents in collection '{collection_id}':\n\n"

		for i, result in enumerate(results.results, 1):
			content_preview = result.content[:200] + '...' if len(result.content) > 200 else result.content
			formatted_results += f'{i}. Score: {result.score:.3f}\n'
			formatted_results += f'   Content: {content_preview}\n'
			if result.metadata and 'source' in result.metadata:
				formatted_results += f'   Source: {result.metadata["source"]}\n'
			formatted_results += '\n'

		logger.info(f"[SearchTool] Found {len(results.results)} documents in collection '{collection_id}'")
		return formatted_results

	except Exception as e:
		logger.error(f'[SearchTool] Error searching knowledge base: {str(e)}')
		return f'Error searching knowledge base: {str(e)}'


# List of available tools
tools = [
	add,
	subtract,
	multiply,
	divide,
	answer_query_collection,
	search_knowledge_base,
]


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get tools for the workflow"""
	return tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
	"""Get tool definitions for model binding"""
	# Return tool schema for model binding
	return [tool for tool in tools]
