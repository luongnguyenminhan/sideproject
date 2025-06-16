"""
Global Knowledge Base Service
Quản lý kiến thức chung cho agent với admin document indexing
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.modules.agentic_rag.repository.kb_repo import KBRepository
from app.modules.agentic_rag.schemas.kb_schema import (
    AddDocumentsRequest,
    DocumentModel,
    QueryRequest,
)
from app.middleware.translation_manager import _
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


class GlobalKBService:
    """Service quản lý Global Knowledge Base với admin document indexing"""

    GLOBAL_COLLECTION_NAME = "global_knowledge_base"

    def __init__(self, db: Session):
        logger.info("[GlobalKBService] Initializing Global Knowledge Base service")
        self.db = db
        self.kb_repo = KBRepository()
        self.kb_repo.collection_name = self.GLOBAL_COLLECTION_NAME
        logger.info(
            f"[GlobalKBService] Using collection: {self.GLOBAL_COLLECTION_NAME}"
        )

    async def index_admin_documents(
        self, documents_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Index admin documents vào Global KB

        Args:
            documents_data: List documents với format:
                [{
                    "id": str,
                    "title": str,
                    "content": str,
                    "category": str,
                    "tags": List[str],
                    "source": str (optional)
                }]

        Returns:
            Indexing results
        """
        logger.info(f"[GlobalKBService] Indexing {len(documents_data)} admin documents")

        documents = []
        successful_docs = []
        failed_docs = []

        for doc_data in documents_data:
            try:
                doc_id = doc_data.get("id", f"admin_doc_{len(documents)}")
                title = doc_data.get("title", "Untitled Document")
                content = doc_data.get("content", "")

                if not content.strip():
                    failed_docs.append({"id": doc_id, "error": "Empty content"})
                    continue

                # Format content với title
                formatted_content = f"# {title}\n\n{content}"

                doc = DocumentModel(
                    id=doc_id,
                    content=formatted_content,
                    metadata={
                        "source": doc_data.get("source", "admin_indexed"),
                        "title": title,
                        "category": doc_data.get("category", "general"),
                        "tags": doc_data.get("tags", []),
                        "type": "admin_document",
                        "indexed_by": "admin",
                    },
                )
                documents.append(doc)
                successful_docs.append(doc_id)
                logger.info(f"[GlobalKBService] Prepared admin document: {title}")

            except Exception as e:
                doc_id = doc_data.get("id", "unknown")
                logger.error(
                    f"[GlobalKBService] Error preparing document {doc_id}: {str(e)}"
                )
                failed_docs.append({"id": doc_id, "error": str(e)})

        # Index documents vào Global KB
        if documents:
            logger.info(
                f"[GlobalKBService] Indexing {len(documents)} admin documents to Global KB"
            )

            request = AddDocumentsRequest(documents=documents)
            indexed_ids = await self.kb_repo.add_documents(request)

            logger.info(
                f"[GlobalKBService] Successfully indexed {len(indexed_ids)} admin documents"
            )
        else:
            logger.warning("[GlobalKBService] No admin documents to index")

        return {
            "successful_docs": successful_docs,
            "failed_docs": failed_docs,
            "total_documents": len(documents),
            "indexed_count": len(documents),
            "collection_name": self.GLOBAL_COLLECTION_NAME,
        }

    async def _get_default_admin_documents(self) -> List[Dict[str, Any]]:
        """Get default admin documents for agent knowledge"""
        return [
            {
                "id": "agent_instructions_general",
                "title": "General Agent Instructions",
                "content": """
Agent là một AI assistant thông minh và hữu ích.

## Nguyên tắc cơ bản:
- Luôn trả lời bằng tiếng Việt
- Cung cấp thông tin chính xác và hữu ích
- Hỏi lại nếu câu hỏi không rõ ràng
- Tôn trọng người dùng và giữ giao tiếp lịch sự
- Không cung cấp thông tin có hại hoặc không phù hợp

## Khả năng chính:
- Trả lời câu hỏi và tư vấn
- Hỗ trợ phân tích CV và tuyển dụng
- Coding và technical support
- Dịch thuật và giải thích
- Brainstorming và creative thinking
                """,
                "category": "instructions",
                "tags": ["general", "guidelines", "behavior"],
            },
            {
                "id": "coding_best_practices",
                "title": "Coding Best Practices",
                "content": """
## Nguyên tắc lập trình tốt:

### Code Quality:
- Viết code clean, readable và maintainable
- Sử dụng naming conventions phù hợp
- Comment code khi cần thiết
- Tránh code duplication (DRY principle)

### Error Handling:
- Luôn handle exceptions properly
- Log errors với thông tin chi tiết
- Provide meaningful error messages

### Performance:
- Optimize database queries
- Use async/await cho I/O operations
- Cache kết quả khi phù hợp
- Monitor memory usage

### Security:
- Validate input data
- Use parameterized queries
- Implement proper authentication
- Follow security best practices
                """,
                "category": "technical",
                "tags": ["coding", "best-practices", "guidelines"],
            },
            {
                "id": "cv_analysis_guidelines",
                "title": "CV Analysis Guidelines",
                "content": """
## Hướng dẫn phân tích CV:

### Thông tin cần extract:
- Personal Information (tên, contact, địa chỉ)
- Work Experience (công ty, vị trí, thời gian, mô tả)
- Education (trường, bằng cấp, GPA, thời gian)
- Skills (technical, soft skills, certifications)
- Projects (dự án cá nhân, mô tả, technology stack)

### Phân tích chất lượng:
- Đánh giá relevance với job requirements
- Identify strengths và weaknesses
- Suggest improvements
- Highlight unique selling points

### Tư vấn career:
- Career progression advice
- Skill development recommendations
- Interview preparation tips
- Salary negotiation guidance
                """,
                "category": "hr",
                "tags": ["cv", "analysis", "career", "hr"],
            },
            {
                "id": "langchain_langgraph_basics",
                "title": "LangChain & LangGraph Basics",
                "content": """
## LangChain Framework:

### Core Components:
- **LLMs**: Language model interfaces
- **Prompts**: Templates for model inputs  
- **Chains**: Sequences of calls to components
- **Agents**: High-level directives for LLMs
- **Memory**: State persistence
- **Retrievers**: Interfaces for unstructured data

### Basic Usage:
```python
from langchain.llms import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

llm = ChatGoogleGenerativeAI(model="gemini-pro")
prompt = PromptTemplate(template="Answer: {question}")
chain = LLMChain(llm=llm, prompt=prompt)
```

## LangGraph for Workflows:

### Core Concepts:
- **StateGraph**: Main workflow structure
- **Nodes**: Individual processing steps
- **Edges**: Connections between nodes
- **Conditional Edges**: Dynamic routing

### Example:
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_edge("process", END)
```
                """,
                "category": "technical",
                "tags": ["langchain", "langgraph", "ai", "framework"],
            },
        ]

    async def add_general_knowledge(
        self, knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add general knowledge items vào Global KB

        Args:
            knowledge_items: List knowledge items với format:
                [{
                    "title": str,
                    "content": str,
                    "category": str,
                    "tags": List[str]
                }]

        Returns:
            Indexing results
        """
        logger.info(
            f"[GlobalKBService] Adding {len(knowledge_items)} general knowledge items"
        )

        documents = []
        for i, item in enumerate(knowledge_items):
            doc = DocumentModel(
                id=f"general_knowledge_{i}_{item.get('title', '').lower().replace(' ', '_')}",
                content=f"# {item.get('title', 'Untitled')}\n\n{item.get('content', '')}",
                metadata={
                    "source": "manual_input",
                    "category": item.get("category", "general"),
                    "tags": item.get("tags", []),
                    "type": "general_knowledge",
                    "title": item.get("title", ""),
                },
            )
            documents.append(doc)

        if documents:
            request = AddDocumentsRequest(documents=documents)
            indexed_ids = await self.kb_repo.add_documents(request)

            logger.info(
                f"[GlobalKBService] Successfully indexed {len(indexed_ids)} general knowledge items"
            )

            return {
                "indexed_count": len(indexed_ids),
                "total_items": len(knowledge_items),
                "collection_name": self.GLOBAL_COLLECTION_NAME,
            }
        else:
            return {
                "indexed_count": 0,
                "total_items": 0,
                "collection_name": self.GLOBAL_COLLECTION_NAME,
            }

    async def search_global_knowledge(
        self, query: str, top_k: int = 10, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Global Knowledge Base

        Args:
            query: Search query
            top_k: Number of results
            category: Filter by category (optional)

        Returns:
            Search results
        """
        logger.info(f'[GlobalKBService] Searching global knowledge: "{query[:50]}..."')

        try:
            request = QueryRequest(query=query, top_k=top_k)
            response = await self.kb_repo.query(request)

            results = []
            for item in response.results:
                # Filter by category if specified
                if (
                    category
                    and item.metadata
                    and item.metadata.get("category") != category
                ):
                    continue

                result = {
                    "content": item.content,
                    "metadata": item.metadata or {},
                    "similarity_score": item.score or 0.0,
                    "source": "global_kb",
                    "doc_id": item.id,
                }
                results.append(result)

            logger.info(f"[GlobalKBService] Found {len(results)} relevant items")
            return results

        except Exception as e:
            logger.error(
                f"[GlobalKBService] Error searching global knowledge: {str(e)}"
            )
            return []

    def get_global_kb_stats(self) -> Dict[str, Any]:
        """Get statistics về Global Knowledge Base"""
        try:
            # Check if collection exists và get basic stats
            stats = {
                "collection_name": self.GLOBAL_COLLECTION_NAME,
                "exists": self._check_collection_exists(),
                "status": (
                    "active" if self._check_collection_exists() else "not_initialized"
                ),
            }

            logger.info(f"[GlobalKBService] Global KB stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"[GlobalKBService] Error getting stats: {str(e)}")
            return {
                "collection_name": self.GLOBAL_COLLECTION_NAME,
                "exists": False,
                "status": "error",
                "error": str(e),
            }

    def _check_collection_exists(self) -> bool:
        """Check if Global KB collection exists"""
        try:
            # Simple check - would implement actual collection existence check
            return True  # Placeholder
        except Exception:
            return False

    async def initialize_default_knowledge(self) -> Dict[str, Any]:
        """Initialize Global KB với default admin documents"""
        logger.info("[GlobalKBService] Initializing default global knowledge base")

        # 1. Index default admin documents
        default_admin_docs = await self._get_default_admin_documents()
        admin_result = await self.index_admin_documents(default_admin_docs)

        # 2. Add additional general knowledge
        additional_knowledge = [
            {
                "title": "AI Assistant Best Practices",
                "content": """
AI Assistant nên:
- Cung cấp thông tin chính xác và hữu ích
- Thừa nhận khi không biết thông tin
- Đưa ra giải thích rõ ràng, dễ hiểu
- Tôn trọng privacy và bảo mật
- Hỗ trợ người dùng đạt được mục tiêu
- Sử dụng ngôn ngữ phù hợp với context
                """,
                "category": "ai_guidelines",
                "tags": ["ai", "best_practices", "guidelines"],
            },
            {
                "title": "Software Development Principles",
                "content": """
Nguyên tắc phát triển phần mềm:
- SOLID principles
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple, Stupid)
- YAGNI (You Aren't Gonna Need It)
- Code readability và maintainability
- Proper error handling
- Testing và documentation
- Security best practices
                """,
                "category": "development",
                "tags": ["programming", "principles", "best_practices"],
            },
        ]

        general_result = await self.add_general_knowledge(additional_knowledge)

        total_result = {
            "admin_documents": admin_result,
            "general_knowledge": general_result,
            "status": "initialized",
            "collection_name": self.GLOBAL_COLLECTION_NAME,
        }

        logger.info(
            "[GlobalKBService] Default global knowledge base initialized successfully"
        )
        return total_result
