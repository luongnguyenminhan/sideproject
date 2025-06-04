"""
Version 1 of the Agentic RAG API routes.
"""

from app.modules.agentic_rag.routes.v1.kb_route import route as kb_route
from app.modules.agentic_rag.routes.v1.rag_route import route as rag_route
from app.modules.agentic_rag.routes.v1.agent_route import route as agent_route

__all__ = [
	'kb_route',
	'rag_route',
	'agent_route',
]
