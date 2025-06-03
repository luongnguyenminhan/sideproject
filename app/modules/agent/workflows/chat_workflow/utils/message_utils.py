"""
Message processing utilities cho Chat Workflow
Enhanced message handling và formatting
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class MessageProcessor:
	"""Enhanced message processing utilities"""

	@staticmethod
	def get_message_text(msg: BaseMessage) -> str:
		"""Extract text từ various message formats"""
		if hasattr(msg, 'content'):
			content = msg.content
			if isinstance(content, str):
				return content
			elif isinstance(content, list):
				# Handle complex content (text + images, etc.)
				text_parts = []
				for part in content:
					if isinstance(part, dict) and part.get('type') == 'text':
						text_parts.append(part.get('text', ''))
					elif isinstance(part, str):
						text_parts.append(part)
				return ' '.join(text_parts)
			else:
				return str(content)
		elif isinstance(msg, dict):
			return str(msg.get('content', ''))
		return str(msg)

	@staticmethod
	def extract_last_user_message(messages: List[BaseMessage]) -> Optional[str]:
		"""Extract content từ last user message"""
		for message in reversed(messages):
			if isinstance(message, HumanMessage):
				return MessageProcessor.get_message_text(message)
		return None

	@staticmethod
	def extract_conversation_history(messages: List[BaseMessage], limit: Optional[int] = None, include_system: bool = False) -> List[Dict[str, Any]]:
		"""Extract conversation history trong structured format"""

		history = []

		for message in messages:
			# Skip system messages unless requested
			if isinstance(message, SystemMessage) and not include_system:
				continue

			# Process different message types
			if isinstance(message, HumanMessage):
				role = 'user'
			elif isinstance(message, AIMessage):
				role = 'assistant'
			elif isinstance(message, SystemMessage):
				role = 'system'
			elif isinstance(message, ToolMessage):
				role = 'tool'
			else:
				role = 'unknown'

			history.append({'role': role, 'content': MessageProcessor.get_message_text(message), 'timestamp': getattr(message, 'timestamp', None), 'message_type': message.__class__.__name__})

		# Apply limit
		if limit and len(history) > limit:
			history = history[-limit:]

		return history

	@staticmethod
	def count_messages_by_type(messages: List[BaseMessage]) -> Dict[str, int]:
		"""Count messages by type"""
		counts = {'human': 0, 'ai': 0, 'system': 0, 'tool': 0, 'other': 0}

		for message in messages:
			if isinstance(message, HumanMessage):
				counts['human'] += 1
			elif isinstance(message, AIMessage):
				counts['ai'] += 1
			elif isinstance(message, SystemMessage):
				counts['system'] += 1
			elif isinstance(message, ToolMessage):
				counts['tool'] += 1
			else:
				counts['other'] += 1

		return counts

	@staticmethod
	def create_enhanced_user_message(content: str, user_id: Optional[str] = None, session_id: Optional[str] = None, additional_context: Optional[Dict[str, Any]] = None) -> HumanMessage:
		"""Create enhanced user message với metadata"""

		# Add timestamp context
		current_time = datetime.now(timezone.utc).isoformat()

		# Enhance content với context
		enhanced_content = content
		if additional_context:
			context_info = []
			if user_id:
				context_info.append(f'User ID: {user_id}')
			if session_id:
				context_info.append(f'Session: {session_id}')

			if context_info:
				enhanced_content += f'\n\n[Context: {", ".join(context_info)}]'

		enhanced_content += f'\n[Timestamp: {current_time}]'

		return HumanMessage(content=enhanced_content, additional_kwargs={'user_id': user_id, 'session_id': session_id, 'timestamp': current_time, 'original_content': content})

	@staticmethod
	def create_rag_enhanced_response(response_content: str, rag_context: List[str], retrieved_docs: List[Document], confidence_score: Optional[float] = None) -> AIMessage:
		"""Create AI response enhanced với RAG metadata"""

		# Create metadata about RAG usage
		rag_metadata = {
			'rag_enabled': True,
			'context_count': len(rag_context),
			'documents_count': len(retrieved_docs),
			'confidence_score': confidence_score,
			'timestamp': datetime.now(timezone.utc).isoformat(),
		}

		# Add source information nếu có
		if retrieved_docs:
			sources = []
			for doc in retrieved_docs:
				if hasattr(doc, 'metadata') and doc.metadata:
					source = doc.metadata.get('source', 'unknown')
					score = doc.metadata.get('similarity_score', 0)
					sources.append({'source': source, 'score': score})

			rag_metadata['sources'] = sources

		return AIMessage(content=response_content, additional_kwargs={'rag_metadata': rag_metadata, 'enhanced_response': True})

	@staticmethod
	def validate_message_content(content: str) -> bool:
		"""Validate message content"""
		if not content or not content.strip():
			return False

		if len(content) > 10000:  # Too long
			return False

		# Check for suspicious patterns
		suspicious_patterns = ['javascript:', 'data:', '<script', 'eval(', 'onclick=']

		content_lower = content.lower()
		for pattern in suspicious_patterns:
			if pattern in content_lower:
				return False

		return True


class DocumentFormatter:
	"""Document formatting utilities cho prompts"""

	@staticmethod
	def format_docs_as_xml(docs: List[Document]) -> str:
		"""Format documents as XML cho prompts"""
		if not docs:
			return ''

		formatted = []
		for i, doc in enumerate(docs):
			content = doc.page_content if hasattr(doc, 'page_content') else str(doc)

			# Get metadata
			metadata = ''
			if hasattr(doc, 'metadata') and doc.metadata:
				meta_parts = []
				for key, value in doc.metadata.items():
					if key in ['source', 'similarity_score', 'relevance_tier']:
						meta_parts.append(f"{key}='{value}'")

				if meta_parts:
					metadata = f' {" ".join(meta_parts)}'

			formatted.append(f'<document_{i + 1}{metadata}>\n{content}\n</document_{i + 1}>')

		return '\n\n'.join(formatted)

	@staticmethod
	def format_docs_as_context(docs: List[Document]) -> str:
		"""Format documents as natural context"""
		if not docs:
			return 'Không có thông tin tham khảo.'

		context_parts = []
		for i, doc in enumerate(docs):
			content = doc.page_content if hasattr(doc, 'page_content') else str(doc)

			# Add source if available
			source = ''
			if hasattr(doc, 'metadata') and doc.metadata:
				doc_source = doc.metadata.get('source', '')
				if doc_source:
					source = f' (Nguồn: {doc_source})'

			context_parts.append(f'{i + 1}. {content}{source}')

		return '\n\n'.join(context_parts)

	@staticmethod
	def create_summary_context(docs: List[Document], max_length: int = 1500) -> str:
		"""Create summarized context từ documents"""
		if not docs:
			return ''

		# Combine all content
		all_content = []
		for doc in docs:
			content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
			all_content.append(content)

		combined = ' '.join(all_content)

		# Truncate if too long
		if len(combined) > max_length:
			# Try to truncate at sentence boundary
			truncated = combined[:max_length]
			last_period = truncated.rfind('.')
			if last_period > max_length * 0.8:  # If found near end
				combined = truncated[: last_period + 1]
			else:
				combined = truncated + '...'

		return combined


class ConversationAnalyzer:
	"""Analyze conversation patterns và context"""

	@staticmethod
	def analyze_conversation_flow(messages: List[BaseMessage]) -> Dict[str, Any]:
		"""Analyze conversation flow và patterns"""

		if not messages:
			return {'status': 'empty'}

		message_counts = MessageProcessor.count_messages_by_type(messages)

		# Calculate conversation metrics
		total_messages = len(messages)
		user_messages = message_counts['human']
		ai_messages = message_counts['ai']

		# Determine conversation stage
		if total_messages <= 2:
			stage = 'initial'
		elif total_messages <= 6:
			stage = 'developing'
		elif total_messages <= 12:
			stage = 'engaged'
		else:
			stage = 'extended'

		# Analyze last few messages for context
		recent_messages = messages[-3:] if len(messages) >= 3 else messages
		recent_user_queries = [MessageProcessor.get_message_text(msg) for msg in recent_messages if isinstance(msg, HumanMessage)]

		return {
			'status': 'active',
			'total_messages': total_messages,
			'message_counts': message_counts,
			'stage': stage,
			'user_ai_ratio': user_messages / max(ai_messages, 1),
			'recent_user_queries': recent_user_queries,
			'conversation_length': sum(len(MessageProcessor.get_message_text(msg)) for msg in messages),
		}

	@staticmethod
	def extract_topics(messages: List[BaseMessage]) -> List[str]:
		"""Extract main topics từ conversation"""

		# Simple keyword extraction
		financial_keywords = ['đầu tư', 'tiết kiệm', 'ngân hàng', 'tín dụng', 'bảo hiểm', 'lãi suất', 'cổ phiếu', 'trái phiếu', 'quỹ đầu tư', 'forex', 'crypto', 'bitcoin', 'thẻ tín dụng', 'vay vốn']

		found_topics = []

		for message in messages:
			if isinstance(message, HumanMessage):
				content = MessageProcessor.get_message_text(message).lower()
				for keyword in financial_keywords:
					if keyword in content and keyword not in found_topics:
						found_topics.append(keyword)

		return found_topics

	@staticmethod
	def detect_intent_shift(messages: List[BaseMessage]) -> bool:
		"""Detect if user intent has shifted significantly"""

		if len(messages) < 4:
			return False

		# Compare topics in first half vs second half
		mid_point = len(messages) // 2
		early_messages = messages[:mid_point]
		recent_messages = messages[mid_point:]

		early_topics = set(ConversationAnalyzer.extract_topics(early_messages))
		recent_topics = set(ConversationAnalyzer.extract_topics(recent_messages))

		# Check overlap
		if early_topics and recent_topics:
			overlap = len(early_topics.intersection(recent_topics))
			total_unique = len(early_topics.union(recent_topics))

			# If less than 30% overlap, consider it a shift
			return (overlap / total_unique) < 0.3

		return False
