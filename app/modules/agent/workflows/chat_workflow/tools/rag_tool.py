"""
RAG Tool for Chat Agent - Simplified Function-based Implementation
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Literal
from langchain_core.tools import tool
from pydantic import BaseModel, Field
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


# Global variables for tool configuration
_global_db_session: Optional[Session] = None
_router_llm = None
_router_prompt = None
_router_chain = None


def _initialize_rag_components():
    """Initialize RAG components if not already initialized"""
    global _router_llm, _router_prompt, _router_chain

    if _router_llm is None:
        print("🚀 [RAG] Initializing RAG components...")

        # Initialize router LLM for intelligent routing
        _router_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)

        # Router prompt for query analysis and routing
        _router_prompt = ChatPromptTemplate.from_messages(
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

        _router_chain = _router_prompt | _router_llm.with_structured_output(RAGRoute)

        print("✅ [RAG] RAG components initialized")


@tool("rag_retrieval", args_schema=RAGInput)
def rag_retrieval_tool(
    conversation_id: str, user_id: str, query: str, top_k: int = 5
) -> str:
    """
    🔍 ADVANCED RAG SEARCH TOOL - Ưu tiên sử dụng để tìm kiếm thông tin!

    📋 ƯU TIÊN SỬ DỤNG TOOL NÀY KHI:
    ✅ User hỏi về bất kỳ thông tin nào - dù đơn giản
    ✅ Cần tìm thông tin về công ty, việc làm, kiến thức chuyên môn
    ✅ User đề cập đến tài liệu, file đã upload trước đó
    ✅ Câu hỏi về thông tin personal/CV/profile của user
    ✅ Tìm hiểu về lịch sử trò chuyện trước đó
    ✅ Bất kỳ câu hỏi nào cần context hoặc thông tin cụ thể
    ✅ User hỏi về Enterview, dịch vụ, tính năng
    ✅ Câu hỏi về tuyển dụng, phỏng vấn, career advice

    ⚠️ LUÔN ƯU TIÊN tool này thay vì trả lời trực tiếp!

    🎯 CHỨC NĂNG:
    - Tìm kiếm trong Global Knowledge Base (kiến thức tổng quát)
    - Tìm kiếm trong Conversation Knowledge Base (CV, files của user)
    - Intelligent routing để chọn source phù hợp
    - Kết hợp và rank kết quả từ nhiều nguồn

    Args:
        conversation_id: ID cuộc trò chuyện
        user_id: ID người dùng
        query: Câu hỏi tìm kiếm (có thể rephrase để tối ưu)
        top_k: Số kết quả trả về (default: 5)

    Returns:
        JSON string với retrieved context
    """
    print(f"🔍 [RAG] Tool called with query: {query[:100]}...")

    try:
        # Initialize components if needed
        _initialize_rag_components()

        logger.info(
            f'[RAG] Processing query: "{query[:100]}..." for conversation: {conversation_id}'
        )

        # Execute RAG retrieval using asyncio
        result = asyncio.run(_execute_rag_async(conversation_id, user_id, query, top_k))

        print(f"✅ [RAG] Tool execution completed successfully")
        return result

    except Exception as e:
        print(f"💥 [RAG] Error: {str(e)}")
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


async def _execute_rag_async(
    conversation_id: str, user_id: str, query: str, top_k: int
) -> str:
    """Execute RAG retrieval với intelligent routing"""
    print(f"🎯 [RAG] Starting async RAG execution")

    # 1. Intelligent routing
    route_decision = await _route_query_async(query)
    logger.info(
        f"[RAG] Routing decision: {route_decision.routing_decision}, Query type: {route_decision.query_type}"
    )

    # 2. Retrieve from appropriate knowledge bases
    results = await _execute_retrieval_async(
        conversation_id=conversation_id,
        user_id=user_id,
        route_decision=route_decision,
        top_k=top_k,
    )

    # 3. Combine and rank results
    final_context = _combine_and_rank_results(results, route_decision)

    logger.info(
        f'[RAG] Retrieved {len(final_context.get("sources", []))} total sources'
    )

    return json.dumps(final_context, ensure_ascii=False)


async def _route_query_async(query: str) -> RAGRoute:
    """Phân tích query và quyết định routing"""
    try:
        if _router_chain is None:
            raise Exception("Router chain not initialized")

        route_decision = await _router_chain.ainvoke({"query": query})
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


async def _execute_retrieval_async(
    conversation_id: str, user_id: str, route_decision: RAGRoute, top_k: int
) -> Dict[str, List[Dict]]:
    """Execute retrieval từ các knowledge bases theo routing decision"""
    results = {"global": [], "conversation": []}

    try:
        # Global Knowledge Base retrieval
        if route_decision.routing_decision in ["global_only", "both"]:
            global_results = await _search_global_kb_async(
                route_decision.enhanced_query, top_k
            )
            results["global"] = global_results
            logger.info(f"[RAG] Retrieved {len(global_results)} results from Global KB")

        # Conversation Knowledge Base retrieval
        if route_decision.routing_decision in ["conversation_only", "both"]:
            conv_results = await _search_conversation_kb_async(
                conversation_id, user_id, route_decision.enhanced_query, top_k
            )
            results["conversation"] = conv_results
            logger.info(
                f"[RAG] Retrieved {len(conv_results)} results from Conversation KB"
            )

    except Exception as e:
        logger.error(f"[RAG] Error in retrieval execution: {str(e)}")

    return results


async def _search_global_kb_async(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Search Global Knowledge Base"""
    try:
        print(f"🌐 [RAG] Searching Global KB for: {query[:50]}...")

        # Mock implementation for demonstration
        # TODO: Replace with actual search implementation
        mock_results = [
            {
                "content": f"Global knowledge about {query} - mock result 1",
                "metadata": {"source": "global_kb", "topic": "general"},
                "similarity_score": 0.85,
                "source": "global_kb",
                "doc_id": "global_1",
            },
            {
                "content": f"Additional global context for {query} - mock result 2",
                "metadata": {"source": "global_kb", "topic": "technical"},
                "similarity_score": 0.78,
                "source": "global_kb",
                "doc_id": "global_2",
            },
        ]

        logger.info(f"[RAG] Global KB search returned {len(mock_results)} results")
        return mock_results

        # Commented out actual implementation that requires external dependencies:
        """
        from app.modules.agentic_rag.repository.kb_repo import KBRepository
        from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

        global_kb_repo = KBRepository()
        global_kb_repo.collection_name = "global_knowledge_base"
        request = QueryRequest(query=query, top_k=top_k)
        response = global_kb_repo.query(request)
        return [
            {
                "content": item.content,
                "metadata": item.metadata or {},
                "similarity_score": item.score or 0.0,
                "source": "global_kb",
                "doc_id": item.id,
            }
            for item in response.results
        ]
        """

    except Exception as e:
        logger.error(f"[RAG] Error searching global KB: {str(e)}")
        return []


async def _search_conversation_kb_async(
    conversation_id: str, user_id: str, query: str, top_k: int
) -> List[Dict[str, Any]]:
    """Search Conversation-specific Knowledge Base"""
    try:
        print(f"💬 [RAG] Searching Conversation KB for: {query[:50]}...")

        results = []

        # Add CV context nếu có
        cv_context = await _get_cv_context_async(conversation_id, user_id, query)
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

        # Mock additional conversation results
        if len(results) < top_k:
            mock_conv_result = {
                "content": f"Conversation-specific context about {query} for user {user_id}",
                "metadata": {
                    "source": "conversation_history",
                    "conversation_id": conversation_id,
                },
                "similarity_score": 0.82,
                "source": "conversation_kb",
                "doc_id": f"conv_{conversation_id}_1",
            }
            results.append(mock_conv_result)

        logger.info(f"[RAG] Conversation KB search returned {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"[RAG] Error searching conversation KB: {str(e)}")
        return []


async def _get_cv_context_async(
    conversation_id: str, user_id: str, query: str
) -> Optional[str]:
    """Get relevant CV context nếu query liên quan đến CV"""
    try:
        print(f"📄 [RAG] Checking for CV context relevance...")

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
            "profile",
            "kinh nghiệm",
            "kỹ năng",
        ]
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in cv_keywords):
            # Mock CV context
            cv_context = f"""
CV Information for user {user_id} in conversation {conversation_id}:
- Experience: Software Developer with 3+ years
- Skills: Python, JavaScript, React, Node.js
- Education: Computer Science degree
- Recent projects: E-commerce platform, Chat application
- Looking for: Senior developer position
            """
            print(f"✅ [RAG] CV context found and returned")
            return cv_context.strip()

        print(f"❌ [RAG] No CV context needed for this query")
        return None

        # TODO: Replace with actual CV service integration:
        """
        from app.modules.chat.services.cv_integration_service import CVIntegrationService
        cv_service = CVIntegrationService()
        return await cv_service.get_relevant_cv_context(conversation_id, user_id, query)
        """

    except Exception as e:
        logger.error(f"[RAG] Error getting CV context: {str(e)}")
        return None


def _combine_and_rank_results(
    results: Dict[str, List[Dict]], route_decision: RAGRoute
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
                source["similarity_score"] = source.get("similarity_score", 0.0) + 0.1

    elif route_decision.routing_decision == "global_only":
        # Boost global sources
        for source in all_sources:
            if source["source_type"] == "global":
                source["similarity_score"] = source.get("similarity_score", 0.0) + 0.1

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


def get_rag_tool(db_session: Session):
    """Factory function để tạo RAG tool với db_session"""
    print(f"🏭 [Factory] Creating function-based RAG tool")

    # Store db_session in global context
    global _global_db_session
    _global_db_session = db_session

    print(f"✅ [Factory] RAG tool created")
    return rag_retrieval_tool
