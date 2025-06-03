"""
Error handling và fallback mechanisms cho Chat Workflow
Production-ready error handling với graceful degradation
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from functools import wraps
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
	"""Base exception cho workflow errors"""

	def __init__(self, message: str, error_type: str = 'unknown', node_name: Optional[str] = None):
		super().__init__(message)
		self.error_type = error_type
		self.node_name = node_name
		self.timestamp = time.time()


class RAGError(WorkflowError):
	"""RAG-specific errors"""

	pass


class ModelError(WorkflowError):
	"""Model invocation errors"""

	pass


class ToolError(WorkflowError):
	"""Tool execution errors"""

	pass


def handle_errors(fallback_response: Optional[str] = None, error_type: str = 'unknown', retry_count: int = 0):
	"""
	Decorator cho error handling với graceful degradation
	"""

	def decorator(func: Callable):
		@wraps(func)
		async def wrapper(*args, **kwargs):
			try:
				return await func(*args, **kwargs)
			except Exception as e:
				# Log error
				logger.error(f'Error in {func.__name__}: {str(e)}', extra={'error_type': error_type, 'function': func.__name__, 'args': str(args)[:200] if args else None, 'retry_count': retry_count})

				# Try fallback response
				if fallback_response:
					return {'messages': [AIMessage(content=fallback_response)]}

				# Return empty response
				return {}

		return wrapper

	return decorator


def handle_retrieval_error(error: Exception, queries: List[str], logger_instance: logging.Logger) -> List[Document]:
	"""
	Handle retrieval errors với graceful degradation
	"""
	logger_instance.error(f'Knowledge retrieval failed: {str(error)}', extra={'error_type': 'retrieval_error', 'queries': queries, 'error_class': error.__class__.__name__})

	# Return empty documents list cho graceful degradation
	return []


def handle_model_error(error: Exception, state: Dict[str, Any], logger_instance: logging.Logger) -> Dict[str, Any]:
	"""
	Handle model invocation errors
	"""
	logger_instance.error(f'Model invocation failed: {str(error)}', extra={'error_type': 'model_error', 'state_keys': list(state.keys()), 'error_class': error.__class__.__name__})

	# Create fallback response
	fallback_message = AIMessage(content='Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau hoặc đặt câu hỏi khác.')

	return {'messages': [fallback_message]}


def handle_tool_error(error: Exception, tool_name: str, logger_instance: logging.Logger) -> Dict[str, Any]:
	"""
	Handle tool execution errors
	"""
	logger_instance.error(f'Tool execution failed: {tool_name} - {str(error)}', extra={'error_type': 'tool_error', 'tool_name': tool_name, 'error_class': error.__class__.__name__})

	# Create tool error message
	error_message = AIMessage(content=f"Không thể thực hiện thao tác '{tool_name}'. Vui lòng thử lại sau.")

	return {'messages': [error_message]}


class ErrorRecovery:
	"""Error recovery strategies"""

	@staticmethod
	def create_fallback_documents(queries: List[str]) -> List[Document]:
		"""Create fallback documents khi retrieval fails"""

		fallback_docs = []

		for query in queries:
			doc = Document(
				page_content=f"Xin lỗi, không thể tìm thấy thông tin cụ thể về '{query}'. Vui lòng thử với câu hỏi cụ thể hơn hoặc liên hệ chuyên gia tài chính.",
				metadata={'source': 'fallback', 'query': query, 'similarity_score': 0.0, 'is_fallback': True},
			)
			fallback_docs.append(doc)

		return fallback_docs

	@staticmethod
	def create_error_response(error_type: str, user_message: str, suggestions: Optional[List[str]] = None) -> str:
		"""Create user-friendly error response"""

		error_messages = {
			'retrieval_error': 'Không thể tìm kiếm thông tin lúc này.',
			'model_error': 'Gặp sự cố khi xử lý câu hỏi.',
			'tool_error': 'Không thể thực hiện thao tác yêu cầu.',
			'timeout_error': 'Quá thời gian xử lý.',
			'unknown_error': 'Gặp sự cố không xác định.',
		}

		base_message = error_messages.get(error_type, error_messages['unknown_error'])

		response = f'Xin lỗi, {base_message}\n\n'

		if suggestions:
			response += 'Gợi ý:\n'
			for suggestion in suggestions:
				response += f'• {suggestion}\n'
		else:
			response += 'Gợi ý:\n'
			response += '• Thử lại với câu hỏi đơn giản hơn\n'
			response += '• Kiểm tra kết nối internet\n'
			response += '• Liên hệ hỗ trợ nếu vấn đề tiếp tục\n'

		response += '\nTôi sẵn sàng hỗ trợ bạn với các câu hỏi tài chính khác.'

		return response


class RetryStrategy:
	"""Retry strategies cho failed operations"""

	@staticmethod
	async def retry_with_backoff(func: Callable, max_attempts: int = 3, backoff_factor: float = 1.0, exceptions: tuple = (Exception,)):
		"""
		Retry function với exponential backoff
		"""
		import asyncio

		for attempt in range(max_attempts):
			try:
				return await func()
			except exceptions as e:
				if attempt == max_attempts - 1:
					raise e

				wait_time = backoff_factor * (2**attempt)
				logger.warning(f'Attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}')
				await asyncio.sleep(wait_time)

	@staticmethod
	async def retry_retrieval(retriever_func: Callable, queries: List[str], max_attempts: int = 2) -> List[Document]:
		"""
		Retry retrieval với fallback strategies
		"""

		for attempt in range(max_attempts):
			try:
				docs = await retriever_func(queries)
				if docs:  # Success
					return docs
			except Exception as e:
				logger.warning(f'Retrieval attempt {attempt + 1} failed: {str(e)}')

				if attempt == max_attempts - 1:
					# Final fallback
					return ErrorRecovery.create_fallback_documents(queries)

		return []


class ValidationError(Exception):
	"""Validation errors"""

	pass


class Validator:
	"""Input validation utilities"""

	@staticmethod
	def validate_queries(queries: List[str]) -> bool:
		"""Validate search queries"""
		if not queries:
			return False

		for query in queries:
			if not query or not query.strip():
				return False

			if len(query.strip()) < 2:
				return False

			if len(query) > 500:  # Too long
				return False

		return True

	@staticmethod
	def validate_documents(documents: List[Document]) -> bool:
		"""Validate retrieved documents"""
		if not isinstance(documents, list):
			return False

		for doc in documents:
			if not isinstance(doc, Document):
				return False

			if not hasattr(doc, 'page_content') or not doc.page_content:
				return False

		return True

	@staticmethod
	def validate_state(state: Dict[str, Any]) -> bool:
		"""Validate workflow state"""
		required_keys = ['messages']

		for key in required_keys:
			if key not in state:
				return False

		# Validate messages
		messages = state.get('messages', [])
		if not isinstance(messages, list):
			return False

		return True


class CircuitBreaker:
	"""Circuit breaker pattern cho external service calls"""

	def __init__(self, failure_threshold: int = 5, timeout: int = 60):
		self.failure_threshold = failure_threshold
		self.timeout = timeout
		self.failure_count = 0
		self.last_failure_time = None
		self.state = 'closed'  # closed, open, half_open

	async def call(self, func: Callable, *args, **kwargs):
		"""Execute function với circuit breaker protection"""

		if self.state == 'open':
			if self._should_attempt_reset():
				self.state = 'half_open'
			else:
				raise Exception('Circuit breaker is open')

		try:
			result = await func(*args, **kwargs)
			self._on_success()
			return result

		except Exception as e:
			self._on_failure()
			raise e

	def _should_attempt_reset(self) -> bool:
		"""Check if should attempt to reset circuit breaker"""
		if not self.last_failure_time:
			return True

		return (time.time() - self.last_failure_time) >= self.timeout

	def _on_success(self):
		"""Handle successful call"""
		self.failure_count = 0
		self.state = 'closed'

	def _on_failure(self):
		"""Handle failed call"""
		self.failure_count += 1
		self.last_failure_time = time.time()

		if self.failure_count >= self.failure_threshold:
			self.state = 'open'


import time
