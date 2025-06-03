"""
Enhanced Chat Workflow với QdrantService Integration
Production-ready LangGraph workflow cho MoneyEZ Financial Assistant

✨ Features:
- QdrantService integration cho knowledge retrieval
- Query optimization cho better search
- Basic calculation tools (+, -, *, /)
- Vietnamese financial expertise
- Production error handling
- Performance monitoring
"""

import logging
import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .basic_workflow import create_workflow_with_rag, basic_workflow
from .config import WorkflowConfig
from .knowledge.query_optimizer import QueryOptimizer
from .knowledge.retriever import KnowledgeRetriever
from app.modules.agent.services.qdrant_service import QdrantService

logger = logging.getLogger(__name__)


class ChatWorkflow:
	"""
	Enhanced Chat Workflow Implementation

	Production workflow với:
	- QdrantService integration
	- Query optimization
	- Knowledge retrieval
	- Basic calculation tools
	- Vietnamese financial knowledge
	- Production-ready error handling
	"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()

		# Initialize services
		self.qdrant_service = None
		self.query_optimizer = None
		self.knowledge_retriever = None

		try:
			# Initialize RAG services
			self.qdrant_service = QdrantService(db_session)
			self.query_optimizer = QueryOptimizer(self.config)
			self.knowledge_retriever = KnowledgeRetriever(db_session, self.config)

			# Use RAG-enabled workflow
			self.compiled_graph = create_workflow_with_rag(db_session, self.config)

			logger.info('🚀 [ChatWorkflow] Initialized with RAG functionality')

		except Exception as e:
			logger.warning(f'⚠️ [ChatWorkflow] RAG initialization failed: {str(e)}, using basic workflow')

			# Fallback to basic workflow
			self.compiled_graph = basic_workflow

		logger.info('✅ [ChatWorkflow] Workflow ready')

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""
		Process user message through enhanced workflow với RAG
		"""
		start_time = time.time()

		try:
			logger.info(f"📨 [ChatWorkflow] Processing message: '{user_message[:50]}...'")

			# Create initial state
			from langchain_core.messages import HumanMessage

			initial_state = {'messages': [HumanMessage(content=user_message)]}

			# Prepare config
			runtime_config = {
				'configurable': {
					'thread_id': session_id or 'default',
					'system_prompt': getattr(self.config, 'system_prompt', None),
					'use_rag': (self.config.rag_enabled if hasattr(self.config, 'rag_enabled') else True),
					**self.config.to_dict(),
				}
			}

			if config_override:
				runtime_config['configurable'].update(config_override)

			# Execute workflow
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)

			# Extract response
			response = self._extract_response(final_state)

			# Calculate processing metrics
			processing_time = time.time() - start_time

			logger.info(f'✅ [ChatWorkflow] Message processed successfully (processed in {processing_time:.2f}s)')

			return {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'rag_used': bool(final_state.get('rag_context')),
					'rag_sources': len(final_state.get('rag_context', [])),
					'user_id': user_id,
					'session_id': session_id,
				},
			}

		except Exception as e:
			logger.error(f'❌ [ChatWorkflow] Error processing message: {str(e)}')

			# Create fallback response
			fallback_response = 'Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau hoặc đặt câu hỏi khác.'

			return {
				'response': fallback_response,
				'error': str(e),
				'metadata': {
					'processing_time': time.time() - start_time,
					'error_occurred': True,
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response từ final state"""

		messages = final_state.get('messages', [])
		if not messages:
			return 'Không thể tạo phản hồi.'

		# Get last AI message
		for message in reversed(messages):
			if hasattr(message, 'content') and message.content:
				content = message.content
				if content and content.strip():
					return content

		return 'Phản hồi không khả dụng.'

	async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
		"""Search knowledge base directly"""
		try:
			if not self.query_optimizer or not self.knowledge_retriever:
				logger.warning('RAG services not available for knowledge search')
				return []

			# Optimize queries
			optimized_queries = self.query_optimizer.optimize_queries(query)

			# Retrieve documents
			documents = await self.knowledge_retriever.retrieve_documents(queries=optimized_queries, top_k=top_k)

			# Format results
			results = []
			for doc in documents:
				results.append({
					'content': doc.page_content,
					'metadata': doc.metadata,
					'score': doc.metadata.get('similarity_score', 0),
				})

			return results

		except Exception as e:
			logger.error(f'Error searching knowledge: {str(e)}')
			return []

	async def index_documents(self, documents: List[Dict[str, Any]], collection_name: Optional[str] = None) -> Dict[str, Any]:
		"""Index documents to knowledge base"""
		try:
			if not self.qdrant_service:
				return {'error': 'QdrantService not available'}

			from langchain_core.documents import Document

			# Convert to Document objects
			doc_objects = []
			for doc in documents:
				content = doc.get('content', '')
				metadata = doc.get('metadata', {})
				doc_objects.append(Document(page_content=content, metadata=metadata))

			# Index documents
			collection = collection_name or self.config.collection_name
			result = self.qdrant_service.index_documents(doc_objects, collection)

			logger.info(f'Indexed {result.get("total_indexed", 0)} documents to {collection}')
			return result

		except Exception as e:
			logger.error(f'Error indexing documents: {str(e)}')
			return {'error': str(e)}

	async def get_knowledge_stats(self) -> Dict[str, Any]:
		"""Get knowledge base statistics"""
		try:
			if not self.qdrant_service:
				return {'error': 'QdrantService not available'}

			stats = self.qdrant_service.get_collection_stats(self.config.collection_name)
			return stats

		except Exception as e:
			logger.error(f'Error getting knowledge stats: {str(e)}')
			return {'error': str(e)}

	async def health_check(self) -> Dict[str, Any]:
		"""Comprehensive health check"""

		try:
			health_data = {
				'status': 'healthy',
				'components': {},
				'timestamp': time.time(),
			}

			# Check QdrantService
			if self.qdrant_service:
				try:
					collections = self.qdrant_service.list_collections()
					health_data['components']['qdrant'] = {
						'status': 'healthy',
						'collections': collections,
					}
				except Exception as e:
					health_data['components']['qdrant'] = {
						'status': 'unhealthy',
						'error': str(e),
					}
			else:
				health_data['components']['qdrant'] = {'status': 'not_initialized'}

			# Check Query Optimizer
			health_data['components']['query_optimizer'] = {'status': 'healthy' if self.query_optimizer else 'not_initialized'}

			# Check Knowledge Retriever
			if self.knowledge_retriever:
				retriever_health = await self.knowledge_retriever.health_check()
				health_data['components']['knowledge_retriever'] = retriever_health
			else:
				health_data['components']['knowledge_retriever'] = {'status': 'not_initialized'}

			# Check workflow
			health_data['components']['workflow'] = {
				'status': 'healthy',
				'compiled': self.compiled_graph is not None,
			}

			# Determine overall status
			component_statuses = [comp.get('status') for comp in health_data['components'].values()]
			if any(status == 'unhealthy' for status in component_statuses):
				health_data['status'] = 'degraded'
			elif any(status == 'not_initialized' for status in component_statuses):
				health_data['status'] = 'partial'

			return health_data

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""

		# Check which services are available
		services_status = {
			'qdrant_service': self.qdrant_service is not None,
			'query_optimizer': self.query_optimizer is not None,
			'knowledge_retriever': self.knowledge_retriever is not None,
		}

		return {
			'name': 'MoneyEZ Enhanced Chat Workflow',
			'version': '2.0.0',
			'description': 'Enhanced LangGraph workflow with QdrantService integration',
			'features': [
				'QdrantService integration',
				'Query optimization',
				'Knowledge retrieval',
				'Basic calculation tools (+, -, *, /)',
				'Vietnamese financial expertise',
				'Production error handling',
				'Performance monitoring',
			],
			'nodes': (['rag_decision', 'retrieve', 'agent', 'tools'] if any(services_status.values()) else ['agent', 'tools']),
			'services': services_status,
			'config': self.config.to_dict() if hasattr(self.config, 'to_dict') else {},
			'compiled': self.compiled_graph is not None,
		}


# Factory function cho easy initialization
def create_chat_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> ChatWorkflow:
	"""
	Factory function để create ChatWorkflow instance
	"""
	return ChatWorkflow(db_session=db_session, config=config)


# Export workflow instance cho compatibility
def get_compiled_workflow(db_session: Session, config: Optional[WorkflowConfig] = None):
	"""
	Get compiled workflow instance cho direct use
	"""
	workflow = create_chat_workflow(db_session, config)
	return workflow.compiled_graph


logger.info('🚀 [System] MoneyEZ Enhanced Chat Workflow ready!')
logger.info('📊 [System] Features: QdrantService, Query Optimization, Knowledge Retrieval, Basic Tools')
logger.info('🔧 [System] Production-ready với comprehensive RAG functionality')
