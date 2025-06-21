"""
Global Knowledge Base Service
Quản lý kiến thức chung cho agent với admin document indexing
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .repository.kb_repo import KBRepository
from .schemas.kb_schema import (
	AddDocumentsRequest,
	DocumentModel,
	QueryRequest,
)

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


class GlobalKBService:
	"""Service quản lý Global Knowledge Base với admin document indexing"""

	GLOBAL_COLLECTION_NAME = 'global_knowledge_base'

	def __init__(self, db: Session):
		logger.info('[GlobalKBService] Starting GlobalKBService initialization')
		logger.debug(f'[GlobalKBService] Database session type: {type(db)}')

		self.db = db
		logger.debug('[GlobalKBService] Database session assigned')

		logger.debug('[GlobalKBService] Creating KBRepository instance')
		self.kb_repo = KBRepository()
		logger.debug('[GlobalKBService] KBRepository created successfully')

		logger.debug(f'[GlobalKBService] Setting collection name to: {self.GLOBAL_COLLECTION_NAME}')
		self.kb_repo.collection_name = self.GLOBAL_COLLECTION_NAME
		logger.info(f'[GlobalKBService] GlobalKBService initialized successfully with collection: {self.GLOBAL_COLLECTION_NAME}')

	async def index_admin_documents(self, documents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
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
		logger.info(f'[GlobalKBService] Starting index_admin_documents with {len(documents_data)} documents')
		logger.debug(f'[GlobalKBService] Documents data overview: {[doc.get("title", "No title") for doc in documents_data]}')

		documents = []
		successful_docs = []
		failed_docs = []

		logger.info('[GlobalKBService] Processing documents for indexing')
		for i, doc_data in enumerate(documents_data):
			logger.debug(f'[GlobalKBService] Processing document {i + 1}/{len(documents_data)}')
			try:
				doc_id = doc_data.get('id', f'admin_doc_{len(documents)}')
				title = doc_data.get('title', 'Untitled Document')
				content = doc_data.get('content', '')

				logger.debug(f'[GlobalKBService] Document details - ID: {doc_id}, Title: {title}, Content length: {len(content)}')

				if not content.strip():
					logger.warning(f'[GlobalKBService] Document {doc_id} has empty content, skipping')
					failed_docs.append({'id': doc_id, 'error': 'Empty content'})
					continue

				# Format content với title
				logger.debug(f'[GlobalKBService] Formatting content for document {doc_id}')
				formatted_content = f'# {title}\n\n{content}'
				logger.debug(f'[GlobalKBService] Formatted content length: {len(formatted_content)}')

				logger.debug(f'[GlobalKBService] Creating DocumentModel for {doc_id}')
				doc = DocumentModel(
					id=doc_id,
					content=formatted_content,
					metadata={
						'source': doc_data.get('source', 'admin_indexed'),
						'title': title,
						'category': doc_data.get('category', 'general'),
						'tags': doc_data.get('tags', []),
						'type': 'admin_document',
						'indexed_by': 'admin',
					},
				)
				documents.append(doc)
				successful_docs.append(doc_id)
				logger.info(f'[GlobalKBService] Successfully prepared admin document: {title} (ID: {doc_id})')

			except Exception as e:
				doc_id = doc_data.get('id', 'unknown')
				logger.error(f'[GlobalKBService] Error preparing document {doc_id}: {str(e)}')
				failed_docs.append({'id': doc_id, 'error': str(e)})

		# Index documents vào Global KB
		if documents:
			logger.info(f'[GlobalKBService] Starting indexing process for {len(documents)} admin documents to Global KB')
			logger.debug(f'[GlobalKBService] Collection name: {self.GLOBAL_COLLECTION_NAME}')

			try:
				request = AddDocumentsRequest(documents=documents)
				logger.debug(f'[GlobalKBService] Created AddDocumentsRequest with {len(request.documents)} documents')

				logger.debug('[GlobalKBService] Calling kb_repo.add_documents')
				indexed_ids = await self.kb_repo.add_documents(request)
				logger.info(f'[GlobalKBService] Successfully indexed {len(indexed_ids)} admin documents')
				logger.debug(f'[GlobalKBService] Indexed document IDs: {indexed_ids}')
			except Exception as e:
				logger.error(f'[GlobalKBService] Error during indexing process: {str(e)}')
				# Add all successful docs to failed if indexing fails
				for doc_id in successful_docs:
					failed_docs.append({'id': doc_id, 'error': f'Indexing failed: {str(e)}'})
				successful_docs = []
		else:
			logger.warning('[GlobalKBService] No admin documents to index after processing')

		result = {
			'successful_docs': successful_docs,
			'failed_docs': failed_docs,
			'total_documents': len(documents),
			'indexed_count': len(documents),
			'collection_name': self.GLOBAL_COLLECTION_NAME,
		}

		logger.info(f'[GlobalKBService] Completed index_admin_documents - Success: {len(successful_docs)}, Failed: {len(failed_docs)}')
		logger.debug(f'[GlobalKBService] Final result: {result}')
		return result

	async def _get_default_admin_documents(self) -> List[Dict[str, Any]]:
		"""Get default admin documents for agent knowledge"""
		logger.info('[GlobalKBService] Starting _get_default_admin_documents')

		try:
			logger.debug('[GlobalKBService] Preparing default admin documents list')
			default_docs = [
				{
					'id': 'agent_instructions_general',
					'title': 'General Agent Instructions',
					'content': """
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
					'category': 'instructions',
					'tags': ['general', 'guidelines', 'behavior'],
				},
				{
					'id': 'coding_best_practices',
					'title': 'Coding Best Practices',
					'content': """
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
					'category': 'technical',
					'tags': ['coding', 'best-practices', 'guidelines'],
				},
				{
					'id': 'cv_analysis_guidelines',
					'title': 'CV Analysis Guidelines',
					'content': """
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
					'category': 'hr',
					'tags': ['cv', 'analysis', 'career', 'hr'],
				},
				{
					'id': 'langchain_langgraph_basics',
					'title': 'LangChain & LangGraph Basics',
					'content': """
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
					'category': 'technical',
					'tags': ['langchain', 'langgraph', 'ai', 'framework'],
				},
			]

			logger.info(f'[GlobalKBService] Prepared {len(default_docs)} default admin documents')
			logger.debug(f'[GlobalKBService] Default doc IDs: {[doc["id"] for doc in default_docs]}')
			logger.debug(f'[GlobalKBService] Default doc categories: {list(set(doc["category"] for doc in default_docs))}')

			return default_docs

		except Exception as e:
			logger.error(f'[GlobalKBService] Error in _get_default_admin_documents: {str(e)}')
			return []

	async def add_general_knowledge(self, knowledge_items: List[Dict[str, Any]]) -> Dict[str, Any]:
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
		logger.info(f'[GlobalKBService] Starting add_general_knowledge with {len(knowledge_items)} items')
		logger.debug(f'[GlobalKBService] Knowledge items overview: {[item.get("title", "No title") for item in knowledge_items]}')

		documents = []
		logger.info('[GlobalKBService] Processing knowledge items for indexing')

		for i, item in enumerate(knowledge_items):
			logger.debug(f'[GlobalKBService] Processing knowledge item {i + 1}/{len(knowledge_items)}')
			try:
				title = item.get('title', 'Untitled')
				content = item.get('content', '')
				category = item.get('category', 'general')
				tags = item.get('tags', [])

				logger.debug(f'[GlobalKBService] Item details - Title: {title}, Category: {category}, Content length: {len(content)}, Tags: {tags}')

				doc_id = f'general_knowledge_{i}_{title.lower().replace(" ", "_")}'
				logger.debug(f'[GlobalKBService] Generated document ID: {doc_id}')

				formatted_content = f'# {title}\n\n{content}'
				logger.debug(f'[GlobalKBService] Formatted content length: {len(formatted_content)}')

				logger.debug(f'[GlobalKBService] Creating DocumentModel for knowledge item: {title}')
				doc = DocumentModel(
					id=doc_id,
					content=formatted_content,
					metadata={
						'source': 'manual_input',
						'category': category,
						'tags': tags,
						'type': 'general_knowledge',
						'title': title,
					},
				)
				documents.append(doc)
				logger.info(f'[GlobalKBService] Successfully prepared knowledge item: {title} (ID: {doc_id})')
			except Exception as e:
				logger.error(f'[GlobalKBService] Error processing knowledge item {i}: {str(e)}')

		if documents:
			logger.info(f'[GlobalKBService] Starting indexing process for {len(documents)} general knowledge items')
			logger.debug(f'[GlobalKBService] Collection name: {self.GLOBAL_COLLECTION_NAME}')

			try:
				request = AddDocumentsRequest(documents=documents)
				logger.debug(f'[GlobalKBService] Created AddDocumentsRequest with {len(request.documents)} documents')

				logger.debug('[GlobalKBService] Calling kb_repo.add_documents for general knowledge')
				indexed_ids = await self.kb_repo.add_documents(request)
				logger.info(f'[GlobalKBService] Successfully indexed {len(indexed_ids)} general knowledge items')
				logger.debug(f'[GlobalKBService] Indexed knowledge item IDs: {indexed_ids}')

				result = {
					'indexed_count': len(indexed_ids),
					'total_items': len(knowledge_items),
					'collection_name': self.GLOBAL_COLLECTION_NAME,
				}

				logger.info(f'[GlobalKBService] Completed add_general_knowledge successfully')
				logger.debug(f'[GlobalKBService] Final result: {result}')
				return result
			except Exception as e:
				logger.error(f'[GlobalKBService] Error during general knowledge indexing: {str(e)}')
				return {
					'indexed_count': 0,
					'total_items': len(knowledge_items),
					'collection_name': self.GLOBAL_COLLECTION_NAME,
					'error': str(e),
				}
		else:
			logger.warning('[GlobalKBService] No knowledge items to index after processing')
			return {
				'indexed_count': 0,
				'total_items': 0,
				'collection_name': self.GLOBAL_COLLECTION_NAME,
			}

	async def search_global_knowledge(self, query: str, top_k: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
		"""
		Search Global Knowledge Base

		Args:
		    query: Search query
		    top_k: Number of results
		    category: Filter by category (optional)

		Returns:
		    Search results
		"""
		logger.info(f'[GlobalKBService] Starting search_global_knowledge')
		logger.debug(f'[GlobalKBService] Search parameters - Query: "{query[:50]}...", top_k: {top_k}, category: {category}')
		logger.debug(f'[GlobalKBService] Collection: {self.GLOBAL_COLLECTION_NAME}')

		try:
			logger.debug('[GlobalKBService] Creating QueryRequest')
			request = QueryRequest(query=query, top_k=top_k)
			logger.debug(f'[GlobalKBService] QueryRequest created with query length: {len(query)}, top_k: {top_k}')

			logger.debug('[GlobalKBService] Calling kb_repo.query')
			response = await self.kb_repo.query(request)
			logger.info(f'[GlobalKBService] Received {len(response.results)} results from kb_repo')

			results = []
			filtered_count = 0

			logger.debug('[GlobalKBService] Processing search results')
			for i, item in enumerate(response.results):
				logger.debug(f'[GlobalKBService] Processing result {i + 1}/{len(response.results)}')

				# Filter by category if specified
				if category and item.metadata and item.metadata.get('category') != category:
					logger.debug(f'[GlobalKBService] Filtering out result {i + 1} - category mismatch: {item.metadata.get("category")} != {category}')
					filtered_count += 1
					continue

				logger.debug(f'[GlobalKBService] Including result {i + 1} - Score: {item.score}, Content length: {len(item.content) if item.content else 0}')
				result = {
					'content': item.content,
					'metadata': item.metadata or {},
					'similarity_score': item.score or 0.0,
					'source': 'global_kb',
					'doc_id': item.id,
				}
				results.append(result)
				logger.debug(f'[GlobalKBService] Added result with doc_id: {item.id}')

			logger.info(f'[GlobalKBService] Search completed - Found {len(results)} relevant items (filtered out {filtered_count})')
			logger.debug(f'[GlobalKBService] Result summary: {[{"doc_id": r["doc_id"], "score": r["similarity_score"]} for r in results[:3]]}')
			return results

		except Exception as e:
			logger.error(f'[GlobalKBService] Error searching global knowledge: {str(e)}')
			logger.debug(f'[GlobalKBService] Search error details - Query: "{query}", Collection: {self.GLOBAL_COLLECTION_NAME}')
			return []

	def get_global_kb_stats(self) -> Dict[str, Any]:
		"""Get statistics về Global Knowledge Base"""
		logger.info('[GlobalKBService] Starting get_global_kb_stats')
		logger.debug(f'[GlobalKBService] Collection name: {self.GLOBAL_COLLECTION_NAME}')

		try:
			logger.debug('[GlobalKBService] Checking if collection exists')
			collection_exists = self._check_collection_exists()
			logger.debug(f'[GlobalKBService] Collection exists check result: {collection_exists}')

			# Check if collection exists và get basic stats
			stats = {
				'collection_name': self.GLOBAL_COLLECTION_NAME,
				'exists': collection_exists,
				'status': ('active' if collection_exists else 'not_initialized'),
			}

			logger.info(f'[GlobalKBService] Successfully generated Global KB stats')
			logger.debug(f'[GlobalKBService] Stats details: {stats}')
			return stats

		except Exception as e:
			logger.error(f'[GlobalKBService] Error getting stats: {str(e)}')
			error_stats = {
				'collection_name': self.GLOBAL_COLLECTION_NAME,
				'exists': False,
				'status': 'error',
				'error': str(e),
			}
			logger.debug(f'[GlobalKBService] Error stats: {error_stats}')
			return error_stats

	def _check_collection_exists(self) -> bool:
		"""Check if Global KB collection exists"""
		logger.debug('[GlobalKBService] Starting _check_collection_exists')
		try:
			# Simple check - would implement actual collection existence check
			logger.debug('[GlobalKBService] Performing collection existence check (placeholder implementation)')
			result = True  # Placeholder
			logger.debug(f'[GlobalKBService] Collection existence check result: {result}')
			return result
		except Exception as e:
			logger.error(f'[GlobalKBService] Error in _check_collection_exists: {str(e)}')
			return False

	async def initialize_default_knowledge(self) -> Dict[str, Any]:
		"""Initialize Global KB với default admin documents"""
		logger.info('[GlobalKBService] Starting initialize_default_knowledge')
		logger.debug(f'[GlobalKBService] Collection: {self.GLOBAL_COLLECTION_NAME}')

		try:
			# 1. Index default admin documents
			logger.info('[GlobalKBService] Step 1: Getting default admin documents')
			default_admin_docs = await self._get_default_admin_documents()
			logger.info(f'[GlobalKBService] Retrieved {len(default_admin_docs)} default admin documents')
			logger.debug(f'[GlobalKBService] Admin docs titles: {[doc.get("title") for doc in default_admin_docs]}')

			logger.info('[GlobalKBService] Step 2: Indexing default admin documents')
			admin_result = await self.index_admin_documents(default_admin_docs)
			logger.info(f'[GlobalKBService] Admin indexing completed - Success: {len(admin_result.get("successful_docs", []))}, Failed: {len(admin_result.get("failed_docs", []))}')

			# 2. Add additional general knowledge
			logger.info('[GlobalKBService] Step 3: Preparing additional general knowledge')
			additional_knowledge = [
				{
					'title': 'AI Assistant Best Practices',
					'content': """
AI Assistant nên:
- Cung cấp thông tin chính xác và hữu ích
- Thừa nhận khi không biết thông tin
- Đưa ra giải thích rõ ràng, dễ hiểu
- Tôn trọng privacy và bảo mật
- Hỗ trợ người dùng đạt được mục tiêu
- Sử dụng ngôn ngữ phù hợp với context
                    """,
					'category': 'ai_guidelines',
					'tags': ['ai', 'best_practices', 'guidelines'],
				},
				{
					'title': 'Software Development Principles',
					'content': """
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
					'category': 'development',
					'tags': ['programming', 'principles', 'best_practices'],
				},
			]

			logger.info(f'[GlobalKBService] Prepared {len(additional_knowledge)} additional knowledge items')
			logger.debug(f'[GlobalKBService] Additional knowledge titles: {[item.get("title") for item in additional_knowledge]}')

			logger.info('[GlobalKBService] Step 4: Adding additional general knowledge')
			general_result = await self.add_general_knowledge(additional_knowledge)
			logger.info(f'[GlobalKBService] General knowledge indexing completed - Indexed: {general_result.get("indexed_count", 0)}')

			total_result = {
				'admin_documents': admin_result,
				'general_knowledge': general_result,
				'status': 'initialized',
				'collection_name': self.GLOBAL_COLLECTION_NAME,
			}

			logger.info('[GlobalKBService] Default global knowledge base initialized successfully')
			logger.debug(f'[GlobalKBService] Final initialization result: {total_result}')
			return total_result

		except Exception as e:
			logger.error(f'[GlobalKBService] Error in initialize_default_knowledge: {str(e)}')
			error_result = {
				'admin_documents': {
					'successful_docs': [],
					'failed_docs': [],
					'total_documents': 0,
					'indexed_count': 0,
				},
				'general_knowledge': {'indexed_count': 0, 'total_items': 0},
				'status': 'error',
				'collection_name': self.GLOBAL_COLLECTION_NAME,
				'error': str(e),
			}
			logger.debug(f'[GlobalKBService] Error result: {error_result}')
			return error_result
