"""
Advanced query processing và enhancement cho Vietnamese financial content
Optimize search queries cho better retrieval performance
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from ..config.workflow_config import WorkflowConfig

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
	"""Analysis results cho một query"""

	original_query: str
	cleaned_query: str
	intent_type: str
	financial_terms: List[str]
	key_concepts: List[str]
	confidence_score: float
	suggested_variants: List[str]


class QueryOptimizer:
	"""
	Advanced query processing cho better retrieval

	Features:
	- Vietnamese text normalization
	- Financial term extraction
	- Intent classification
	- Query expansion
	- Synonym handling
	"""

	def __init__(self, config: WorkflowConfig):
		self.config = config
		self.logger = logging.getLogger(__name__)

		# Vietnamese financial synonyms
		self.financial_synonyms = {
			'tiền gửi': ['gửi tiết kiệm', 'tiết kiệm ngân hàng', 'sổ tiết kiệm'],
			'đầu tư': ['investment', 'beđầu tư', 'đầu tư tài chính'],
			'vay tiền': ['vay vốn', 'khoản vay', 'vay ngân hàng', 'tín dụng'],
			'bảo hiểm': ['insurance', 'bh', 'bảo hiểm nhân thọ'],
			'lãi suất': ['lãi xuất', 'tỷ lệ lãi suất', 'interest rate'],
			'cổ phiếu': ['cp', 'stock', 'chứng khoán', 'cổ phần'],
			'trái phiếu': ['bond', 'tp', 'công trái'],
			'quỹ đầu tư': ['fund', 'mutual fund', 'quỹ mở'],
			'thẻ tín dụng': ['credit card', 'thẻ visa', 'thẻ master'],
			'forex': ['ngoại hối', 'fx', 'foreign exchange'],
			'crypto': ['cryptocurrency', 'bitcoin', 'tiền ảo', 'tiền điện tử'],
		}

		# Intent classification patterns
		self.intent_patterns = {
			'definition': [r'\b(là gì|định nghĩa|khái niệm|nghĩa là)\b', r'\b(có nghĩa|ý nghĩa|hiểu như thế nào)\b'],
			'explanation': [r'\b(giải thích|cách thức|hoạt động|làm sao)\b', r'\b(tại sao|vì sao|nguyên nhân)\b'],
			'comparison': [r'\b(so sánh|khác nhau|giống nhau|khác biệt)\b', r'\b(tốt hơn|hơn|vs|versus)\b'],
			'guidance': [r'\b(hướng dẫn|cách làm|thực hiện|bước)\b', r'\b(làm thế nào|how to)\b'],
			'advice': [r'\b(tư vấn|lời khuyên|nên|không nên)\b', r'\b(đề xuất|gợi ý|recommend)\b'],
			'information': [r'\b(thông tin|chi tiết|details|info)\b', r'\b(tìm hiểu|biết thêm|tìm kiếm)\b'],
		}

	def optimize_queries(self, user_message: str, conversation_context: Optional[List[str]] = None) -> List[str]:
		"""
		Generate multiple optimized search queries từ user message

		Args:
		    user_message: Original user message
		    conversation_context: Previous conversation messages

		Returns:
		    List of optimized query strings
		"""
		try:
			# Analyze query
			analysis = self.analyze_query(user_message)

			# Generate query variants
			variants = self._generate_query_variants(analysis)

			# Add context-aware queries nếu có conversation history
			if conversation_context:
				context_queries = self._generate_context_queries(analysis, conversation_context)
				variants.extend(context_queries)

			# Remove duplicates và filter
			unique_queries = self._deduplicate_queries(variants)
			filtered_queries = self._filter_queries(unique_queries)

			# Limit to max queries
			final_queries = filtered_queries[: self.config.max_queries_per_request]

			self.logger.info(f"Generated {len(final_queries)} optimized queries from original: '{user_message[:50]}...'")

			return final_queries

		except Exception as e:
			self.logger.error(f'Error optimizing queries: {str(e)}')
			# Fallback to basic cleaning
			return [self._basic_query_cleaning(user_message)]

	def analyze_query(self, query: str) -> QueryAnalysis:
		"""Perform comprehensive query analysis"""

		# Basic cleaning
		cleaned = self._basic_query_cleaning(query)

		# Intent classification
		intent = self._classify_intent(query)

		# Extract financial terms
		financial_terms = self._extract_financial_terms(query)

		# Extract key concepts
		key_concepts = self._extract_key_concepts(query)

		# Calculate confidence score
		confidence = self._calculate_confidence_score(query, intent, financial_terms, key_concepts)

		# Generate suggested variants
		variants = self._generate_basic_variants(cleaned, financial_terms)

		return QueryAnalysis(
			original_query=query, cleaned_query=cleaned, intent_type=intent, financial_terms=financial_terms, key_concepts=key_concepts, confidence_score=confidence, suggested_variants=variants
		)

	def _basic_query_cleaning(self, query: str) -> str:
		"""Basic query cleaning và normalization"""

		# Convert to lowercase
		cleaned = query.lower().strip()

		# Remove filler words
		for filler in self.config.filler_words:
			cleaned = cleaned.replace(filler, ' ')

		# Remove extra whitespace
		cleaned = re.sub(r'\s+', ' ', cleaned).strip()

		# Remove special characters (keep Vietnamese)
		cleaned = re.sub(r'[^\w\sáàảãạâấầẩẫậăắằẳẵặéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]', ' ', cleaned)

		# Remove extra whitespace again
		cleaned = re.sub(r'\s+', ' ', cleaned).strip()

		return cleaned

	def _classify_intent(self, query: str) -> str:
		"""Classify query intent based on patterns"""

		query_lower = query.lower()

		# Score each intent type
		intent_scores = {}

		for intent_type, patterns in self.intent_patterns.items():
			score = 0
			for pattern in patterns:
				matches = len(re.findall(pattern, query_lower))
				score += matches

			if score > 0:
				intent_scores[intent_type] = score

		# Return highest scoring intent or default
		if intent_scores:
			return max(intent_scores, key=intent_scores.get)
		else:
			return 'information'  # Default intent

	def _extract_financial_terms(self, query: str) -> List[str]:
		"""Extract financial terms từ query"""

		query_lower = query.lower()
		found_terms = []

		# Check direct matches
		for term in self.config.financial_terms:
			if term.lower() in query_lower:
				found_terms.append(term)

		# Check synonyms
		for main_term, synonyms in self.financial_synonyms.items():
			for synonym in synonyms:
				if synonym.lower() in query_lower:
					found_terms.append(main_term)
					break

		return list(set(found_terms))  # Remove duplicates

	def _extract_key_concepts(self, query: str) -> List[str]:
		"""Extract key concepts từ query"""

		# Simple noun extraction (can be enhanced với NLP)
		words = query.lower().split()

		# Filter important words
		stop_words = set([
			'của',
			'là',
			'và',
			'với',
			'trong',
			'có',
			'được',
			'để',
			'một',
			'các',
			'này',
			'đó',
			'khi',
			'như',
			'về',
			'từ',
			'theo',
			'còn',
			'hay',
			'hoặc',
			'nhưng',
			'nếu',
			'mà',
			'tại',
			'đến',
			'cho',
		])

		concepts = []
		for word in words:
			# Keep words that are:
			# - Longer than 2 characters
			# - Not in stop words
			# - Not in filler words
			if len(word) > 2 and word not in stop_words and word not in [fw.lower() for fw in self.config.filler_words]:
				concepts.append(word)

		return concepts[:5]  # Limit to top 5 concepts

	def _calculate_confidence_score(self, query: str, intent: str, financial_terms: List[str], key_concepts: List[str]) -> float:
		"""Calculate confidence score cho query analysis"""

		score = 0.0

		# Query length factor
		word_count = len(query.split())
		if 3 <= word_count <= 15:
			score += 0.3
		elif 2 <= word_count < 3 or 15 < word_count <= 25:
			score += 0.1

		# Intent clarity factor
		if intent != 'information':  # Not default intent
			score += 0.2

		# Financial relevance factor
		score += min(len(financial_terms) * 0.15, 0.3)

		# Key concepts factor
		score += min(len(key_concepts) * 0.05, 0.2)

		return min(score, 1.0)

	def _generate_basic_variants(self, cleaned_query: str, financial_terms: List[str]) -> List[str]:
		"""Generate basic query variants"""

		variants = [cleaned_query]

		# Add variant với financial context
		if financial_terms:
			financial_context = ' '.join(financial_terms)
			variants.append(f'{cleaned_query} {financial_context}')

		# Add variant với common financial suffix
		variants.append(f'{cleaned_query} tài chính')

		# Add synonym variations
		for term in financial_terms:
			if term in self.financial_synonyms:
				for synonym in self.financial_synonyms[term][:2]:  # Max 2 synonyms
					variant = cleaned_query.replace(term, synonym)
					if variant != cleaned_query:
						variants.append(variant)

		return variants

	def _generate_query_variants(self, analysis: QueryAnalysis) -> List[str]:
		"""Generate comprehensive query variants"""

		variants = [analysis.cleaned_query]

		# Add suggested variants
		variants.extend(analysis.suggested_variants)

		# Intent-specific variants
		if analysis.intent_type == 'definition':
			variants.append(f'định nghĩa {analysis.cleaned_query}')
			variants.append(f'{analysis.cleaned_query} là gì')

		elif analysis.intent_type == 'explanation':
			variants.append(f'giải thích {analysis.cleaned_query}')
			variants.append(f'cách thức {analysis.cleaned_query}')

		elif analysis.intent_type == 'comparison':
			variants.append(f'so sánh {analysis.cleaned_query}')
			for concept in analysis.key_concepts[:2]:
				variants.append(f'{concept} khác nhau')

		elif analysis.intent_type == 'guidance':
			variants.append(f'hướng dẫn {analysis.cleaned_query}')
			variants.append(f'cách làm {analysis.cleaned_query}')

		elif analysis.intent_type == 'advice':
			variants.append(f'tư vấn {analysis.cleaned_query}')
			variants.append(f'lời khuyên {analysis.cleaned_query}')

		# Key concept variants
		for concept in analysis.key_concepts[:3]:
			variants.append(f'{concept} tài chính')

		return variants

	def _generate_context_queries(self, analysis: QueryAnalysis, conversation_context: List[str]) -> List[str]:
		"""Generate context-aware queries based on conversation history"""

		context_queries = []

		# Extract topics from recent context
		recent_topics = self._extract_topics_from_context(conversation_context[-3:])

		# Combine current query with context topics
		for topic in recent_topics:
			if topic not in analysis.cleaned_query:
				context_queries.append(f'{analysis.cleaned_query} {topic}')

		return context_queries

	def _extract_topics_from_context(self, context_messages: List[str]) -> List[str]:
		"""Extract main topics từ conversation context"""

		topics = []

		for message in context_messages:
			# Extract financial terms from context
			financial_terms = self._extract_financial_terms(message)
			topics.extend(financial_terms)

		# Return unique topics
		return list(set(topics))

	def _deduplicate_queries(self, queries: List[str]) -> List[str]:
		"""Remove duplicate queries"""

		seen = set()
		unique_queries = []

		for query in queries:
			normalized = query.strip().lower()
			if normalized and normalized not in seen:
				seen.add(normalized)
				unique_queries.append(query)

		return unique_queries

	def _filter_queries(self, queries: List[str]) -> List[str]:
		"""Filter out low-quality queries"""

		filtered = []

		for query in queries:
			# Skip very short queries
			if len(query.strip()) < 3:
				continue

			# Skip queries with only stop words
			words = query.split()
			if all(word.lower() in ['của', 'là', 'và', 'với', 'trong'] for word in words):
				continue

			# Skip overly long queries
			if len(words) > 20:
				continue

			filtered.append(query)

		return filtered

	def get_query_suggestions(self, partial_query: str) -> List[str]:
		"""Get query suggestions cho autocomplete"""

		suggestions = []

		# Common financial query patterns
		patterns = [f'{partial_query} là gì', f'cách {partial_query}', f'{partial_query} ở việt nam', f'lãi suất {partial_query}', f'phí {partial_query}', f'rủi ro {partial_query}']

		return patterns[:5]  # Limit suggestions
