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
from .utils.color_logger import get_color_logger, Colors

logger = logging.getLogger(__name__)
color_logger = get_color_logger(__name__)


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
		self.start_time = time.time()
		color_logger.workflow_start(
			'ChatWorkflow Initialization',
			db_session_type=type(db_session).__name__,
			config_provided=config is not None,
		)

		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		print('^^' * 100, f'Config: {self.config.to_dict()}')

		color_logger.info(
			f'⚙️ {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} Workflow configuration loaded',
			Colors.CYAN,
			model_name=self.config.model_name,
			rag_enabled=self.config.rag_enabled,
			temperature=self.config.temperature,
			collection_name=self.config.collection_name,
		)

		# Initialize services
		self.qdrant_service = None
		self.query_optimizer = None
		self.knowledge_retriever = None

		try:
			# Initialize RAG services
			color_logger.info(
				f'🔧 {Colors.BOLD}INITIALIZING:{Colors.RESET}{Colors.YELLOW} RAG services...',
				Colors.YELLOW,
			)

			self.qdrant_service = QdrantService(db_session)
			color_logger.success(
				'QdrantService initialized successfully',
				service='QdrantService',
				status='ready',
			)

			self.query_optimizer = QueryOptimizer(self.config)
			color_logger.success(
				'QueryOptimizer initialized successfully',
				service='QueryOptimizer',
				keywords_available=len(self.config.knowledge_keywords),
			)

			self.knowledge_retriever = KnowledgeRetriever(db_session, self.config)
			color_logger.success(
				'KnowledgeRetriever initialized successfully',
				service='KnowledgeRetriever',
				similarity_threshold=self.config.similarity_threshold,
			)

			# Use RAG-enabled workflow
			self.compiled_graph = create_workflow_with_rag(db_session, self.config)

			color_logger.success(
				'🚀 ChatWorkflow initialized with RAG functionality',
				initialization_time=time.time() - self.start_time,
				workflow_type='RAG-enabled',
				services_count=3,
			)

		except Exception as e:
			color_logger.error(
				f'RAG initialization failed: {str(e)}, using basic workflow',
				error_type=type(e).__name__,
				fallback_mode=True,
			)

			# Fallback to basic workflow
			self.compiled_graph = basic_workflow

			color_logger.warning(
				'🔄 Fallback to basic workflow activated',
				workflow_type='basic',
				rag_available=False,
			)

		initialization_time = time.time() - self.start_time
		color_logger.workflow_complete(
			'ChatWorkflow Initialization',
			initialization_time,
			workflow_ready=True,
			rag_services_available=all([self.qdrant_service, self.query_optimizer, self.knowledge_retriever]),
		)

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
		processing_session = session_id or 'default'

		color_logger.workflow_start(
			'Message Processing',
			user_id=user_id,
			session_id=processing_session,
			message_length=len(user_message),
			has_config_override=bool(config_override),
		)

		color_logger.info(
			f"📨 {Colors.BOLD}INPUT_MESSAGE:{Colors.RESET}{Colors.BRIGHT_CYAN} '{user_message[:100]}{'...' if len(user_message) > 100 else ''}'",
			Colors.BRIGHT_CYAN,
			full_length=len(user_message),
			word_count=len(user_message.split()),
		)

		try:
			# Create initial state
			from langchain_core.messages import HumanMessage

			initial_state = {'messages': [HumanMessage(content=user_message)]}
			color_logger.info(
				f'🏗️ {Colors.BOLD}STATE:{Colors.RESET}{Colors.MAGENTA} Initial state created',
				Colors.MAGENTA,
				message_type='HumanMessage',
			)

			# Prepare config
			runtime_config = {
				'configurable': {
					'thread_id': processing_session,
					'system_prompt': getattr(self.config, 'system_prompt', None),
					'use_rag': (self.config.rag_enabled if hasattr(self.config, 'rag_enabled') else True),
					**self.config.to_dict(),
				}
			}

			if config_override:
				runtime_config['configurable'].update(config_override)
				color_logger.info(
					f'🔧 {Colors.BOLD}CONFIG_OVERRIDE:{Colors.RESET}{Colors.YELLOW} Applied',
					Colors.YELLOW,
					overrides_count=len(config_override),
				)

			color_logger.info(
				f'⚙️ {Colors.BOLD}RUNTIME_CONFIG:{Colors.RESET}{Colors.DIM} Prepared',
				Colors.DIM,
				thread_id=processing_session,
				rag_enabled=runtime_config['configurable'].get('use_rag', False),
			)

			# Execute workflow
			color_logger.info(
				f'🚀 {Colors.BOLD}EXECUTING:{Colors.RESET}{Colors.BRIGHT_YELLOW} Workflow invocation',
				Colors.BRIGHT_YELLOW,
			)
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)

			# Extract response
			response = self._extract_response(final_state)

			color_logger.info(
				f'📤 {Colors.BOLD}RESPONSE:{Colors.RESET}{Colors.BRIGHT_GREEN} Generated',
				Colors.BRIGHT_GREEN,
				response_length=len(response),
				response_preview=(response[:100] + '...' if len(response) > 100 else response),
			)

			# Calculate processing metrics
			processing_time = time.time() - start_time
			rag_sources_count = len(final_state.get('rag_context', []))

			color_logger.performance_metric(
				'processing_time',
				f'{processing_time:.3f}',
				's',
				session_id=processing_session,
			)
			color_logger.performance_metric('rag_sources', rag_sources_count, '', session_id=processing_session)

			result = {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'rag_used': bool(final_state.get('rag_context')),
					'rag_sources': rag_sources_count,
					'user_id': user_id,
					'session_id': processing_session,
				},
			}

			color_logger.workflow_complete(
				'Message Processing',
				processing_time,
				success=True,
				rag_used=result['metadata']['rag_used'],
				response_generated=True,
				session_id=processing_session,
			)

			return result

		except Exception as e:
			processing_time = time.time() - start_time
			color_logger.error(
				f'Message processing failed: {str(e)}',
				error_type=type(e).__name__,
				processing_time=processing_time,
				session_id=processing_session,
				user_message_preview=user_message[:50],
			)

			# Create fallback response
			fallback_response = 'Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau hoặc đặt câu hỏi khác.'

			color_logger.warning(
				f'🔄 {Colors.BOLD}FALLBACK:{Colors.RESET}{Colors.BRIGHT_YELLOW} Using fallback response',
				Colors.BRIGHT_YELLOW,
				fallback_length=len(fallback_response),
			)

			return {
				'response': fallback_response,
				'error': str(e),
				'metadata': {
					'processing_time': processing_time,
					'error_occurred': True,
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response từ final state"""
		color_logger.debug(
			'🔍 Extracting response from final state',
			state_keys=list(final_state.keys()),
			messages_count=len(final_state.get('messages', [])),
		)

		messages = final_state.get('messages', [])
		if not messages:
			color_logger.warning('No messages in final state')
			return 'Không thể tạo phản hồi.'

		# Get last AI message
		for i, message in enumerate(reversed(messages)):
			if hasattr(message, 'content') and message.content:
				content = message.content
				if content and content.strip():
					color_logger.debug(
						f'Response extracted from message #{len(messages) - i}',
						content_length=len(content),
						message_type=type(message).__name__,
					)
					return content

		color_logger.warning('No valid response content found in messages')
		return 'Phản hồi không khả dụng.'

	async def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
		"""Search knowledge base directly"""
		start_time = time.time()
		color_logger.workflow_start('Direct Knowledge Search', query_length=len(query), top_k=top_k)

		color_logger.info(
			f"🔍 {Colors.BOLD}SEARCH_QUERY:{Colors.RESET}{Colors.BRIGHT_BLUE} '{query[:50]}...'",
			Colors.BRIGHT_BLUE,
			full_query_length=len(query),
		)

		try:
			if not self.query_optimizer or not self.knowledge_retriever:
				color_logger.error(
					'RAG services not available for knowledge search',
					optimizer_available=bool(self.query_optimizer),
					retriever_available=bool(self.knowledge_retriever),
				)
				return []

			# Optimize queries
			optimized_queries = self.query_optimizer.optimize_queries(query)
			color_logger.query_optimization(query, len(optimized_queries))

			# Retrieve documents
			documents = await self.knowledge_retriever.retrieve_documents(queries=optimized_queries, top_k=top_k)

			# Format results
			results = []
			for i, doc in enumerate(documents):
				result = {
					'content': doc.page_content,
					'metadata': doc.metadata,
					'score': doc.metadata.get('similarity_score', 0),
				}
				results.append(result)

				color_logger.debug(
					f'Search result #{i + 1}',
					score=result['score'],
					content_length=len(result['content']),
				)

			search_time = time.time() - start_time
			color_logger.workflow_complete(
				'Direct Knowledge Search',
				search_time,
				results_count=len(results),
				avg_score=(sum(r['score'] for r in results) / len(results) if results else 0),
			)

			return results

		except Exception as e:
			color_logger.error(
				f'Error searching knowledge: {str(e)}',
				error_type=type(e).__name__,
				query_preview=query[:50],
			)
			return []

	async def index_documents(self, documents: List[Dict[str, Any]], collection_name: Optional[str] = None) -> Dict[str, Any]:
		"""Index documents to knowledge base"""
		start_time = time.time()
		color_logger.workflow_start(
			'Document Indexing',
			document_count=len(documents),
			target_collection=collection_name or self.config.collection_name,
		)

		try:
			if not self.qdrant_service:
				color_logger.error('QdrantService not available for indexing')
				return {'error': 'QdrantService not available'}

			from langchain_core.documents import Document

			# Convert to Document objects
			doc_objects = []
			total_content_length = 0
			for i, doc in enumerate(documents):
				content = doc.get('content', '')
				metadata = doc.get('metadata', {})
				doc_objects.append(Document(page_content=content, metadata=metadata))
				total_content_length += len(content)

				color_logger.debug(
					f'Document #{i + 1} prepared for indexing',
					content_length=len(content),
					metadata_keys=list(metadata.keys()),
				)

			color_logger.info(
				f'📊 {Colors.BOLD}INDEXING_PREP:{Colors.RESET}{Colors.MAGENTA} Documents prepared',
				Colors.MAGENTA,
				total_docs=len(doc_objects),
				total_content_length=total_content_length,
			)

			# Index documents
			collection = collection_name or self.config.collection_name
			result = self.qdrant_service.index_documents(doc_objects, collection)

			indexing_time = time.time() - start_time
			indexed_count = result.get('total_indexed', 0)

			color_logger.success(
				f'Documents indexed successfully',
				indexed_count=indexed_count,
				collection=collection,
				indexing_time=indexing_time,
			)

			color_logger.workflow_complete(
				'Document Indexing',
				indexing_time,
				success=True,
				indexed_count=indexed_count,
			)

			return result

		except Exception as e:
			color_logger.error(
				f'Error indexing documents: {str(e)}',
				error_type=type(e).__name__,
				document_count=len(documents),
			)
			return {'error': str(e)}

	async def get_knowledge_stats(self) -> Dict[str, Any]:
		"""Get knowledge base statistics"""
		color_logger.info(
			f'📊 {Colors.BOLD}STATS_REQUEST:{Colors.RESET}{Colors.CYAN} Getting knowledge base stats',
			Colors.CYAN,
		)

		try:
			if not self.qdrant_service:
				color_logger.warning('QdrantService not available for stats')
				return {'error': 'QdrantService not available'}

			stats = self.qdrant_service.get_collection_stats(self.config.collection_name)

			color_logger.info(
				f'📈 {Colors.BOLD}STATS_RETRIEVED:{Colors.RESET}{Colors.BRIGHT_GREEN} Collection statistics',
				Colors.BRIGHT_GREEN,
				collection=self.config.collection_name,
				**{k: v for k, v in stats.items() if isinstance(v, (int, float, str))},
			)

			return stats

		except Exception as e:
			color_logger.error(f'Error getting knowledge stats: {str(e)}', error_type=type(e).__name__)
			return {'error': str(e)}

	async def health_check(self) -> Dict[str, Any]:
		"""Comprehensive health check"""
		start_time = time.time()
		color_logger.workflow_start('Health Check', comprehensive=True)

		try:
			health_data = {
				'status': 'healthy',
				'components': {},
				'timestamp': time.time(),
			}

			# Check QdrantService
			color_logger.info(
				f'🔍 {Colors.BOLD}CHECKING:{Colors.RESET}{Colors.YELLOW} QdrantService health',
				Colors.YELLOW,
			)
			if self.qdrant_service:
				try:
					collections = self.qdrant_service.list_collections()
					health_data['components']['qdrant'] = {
						'status': 'healthy',
						'collections': collections,
					}
					color_logger.health_check('QdrantService', 'healthy', collections_count=len(collections))
				except Exception as e:
					health_data['components']['qdrant'] = {
						'status': 'unhealthy',
						'error': str(e),
					}
					color_logger.health_check('QdrantService', 'unhealthy', error=str(e))
			else:
				health_data['components']['qdrant'] = {'status': 'not_initialized'}
				color_logger.health_check('QdrantService', 'not_initialized')

			# Check Query Optimizer
			optimizer_status = 'healthy' if self.query_optimizer else 'not_initialized'
			health_data['components']['query_optimizer'] = {'status': optimizer_status}
			color_logger.health_check('QueryOptimizer', optimizer_status)

			# Check Knowledge Retriever
			color_logger.info(
				f'🔍 {Colors.BOLD}CHECKING:{Colors.RESET}{Colors.YELLOW} KnowledgeRetriever health',
				Colors.YELLOW,
			)
			if self.knowledge_retriever:
				retriever_health = await self.knowledge_retriever.health_check()
				health_data['components']['knowledge_retriever'] = retriever_health
				color_logger.health_check('KnowledgeRetriever', retriever_health.get('status', 'unknown'))
			else:
				health_data['components']['knowledge_retriever'] = {'status': 'not_initialized'}
				color_logger.health_check('KnowledgeRetriever', 'not_initialized')

			# Check workflow
			workflow_status = 'healthy' if self.compiled_graph else 'unhealthy'
			health_data['components']['workflow'] = {
				'status': workflow_status,
				'compiled': self.compiled_graph is not None,
			}
			color_logger.health_check('Workflow', workflow_status, compiled=bool(self.compiled_graph))

			# Determine overall status
			component_statuses = [comp.get('status') for comp in health_data['components'].values()]
			if any(status == 'unhealthy' for status in component_statuses):
				health_data['status'] = 'degraded'
			elif any(status == 'not_initialized' for status in component_statuses):
				health_data['status'] = 'partial'

			check_time = time.time() - start_time
			color_logger.workflow_complete(
				'Health Check',
				check_time,
				overall_status=health_data['status'],
				components_checked=len(health_data['components']),
			)

			return health_data

		except Exception as e:
			color_logger.error(f'Health check failed: {str(e)}', error_type=type(e).__name__)
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""
		color_logger.info(
			f'ℹ️ {Colors.BOLD}INFO_REQUEST:{Colors.RESET}{Colors.BRIGHT_WHITE} Getting workflow information',
			Colors.BRIGHT_WHITE,
		)

		# Check which services are available
		services_status = {
			'qdrant_service': self.qdrant_service is not None,
			'query_optimizer': self.query_optimizer is not None,
			'knowledge_retriever': self.knowledge_retriever is not None,
		}

		workflow_info = {
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

		color_logger.info(
			f'📋 {Colors.BOLD}WORKFLOW_INFO:{Colors.RESET}{Colors.BRIGHT_CYAN} Information compiled',
			Colors.BRIGHT_CYAN,
			version=workflow_info['version'],
			features_count=len(workflow_info['features']),
			nodes_count=len(workflow_info['nodes']),
			services_available=sum(services_status.values()),
		)

		return workflow_info


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


color_logger.success('🚀 MoneyEZ Enhanced Chat Workflow module loaded!')
color_logger.info(
	f'📊 {Colors.BOLD}FEATURES:{Colors.RESET}{Colors.BRIGHT_MAGENTA} QdrantService, Query Optimization, Knowledge Retrieval, Basic Tools',
	Colors.BRIGHT_MAGENTA,
)
color_logger.info(
	f'🔧 {Colors.BOLD}STATUS:{Colors.RESET}{Colors.BRIGHT_GREEN} Production-ready với comprehensive RAG functionality',
	Colors.BRIGHT_GREEN,
)
