"""
Production knowledge retriever với QdrantService integration
Real document retrieval từ QdrantDB cho Vietnamese financial content
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set
from langchain_core.documents import Document
from sqlalchemy.orm import Session

from app.modules.agent.services.qdrant_service import QdrantService
from ..config.workflow_config import WorkflowConfig
from ..utils.error_handlers import handle_retrieval_error

logger = logging.getLogger(__name__)


def handle_retrieval_error(error, queries, logger):
	"""Simple error handler fallback"""
	logger.error(f'Retrieval error: {str(error)}')
	return []


class KnowledgeRetriever:
	"""
	Production knowledge retriever với QdrantService

	Features:
	- Real QdrantDB integration
	- Document ranking và deduplication
	- Error handling với graceful degradation
	- Performance monitoring
	- Caching support
	"""

	def __init__(self, db_session: Session, config: WorkflowConfig):
		self.db_session = db_session
		self.config = config
		self.qdrant_service = None
		self.logger = logging.getLogger(__name__)
		self._document_cache: Dict[str, List[Document]] = {}

		# Initialize QdrantService
		self._initialize_qdrant()

	def _initialize_qdrant(self) -> None:
		"""Initialize QdrantService connection"""
		try:
			self.qdrant_service = QdrantService(self.db_session)

			# Ensure knowledge collection exists
			collection_created = self.qdrant_service.initialize_collection(
				collection_name=self.config.collection_name,
				vector_size=768,  # Google embedding size
			)

			if collection_created:
				self.logger.info(f'QdrantService initialized successfully for collection: {self.config.collection_name}')
			else:
				self.logger.warning('QdrantService initialization had issues')

		except Exception as e:
			self.logger.error(f'Failed to initialize QdrantService: {str(e)}')
			self.qdrant_service = None

	async def retrieve_documents(
		self,
		queries: List[str],
		collection_name: Optional[str] = None,
		top_k: Optional[int] = None,
		score_threshold: Optional[float] = None,
	) -> List[Document]:
		"""
		Real document retrieval từ QdrantDB

		Args:
		    queries: List of search queries
		    collection_name: Optional collection override
		    top_k: Maximum documents to retrieve
		    score_threshold: Minimum similarity score

		Returns:
		    List of ranked Document objects
		"""
		start_time = time.time()

		try:
			# Validate inputs
			if not queries:
				self.logger.warning('No queries provided for retrieval')
				return []

			# Use config defaults if not provided
			collection = collection_name or self.config.collection_name
			max_docs = top_k or self.config.max_retrieved_docs
			threshold = score_threshold or self.config.similarity_threshold

			# Check if QdrantService is available
			if not self.qdrant_service:
				self.logger.error('QdrantService not available - using fallback')
				return self._fallback_retrieval(queries)

			# Check cache if enabled
			if self.config.enable_caching:
				cache_key = self._generate_cache_key(queries, collection, max_docs, threshold)
				cached_docs = self._get_cached_documents(cache_key)
				if cached_docs:
					self.logger.info(f'Retrieved {len(cached_docs)} documents from cache')
					return cached_docs

			# Perform retrieval for each query
			all_documents = []

			for query in queries:
				try:
					# Use QdrantService similarity search
					docs = self.qdrant_service.similarity_search(
						query=query,
						collection_name=collection,
						top_k=max_docs,
						score_threshold=threshold,
					)

					all_documents.extend(docs)
					self.logger.debug(f"Retrieved {len(docs)} documents for query: '{query[:50]}...'")

				except Exception as e:
					self.logger.error(f"Error retrieving documents for query '{query}': {str(e)}")
					continue

			# Process và rank documents
			processed_docs = self._process_retrieved_documents(documents=all_documents, queries=queries, max_docs=max_docs)

			# Cache results if enabled
			if self.config.enable_caching and processed_docs:
				self._cache_documents(cache_key, processed_docs)

			# Log performance metrics
			retrieval_time = time.time() - start_time
			self.logger.info(f'Retrieved {len(processed_docs)} documents in {retrieval_time:.2f}s from {len(queries)} queries')

			return processed_docs

		except Exception as e:
			return handle_retrieval_error(e, queries, self.logger)

	def _process_retrieved_documents(self, documents: List[Document], queries: List[str], max_docs: int) -> List[Document]:
		"""
		Process, deduplicate và rank retrieved documents
		"""
		if not documents:
			return []

		# Deduplicate documents
		unique_docs = self._deduplicate_documents(documents)

		# Rank documents based on relevance
		ranked_docs = self._rank_documents(unique_docs, queries)

		# Apply scoring và filtering
		scored_docs = self._apply_relevance_scoring(ranked_docs, queries)

		# Return top documents
		return scored_docs[:max_docs]

	def _deduplicate_documents(self, documents: List[Document]) -> List[Document]:
		"""Remove duplicate documents based on content similarity"""
		if not documents:
			return []

		unique_docs = []
		seen_content: Set[str] = set()

		for doc in documents:
			# Create content hash cho deduplication
			content_hash = hash(doc.page_content.strip().lower())

			if content_hash not in seen_content:
				seen_content.add(content_hash)
				unique_docs.append(doc)

		self.logger.debug(f'Deduplicated {len(documents)} -> {len(unique_docs)} documents')
		return unique_docs

	def _rank_documents(self, documents: List[Document], queries: List[str]) -> List[Document]:
		"""
		Rank documents based on multiple factors:
		- Similarity score
		- Query relevance
		- Content quality
		"""
		if not documents:
			return []

		# Sort by similarity score (primary ranking)
		ranked = sorted(documents, key=lambda x: x.metadata.get('similarity_score', 0), reverse=True)

		# Apply additional ranking factors
		for doc in ranked:
			base_score = doc.metadata.get('similarity_score', 0)

			# Boost score based on content quality
			quality_boost = self._calculate_content_quality_score(doc.page_content)

			# Boost score based on query keyword matching
			keyword_boost = self._calculate_keyword_relevance(doc.page_content, queries)

			# Calculate final score
			final_score = base_score + (quality_boost * 0.1) + (keyword_boost * 0.2)
			doc.metadata['final_score'] = final_score

		# Re-sort by final score
		return sorted(ranked, key=lambda x: x.metadata.get('final_score', 0), reverse=True)

	def _apply_relevance_scoring(self, documents: List[Document], queries: List[str]) -> List[Document]:
		"""Apply final relevance scoring và filtering"""

		# Filter documents below minimum relevance threshold
		min_relevance = 0.3  # Configurable threshold

		relevant_docs = []
		for doc in documents:
			final_score = doc.metadata.get('final_score', 0)
			similarity_score = doc.metadata.get('similarity_score', 0)

			# Keep documents above threshold
			if similarity_score >= min_relevance:
				# Add relevance metadata
				doc.metadata.update({
					'relevance_tier': self._get_relevance_tier(final_score),
					'query_match_count': self._count_query_matches(doc.page_content, queries),
					'processed_at': time.time(),
				})
				relevant_docs.append(doc)

		self.logger.debug(f'Filtered to {len(relevant_docs)} relevant documents')
		return relevant_docs

	def _calculate_content_quality_score(self, content: str) -> float:
		"""Calculate content quality score based on various factors"""
		if not content:
			return 0.0

		quality_score = 0.0

		# Length factor (prefer moderate length)
		length = len(content)
		if 200 <= length <= 2000:
			quality_score += 0.3
		elif 100 <= length < 200 or 2000 < length <= 5000:
			quality_score += 0.1

		# Structure factor (prefer well-structured content)
		if '.' in content and len(content.split('.')) >= 3:
			quality_score += 0.2

		# Financial terminology factor
		financial_terms = [
			'tài chính',
			'ngân hàng',
			'đầu tư',
			'tiết kiệm',
			'bảo hiểm',
			'lãi suất',
			'cổ phiếu',
			'trái phiếu',
			'quỹ đầu tư',
		]

		content_lower = content.lower()
		term_count = sum(1 for term in financial_terms if term in content_lower)
		quality_score += min(term_count * 0.1, 0.5)

		return min(quality_score, 1.0)

	def _calculate_keyword_relevance(self, content: str, queries: List[str]) -> float:
		"""Calculate keyword relevance score"""
		if not content or not queries:
			return 0.0

		content_lower = content.lower()
		total_relevance = 0.0

		for query in queries:
			query_words = query.lower().split()
			matches = sum(1 for word in query_words if word in content_lower)
			query_relevance = matches / len(query_words) if query_words else 0
			total_relevance += query_relevance

		return min(total_relevance / len(queries), 1.0)

	def _count_query_matches(self, content: str, queries: List[str]) -> int:
		"""Count how many queries have matches in content"""
		if not content or not queries:
			return 0

		content_lower = content.lower()
		matches = 0

		for query in queries:
			if any(word.lower() in content_lower for word in query.split()):
				matches += 1

		return matches

	def _get_relevance_tier(self, score: float) -> str:
		"""Get relevance tier based on score"""
		if score >= 0.8:
			return 'high'
		elif score >= 0.6:
			return 'medium'
		elif score >= 0.4:
			return 'low'
		else:
			return 'minimal'

	def _generate_cache_key(self, queries: List[str], collection: str, max_docs: int, threshold: float) -> str:
		"""Generate cache key cho document caching"""
		import hashlib

		key_data = f'{collection}:{max_docs}:{threshold}:{":".join(sorted(queries))}'
		return hashlib.md5(key_data.encode()).hexdigest()

	def _get_cached_documents(self, cache_key: str) -> Optional[List[Document]]:
		"""Get documents from cache"""
		return self._document_cache.get(cache_key)

	def _cache_documents(self, cache_key: str, documents: List[Document]) -> None:
		"""Cache documents with TTL"""
		# Simple in-memory cache - in production, use Redis or similar
		if len(self._document_cache) > 100:  # Simple cache size limit
			# Remove oldest entries
			oldest_key = next(iter(self._document_cache))
			del self._document_cache[oldest_key]

		self._document_cache[cache_key] = documents

	def _fallback_retrieval(self, queries: List[str]) -> List[Document]:
		"""Fallback retrieval when QdrantService is unavailable"""
		self.logger.warning('Using fallback retrieval - QdrantService unavailable')

		# Return empty list gracefully
		# In production, có thể implement backup retrieval mechanism
		return []

	async def get_collection_stats(self) -> Dict[str, Any]:
		"""Get collection statistics từ QdrantService"""
		try:
			if not self.qdrant_service:
				return {'error': 'QdrantService not available'}

			stats = self.qdrant_service.get_collection_stats(self.config.collection_name)
			return stats

		except Exception as e:
			self.logger.error(f'Error getting collection stats: {str(e)}')
			return {'error': str(e)}

	async def health_check(self) -> Dict[str, Any]:
		"""Health check cho retrieval system"""
		try:
			# Check QdrantService availability
			if not self.qdrant_service:
				return {'status': 'unhealthy', 'error': 'QdrantService not initialized'}

			# Try to get collection info
			collections = self.qdrant_service.list_collections()

			return {
				'status': 'healthy',
				'qdrant_available': True,
				'collections': collections,
				'target_collection': self.config.collection_name,
				'cache_size': len(self._document_cache),
			}

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e)}
