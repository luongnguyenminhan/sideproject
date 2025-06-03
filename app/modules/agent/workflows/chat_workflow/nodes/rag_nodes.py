"""
Production RAG node implementations
Advanced RAG pipeline với QdrantService integration
"""

import logging
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from ..state.workflow_state import AgentState, StateManager
from ..config.workflow_config import WorkflowConfig
from ..knowledge.retriever import KnowledgeRetriever
from ..knowledge.query_optimizer import QueryOptimizer
from ..utils.error_handlers import handle_errors, RAGError
from ..utils.message_utils import MessageProcessor, ConversationAnalyzer

logger = logging.getLogger(__name__)


class RAGNodes:
	"""
	Production RAG node implementations

	Features:
	- Smart RAG decision logic
	- Advanced query optimization
	- Real QdrantService integration
	- Performance monitoring
	- Error handling với graceful degradation
	"""

	def __init__(self, db_session: Session, config: WorkflowConfig):
		self.db_session = db_session
		self.config = config
		self.retriever = KnowledgeRetriever(db_session, config)
		self.optimizer = QueryOptimizer(config)
		self.logger = logging.getLogger(__name__)

	@handle_errors(fallback_response='Tôi sẽ cố gắng trả lời dựa trên kiến thức có sẵn.', error_type='rag_decision')
	async def should_use_rag(self, state: AgentState, config: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Smart RAG decision với advanced logic

		Decision factors:
		- Knowledge keywords detection
		- Question type classification
		- Context dependency analysis
		- Conversation history analysis
		"""
		start_time = time.time()

		try:
			self.logger.info('🔍 [RAG Decision] Starting RAG analysis...')

			# Check if RAG is enabled
			use_rag_setting = config.get('configurable', {}).get('use_rag', True)
			if not use_rag_setting:
				self.logger.info('📝 [RAG Decision] RAG disabled in config')
				return {'need_rag': False, 'queries': []}

			# Extract last user message
			user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

			if not user_message:
				self.logger.warning('📝 [RAG Decision] No user message found')
				return {'need_rag': False, 'queries': []}

			# Analyze conversation context
			conversation_analysis = ConversationAnalyzer.analyze_conversation_flow(state.get('messages', []))

			# Multiple decision factors
			decision_factors = {}

			# 1. Keyword matching
			keyword_match = self._check_knowledge_keywords(user_message)
			decision_factors['keyword_match'] = keyword_match

			# 2. Question type classification
			question_type = self._classify_question_type(user_message)
			decision_factors['question_type'] = question_type

			# 3. Context dependency
			context_dependency = self._check_context_dependency(state, conversation_analysis)
			decision_factors['context_dependency'] = context_dependency

			# 4. Financial relevance
			financial_relevance = self._assess_financial_relevance(user_message)
			decision_factors['financial_relevance'] = financial_relevance

			# 5. Complexity analysis
			complexity_score = self._analyze_query_complexity(user_message)
			decision_factors['complexity_score'] = complexity_score

			# Smart decision logic
			need_rag = self._make_rag_decision(decision_factors)

			# Calculate processing time
			processing_time = time.time() - start_time

			self.logger.info(f'📝 [RAG Decision] Decision: {need_rag} (processed in {processing_time:.2f}s)')

			# Update state with decision metadata
			updated_state = StateManager.add_processing_time(state, 'rag_decision', processing_time)

			return {**updated_state, 'need_rag': need_rag, 'rag_decision_factors': decision_factors, 'queries': []}

		except Exception as e:
			self.logger.error(f'Error in RAG decision: {str(e)}')
			raise RAGError(f'RAG decision failed: {str(e)}', 'rag_decision')

	@handle_errors(fallback_response='Tôi sẽ sử dụng truy vấn đơn giản cho tìm kiếm.', error_type='query_generation')
	async def generate_query(self, state: AgentState, config: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Generate optimized search queries cho RAG retrieval
		"""
		start_time = time.time()

		try:
			self.logger.info('🔍 [Query Generation] Starting query optimization...')

			# Extract user message
			user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

			if not user_message:
				self.logger.warning('No user message found for query generation')
				return {'queries': []}

			# Extract conversation context
			conversation_history = MessageProcessor.extract_conversation_history(state.get('messages', []), limit=5)

			context_messages = [msg['content'] for msg in conversation_history if msg['role'] == 'user']

			# Use query optimizer
			optimized_queries = self.optimizer.optimize_queries(user_message=user_message, conversation_context=context_messages)

			# Analyze queries
			query_analysis = self.optimizer.analyze_query(user_message)

			# Create optimization metadata
			optimization_metadata = {
				'original_query': user_message,
				'optimized_count': len(optimized_queries),
				'intent_type': query_analysis.intent_type,
				'confidence_score': query_analysis.confidence_score,
				'financial_terms': query_analysis.financial_terms,
				'key_concepts': query_analysis.key_concepts,
				'processing_time': time.time() - start_time,
			}

			self.logger.info(f'📝 [Query Generation] Generated {len(optimized_queries)} queries (intent: {query_analysis.intent_type}, confidence: {query_analysis.confidence_score:.2f})')

			return {'queries': optimized_queries, 'query_optimization_metadata': optimization_metadata}

		except Exception as e:
			self.logger.error(f'Error in query generation: {str(e)}')
			# Fallback to simple query
			user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))
			return {'queries': [user_message] if user_message else []}

	@handle_errors(fallback_response='Không thể tìm kiếm thông tin lúc này, tôi sẽ trả lời dựa trên kiến thức có sẵn.', error_type='knowledge_retrieval')
	async def retrieve_knowledge(self, state: AgentState, config: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Real knowledge retrieval implementation với QdrantService
		"""
		start_time = time.time()

		try:
			self.logger.info('🔍 [Knowledge Retrieval] Starting document retrieval...')

			queries = state.get('queries', [])
			if not queries:
				self.logger.warning('No queries provided for retrieval')
				return {'rag_context': [], 'retrieved_docs': []}

			# Validate queries
			from ..utils.error_handlers import Validator

			if not Validator.validate_queries(queries):
				self.logger.warning('Invalid queries detected')
				return {'rag_context': [], 'retrieved_docs': []}

			# Get collection name từ config override hoặc default
			collection_name = config.get('collection_name', self.config.collection_name)

			# Perform retrieval
			retrieved_docs = await self.retriever.retrieve_documents(
				queries=queries, collection_name=collection_name, top_k=self.config.max_retrieved_docs, score_threshold=self.config.similarity_threshold
			)

			# Validate retrieved documents
			if not Validator.validate_documents(retrieved_docs):
				self.logger.warning('Invalid documents retrieved')
				retrieved_docs = []

			# Extract context for prompt
			rag_context = []
			if retrieved_docs:
				rag_context = [doc.page_content for doc in retrieved_docs]

			# Create retrieval metadata
			retrieval_metadata = {
				'query_count': len(queries),
				'doc_count': len(retrieved_docs),
				'context_length': sum(len(ctx) for ctx in rag_context),
				'avg_score': self._calculate_avg_score(retrieved_docs),
				'score_distribution': self._get_score_distribution(retrieved_docs),
				'relevance_tiers': self._get_relevance_tiers(retrieved_docs),
				'processing_time': time.time() - start_time,
			}

			self.logger.info(f'📝 [Knowledge Retrieval] Retrieved {len(retrieved_docs)} documents (avg score: {retrieval_metadata["avg_score"]:.3f})')

			# Log document summaries
			for i, doc in enumerate(retrieved_docs[:3]):  # Log first 3
				preview = doc.page_content[:100] + '...' if len(doc.page_content) > 100 else doc.page_content
				score = doc.metadata.get('similarity_score', 0)
				self.logger.debug(f'📄 [Doc {i + 1}] Score: {score:.3f} - {preview}')

			return {'rag_context': rag_context, 'retrieved_docs': retrieved_docs, 'retrieval_metadata': retrieval_metadata}

		except Exception as e:
			self.logger.error(f'Error in knowledge retrieval: {str(e)}')
			# Graceful degradation
			return {'rag_context': [], 'retrieved_docs': [], 'retrieval_metadata': {'error': str(e), 'query_count': len(state.get('queries', [])), 'doc_count': 0}}

	def _check_knowledge_keywords(self, message: str) -> bool:
		"""Check for knowledge-requiring keywords"""
		message_lower = message.lower()

		# Direct keyword matching
		keyword_matches = sum(1 for keyword in self.config.knowledge_keywords if keyword in message_lower)

		# Weight based on keyword frequency
		return keyword_matches >= 1

	def _classify_question_type(self, message: str) -> str:
		"""Classify question type for RAG decision"""
		message_lower = message.lower()

		# Check question patterns
		for question_type, patterns in self.config.question_types.items():
			for pattern in patterns:
				if pattern in message_lower:
					return question_type

		# Default classification based on question words
		question_words = ['gì', 'sao', 'nào', 'thế nào', 'tại sao', 'vì sao']
		if any(word in message_lower for word in question_words):
			return 'information'

		return 'general'

	def _check_context_dependency(self, state: AgentState, conversation_analysis: Dict[str, Any]) -> bool:
		"""Check if query depends on conversation context"""

		# Check for context-dependent indicators
		user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

		if not user_message:
			return False

		context_indicators = ['đó', 'này', 'trên', 'như vậy', 'theo như', 'dựa trên', 'tiếp theo', 'thêm', 'chi tiết', 'cụ thể hơn']

		return any(indicator in user_message.lower() for indicator in context_indicators)

	def _assess_financial_relevance(self, message: str) -> float:
		"""Assess financial relevance of query"""
		message_lower = message.lower()

		# Count financial terms
		financial_term_count = sum(1 for term in self.config.financial_terms if term in message_lower)

		# Score based on term density
		word_count = len(message.split())
		if word_count == 0:
			return 0.0

		relevance_score = min(financial_term_count / word_count * 5, 1.0)
		return relevance_score

	def _analyze_query_complexity(self, message: str) -> float:
		"""Analyze query complexity to determine RAG necessity"""

		# Factors that increase complexity
		complexity_score = 0.0

		# Word count factor
		word_count = len(message.split())
		if word_count > 10:
			complexity_score += 0.3
		elif word_count > 5:
			complexity_score += 0.1

		# Question complexity indicators
		complex_indicators = ['so sánh', 'khác nhau', 'ưu nhược điểm', 'phân tích', 'đánh giá', 'tư vấn', 'lựa chọn', 'quyết định']

		message_lower = message.lower()
		complexity_matches = sum(1 for indicator in complex_indicators if indicator in message_lower)

		complexity_score += min(complexity_matches * 0.2, 0.5)

		return min(complexity_score, 1.0)

	def _make_rag_decision(self, decision_factors: Dict[str, Any]) -> bool:
		"""Make final RAG decision based on multiple factors"""

		# Weighted scoring
		weights = {'keyword_match': 0.3, 'financial_relevance': 0.3, 'complexity_score': 0.2, 'context_dependency': 0.1, 'question_type': 0.1}

		score = 0.0

		# Keyword match
		if decision_factors.get('keyword_match', False):
			score += weights['keyword_match']

		# Financial relevance
		score += decision_factors.get('financial_relevance', 0) * weights['financial_relevance']

		# Complexity score
		score += decision_factors.get('complexity_score', 0) * weights['complexity_score']

		# Context dependency
		if decision_factors.get('context_dependency', False):
			score += weights['context_dependency']

		# Question type
		question_type = decision_factors.get('question_type', 'general')
		if question_type in ['information', 'explanation', 'comparison', 'advice']:
			score += weights['question_type']

		# Decision threshold
		decision_threshold = 0.3
		return score >= decision_threshold

	def _calculate_avg_score(self, docs: List) -> float:
		"""Calculate average similarity score of documents"""
		if not docs:
			return 0.0

		scores = [doc.metadata.get('similarity_score', 0) for doc in docs if hasattr(doc, 'metadata') and doc.metadata]

		return sum(scores) / len(scores) if scores else 0.0

	def _get_score_distribution(self, docs: List) -> Dict[str, int]:
		"""Get distribution of similarity scores"""
		distribution = {'high': 0, 'medium': 0, 'low': 0}

		for doc in docs:
			if hasattr(doc, 'metadata') and doc.metadata:
				score = doc.metadata.get('similarity_score', 0)
				if score >= 0.8:
					distribution['high'] += 1
				elif score >= 0.6:
					distribution['medium'] += 1
				else:
					distribution['low'] += 1

		return distribution

	def _get_relevance_tiers(self, docs: List) -> Dict[str, int]:
		"""Get relevance tier distribution"""
		tiers = {'high': 0, 'medium': 0, 'low': 0, 'minimal': 0}

		for doc in docs:
			if hasattr(doc, 'metadata') and doc.metadata:
				tier = doc.metadata.get('relevance_tier', 'minimal')
				if tier in tiers:
					tiers[tier] += 1

		return tiers

	async def health_check(self) -> Dict[str, Any]:
		"""Health check cho RAG system"""
		try:
			# Check retriever health
			retriever_health = await self.retriever.health_check()

			return {
				'status': 'healthy' if retriever_health['status'] == 'healthy' else 'unhealthy',
				'retriever': retriever_health,
				'optimizer': {'status': 'healthy', 'config_loaded': True},
				'timestamp': time.time(),
			}

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}
