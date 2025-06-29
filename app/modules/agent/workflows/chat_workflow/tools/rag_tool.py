"""
RAG Tool for Chat Agent - Simplified version as a proper LangChain tool
This tool provides RAG functionality that can be called by the agent when needed
"""

import logging
import json
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@tool
async def rag_search(conversation_id: str, query: str, top_k: int = 5) -> str:
	"""
	Search for relevant information using RAG (Retrieval Augmented Generation).
	
	Use this tool when you need to:
	- Find information from uploaded documents or files
	- Search conversation history or context
	- Get background information about the user or conversation
	- Retrieve relevant CV or profile data
	
	Args:
		conversation_id: ID of the current conversation
		query: What to search for
		top_k: Number of results to return (default: 5)
		
	Returns:
		JSON string containing search results and context
	"""
	logger.info(f'[rag_search] Searching for: "{query}" in conversation: {conversation_id}')
	
	try:
		# Placeholder implementation - will be enhanced with actual RAG
		results = {
			'query': query,
			'conversation_id': conversation_id,
			'results': [],
			'context': '',
			'sources': []
		}
		
		# Try to get conversation-specific context
		conv_context = await _search_conversation_context(conversation_id, query, top_k)
		if conv_context:
			results['results'].extend(conv_context)
			results['context'] += f"Conversation Context: {' '.join([r.get('content', '') for r in conv_context])}\n\n"
		
		# Try to get global knowledge
		global_context = await _search_global_knowledge(query, top_k)
		if global_context:
			results['results'].extend(global_context)
			results['context'] += f"Global Knowledge: {' '.join([r.get('content', '') for r in global_context])}"
		
		logger.info(f'[rag_search] Found {len(results["results"])} total results')
		
		if results['context']:
			return f"🔍 RAG Search Results:\n\n{results['context']}\n\nSources: {len(results['results'])} documents found"
		else:
			return "🔍 No relevant information found in the knowledge base for this query."
			
	except Exception as e:
		logger.error(f'[rag_search] Error in RAG search: {str(e)}')
		return f"❌ RAG search failed: {str(e)}"


async def _search_conversation_context(conversation_id: str, query: str, top_k: int) -> list:
	"""Search conversation-specific context (files, CV data, etc.)"""
	try:
		# This would be replaced with actual conversation RAG implementation
		logger.info(f"[_search_conversation_context] Searching conversation {conversation_id} for: {query}")
		
		# Placeholder - check for CV-related keywords
		cv_keywords = ['cv', 'resume', 'experience', 'skill', 'education', 'work', 'job', 'career']
		if any(keyword in query.lower() for keyword in cv_keywords):
			return [{
				'content': f'CV and profile information for conversation {conversation_id}',
				'source': 'cv_data',
				'relevance': 0.9
			}]
		
		return []
		
	except Exception as e:
		logger.error(f'[_search_conversation_context] Error: {str(e)}')
		return []


async def _search_global_knowledge(query: str, top_k: int) -> list:
	"""Search global knowledge base"""
	try:
		# This would be replaced with actual global KB implementation
		logger.info(f"[_search_global_knowledge] Searching global KB for: {query}")
		
		# Placeholder - provide generic career advice for career-related queries
		career_keywords = ['cv', 'interview', 'job', 'career', 'skill', 'experience', 'resume']
		if any(keyword in query.lower() for keyword in career_keywords):
			return [{
				'content': 'General career and CV best practices: Focus on achievements, use action verbs, tailor to job requirements, include relevant skills and experience.',
				'source': 'global_knowledge',
				'relevance': 0.8
			}]
		
		return []
		
	except Exception as e:
		logger.error(f'[_search_global_knowledge] Error: {str(e)}')
		return []


# Factory function for backward compatibility with the old RAGTool class
def RAGTool(db_session: Session):
	"""Factory function that returns the rag_search tool for backward compatibility"""
	return rag_search