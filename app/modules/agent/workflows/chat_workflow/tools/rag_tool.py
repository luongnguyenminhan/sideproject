"""
RAG Tool for Chat Agent
Simplified RAG system với Global Knowledge Base + Conversation-specific Knowledge Base
"""

import logging
import json
from typing import Dict, Any, Optional, List, Literal
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class RAGRoute(BaseModel):
    """Schema for routing decisions"""

    routing_decision: Literal["global_only", "conversation_only", "both", "none"] = (
        Field(description="Which knowledge base(s) to query")
    )
    query_type: Literal["factual", "conversational", "technical", "personal"] = Field(
        description="Type of user query"
    )
    enhanced_query: str = Field(description="Enhanced query for better retrieval")


class RAGInput(BaseModel):
    """Input schema for RAG tool"""

    conversation_id: str = Field(description="ID của conversation")
    user_id: str = Field(description="ID của user")
    query: str = Field(description="User query để search")
    top_k: int = Field(default=5, description="Số lượng kết quả trả về mỗi source")


class RAGTool(BaseTool):
    """Tool thực hiện RAG với intelligent routing"""

    name: str = "rag_retrieval"
    description: str = """
    Advanced RAG system với intelligent routing.
    - Global Knowledge Base: Kiến thức chung agent cần biết
    - Conversation Knowledge Base: Kiến thức specific cho conversation (CV, files uploaded)
    
    Tool sẽ:
    1. Phân tích query để quyết định route
    2. Search các knowledge base phù hợp
    3. Kết hợp và rank results
    4. Trả về context đã được optimize
    
    Input: conversation_id, user_id, query, top_k
    """

    db_session: Session = Field(exclude=True)
    _router_llm: Any = PrivateAttr()
    _router_prompt: Any = PrivateAttr()
    _router_chain: Any = PrivateAttr()

    def __init__(self, db_session: Session, **kwargs):
        super().__init__(db_session=db_session, **kwargs)

        # Initialize router LLM for intelligent routing
        self._router_llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", temperature=0.1
        )

        # Router prompt for query analysis and routing
        self._router_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Bạn là AI Router chuyên phân tích query và quyết định routing cho RAG system.

KNOWLEDGE BASES:
1. GLOBAL KB: Kiến thức chung, facts, technical knowledge, best practices
2. CONVERSATION KB: Thông tin specific cho conversation (CV data, uploaded files, personal context)

ROUTING DECISIONS:
- "global_only": Query về general knowledge, facts, how-to, technical questions
- "conversation_only": Query về personal info, CV details, uploaded files
- "both": Query cần kết hợp cả 2 sources
- "none": Query không cần retrieval (greeting, simple responses)

QUERY TYPES:
- "factual": Questions about facts, definitions, general knowledge
- "conversational": Personal questions, context-specific queries
- "technical": Technical how-to, coding, implementation questions
- "personal": Questions about user's CV, experience, skills

Phân tích query và trả về routing decision + enhanced query để improve retrieval.
""",
                ),
                ("human", "Query: {query}\\n\\nPhân tích và quyết định routing:"),
            ]
        )

        self._router_chain = (
            self._router_prompt | self._router_llm.with_structured_output(RAGRoute)
        )

    def _run(
        self, conversation_id: str, user_id: str, query: str, top_k: int = 5
    ) -> str:
        """
        Execute RAG retrieval với intelligent routing

        Args:
            conversation_id: ID của conversation
            user_id: ID của user
            query: User query
            top_k: Number of results per source

        Returns:
            JSON string với retrieved context
        """
        try:
            logger.info(
                f'[RAG] Processing query: "{query[:100]}..." for conversation: {conversation_id}'
            )

            # 1. Intelligent routing
            route_decision = self._route_query(query)
            logger.info(
                f"[RAG] Routing decision: {route_decision.routing_decision}, Query type: {route_decision.query_type}"
            )

            # 2. Retrieve from appropriate knowledge bases
            results = self._execute_retrieval(
                conversation_id=conversation_id,
                user_id=user_id,
                route_decision=route_decision,
                top_k=top_k,
            )

            # 3. Combine and rank results
            final_context = self._combine_and_rank_results(results, route_decision)

            logger.info(
                f'[RAG] Retrieved {len(final_context.get("sources", []))} total sources'
            )

            return json.dumps(final_context, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[RAG] Error in RAG retrieval: {str(e)}")
            return json.dumps(
                {
                    "error": str(e),
                    "sources": [],
                    "routing_decision": "none",
                    "message": "Lỗi trong quá trình tìm kiếm kiến thức",
                },
                ensure_ascii=False,
            )

    def _route_query(self, query: str) -> RAGRoute:
        """Phân tích query và quyết định routing"""
        try:
            route_decision = self._router_chain.invoke({"query": query})
            logger.info(
                f"[RAG Router] Decision: {route_decision.routing_decision}, Enhanced query: {route_decision.enhanced_query}"
            )
            return route_decision
        except Exception as e:
            logger.error(f"[RAG Router] Error in routing: {str(e)}")
            # Fallback routing
            return RAGRoute(
                routing_decision="global_only",
                query_type="factual",
                enhanced_query=query,
            )

    def _execute_retrieval(
        self, conversation_id: str, user_id: str, route_decision: RAGRoute, top_k: int
    ) -> Dict[str, List[Dict]]:
        """Execute retrieval từ các knowledge bases theo routing decision"""
        results = {"global": [], "conversation": []}

        try:
            # Global Knowledge Base retrieval
            if route_decision.routing_decision in ["global_only", "both"]:
                global_results = self._search_global_kb(
                    route_decision.enhanced_query, top_k
                )
                results["global"] = global_results
                logger.info(
                    f"[RAG] Retrieved {len(global_results)} results from Global KB"
                )

            # Conversation Knowledge Base retrieval
            if route_decision.routing_decision in ["conversation_only", "both"]:
                conv_results = self._search_conversation_kb(
                    conversation_id, user_id, route_decision.enhanced_query, top_k
                )
                results["conversation"] = conv_results
                logger.info(
                    f"[RAG] Retrieved {len(conv_results)} results from Conversation KB"
                )

        except Exception as e:
            logger.error(f"[RAG] Error in retrieval execution: {str(e)}")

        return results

    def _search_global_kb(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search Global Knowledge Base"""
        try:
            # TODO: Import from outside module - needs to be decided later
            # from app.modules.agentic_rag.repository.kb_repo import KBRepository
            # from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

            # Placeholder implementation - replace with actual search
            logger.warning("Global KB search not implemented - external dependency")
            return []

            # Commented out external dependency:
            # global_kb_repo = KBRepository()
            # global_kb_repo.collection_name = 'global_knowledge_base'
            # request = QueryRequest(query=query, top_k=top_k)
            # response = global_kb_repo.query(request)
            # return [
            #     {
            #         'content': item.content,
            #         'metadata': item.metadata or {},
            #         'similarity_score': item.score or 0.0,
            #         'source': 'global_kb',
            #         'doc_id': item.id,
            #     }
            #     for item in response.results
            # ]

        except Exception as e:
            logger.error(f"[RAG] Error searching global KB: {str(e)}")
            return []

    def _search_conversation_kb(
        self, conversation_id: str, user_id: str, query: str, top_k: int
    ) -> List[Dict[str, Any]]:
        """Search Conversation-specific Knowledge Base"""
        try:
            # TODO: Import from outside module - needs to be decided later
            # from app.modules.agentic_rag.services.conversation_rag_service import ConversationRAGService

            # Placeholder implementation - replace with actual search
            logger.warning(
                "Conversation KB search not implemented - external dependency"
            )
            results = []

            # Add CV context nếu có
            cv_context = self._get_cv_context(conversation_id, user_id, query)
            if cv_context:
                results.append(
                    {
                        "content": cv_context,
                        "metadata": {
                            "source": "cv_data",
                            "conversation_id": conversation_id,
                        },
                        "similarity_score": 0.95,  # High relevance for CV context
                        "source": "conversation_kb",
                        "doc_id": f"cv_{conversation_id}",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"[RAG] Error searching conversation KB: {str(e)}")
            return []

    def _get_cv_context(
        self, conversation_id: str, user_id: str, query: str
    ) -> Optional[str]:
        """Get relevant CV context nếu query liên quan đến CV"""
        try:
            # TODO: Import from outside module - needs to be decided later
            # from app.modules.chat.services.cv_integration_service import CVIntegrationService

            # Placeholder implementation - replace with actual CV service
            logger.warning("CV context retrieval not implemented - external dependency")

            # Check if query có liên quan đến CV
            cv_keywords = [
                "cv",
                "resume",
                "experience",
                "skill",
                "education",
                "work",
                "job",
                "career",
                "background",
            ]
            query_lower = query.lower()

            if any(keyword in query_lower for keyword in cv_keywords):
                return f"CV context for conversation {conversation_id} - placeholder"

            return None

        except Exception as e:
            logger.error(f"[RAG] Error getting CV context: {str(e)}")
            return None

    def _combine_and_rank_results(
        self, results: Dict[str, List[Dict]], route_decision: RAGRoute
    ) -> Dict[str, Any]:
        """Combine và rank results từ multiple knowledge bases"""
        all_sources = []

        # Collect all sources
        for source_type, source_results in results.items():
            for result in source_results:
                result["source_type"] = source_type
                all_sources.append(result)

        # Sort by similarity score (descending)
        all_sources.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        # Apply routing-based boost
        if route_decision.routing_decision == "conversation_only":
            # Boost conversation sources
            for source in all_sources:
                if source["source_type"] == "conversation":
                    source["similarity_score"] = (
                        source.get("similarity_score", 0.0) + 0.1
                    )

        elif route_decision.routing_decision == "global_only":
            # Boost global sources
            for source in all_sources:
                if source["source_type"] == "global":
                    source["similarity_score"] = (
                        source.get("similarity_score", 0.0) + 0.1
                    )

        # Re-sort after boosting
        all_sources.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        # Build context string
        context_parts = []
        for i, source in enumerate(all_sources[:10]):  # Top 10 sources
            source_info = f'[Source {i + 1} - {source["source_type"].upper()}]'
            context_parts.append(f'{source_info}\\n{source["content"]}')

        combined_context = "\\n\\n".join(context_parts)

        return {
            "context": combined_context,
            "sources": all_sources,
            "routing_decision": route_decision.routing_decision,
            "query_type": route_decision.query_type,
            "total_sources": len(all_sources),
            "global_sources": len(results.get("global", [])),
            "conversation_sources": len(results.get("conversation", [])),
        }

    async def _arun(
        self, conversation_id: str, user_id: str, query: str, top_k: int = 5
    ) -> str:
        """Async version of _run"""
        return self._run(conversation_id, user_id, query, top_k)
