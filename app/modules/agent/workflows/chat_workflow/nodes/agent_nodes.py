"""
Production agent node implementations
Advanced LLM calling với RAG context integration
"""

import os
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, START

from ..state.workflow_state import AgentState, StateManager
from ..config.workflow_config import WorkflowConfig
from ..config.prompts import SystemPrompts, PromptTemplates, ValidationPrompts
from ..utils.error_handlers import handle_errors, ModelError
from ..utils.message_utils import MessageProcessor, DocumentFormatter

logger = logging.getLogger(__name__)


class AgentNodes:
	"""
	Production agent implementations với advanced features

	Features:
	- RAG context integration
	- Dynamic prompt selection
	- Response validation
	- Performance monitoring
	- Tool integration
	"""

	def __init__(self, config: WorkflowConfig):
		self.config = config
		self.logger = logging.getLogger(__name__)
		self._model_cache = {}

	@handle_errors(
		fallback_response='Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.',
		error_type='model_invocation',
	)
	async def call_model(self, state: AgentState, config: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Enhanced model calling với RAG context integration
		"""
		start_time = time.time()

		try:
			self.logger.info('🤖 [Agent] Starting model invocation...')

			# Extract user message for context analysis
			user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

			if not user_message:
				raise ModelError('No user message found', 'missing_input')

			# Build enhanced system prompt
			system_prompt = self._build_system_prompt(state, config, user_message)

			# Setup model với proper configuration
			model = self._setup_model(config)

			# Create enhanced prompt với RAG context
			prompt_template = self._create_enhanced_prompt_template(system_prompt)

			# Create chain
			chain = prompt_template | model

			# Prepare messages với enhancements
			enhanced_messages = self._enhance_messages(state, config)

			# Execute model call với monitoring
			response = await self._execute_model_call(chain, enhanced_messages, user_message)

			# Validate response
			if not self._validate_response(response):
				raise ModelError('Response validation failed', 'invalid_response')

			# Calculate processing time và update state
			processing_time = time.time() - start_time
			updated_state = StateManager.add_processing_time(state, 'agent', processing_time)

			# Track model usage
			tokens_used = self._estimate_token_usage(enhanced_messages, response)
			updated_state = StateManager.update_model_usage(updated_state, tokens_used, self.config.model_name)

			self.logger.info(f'🤖 [Agent] Model response generated successfully (processed in {processing_time:.2f}s, ~{tokens_used} tokens)')

			return {**updated_state, 'messages': [response]}

		except Exception as e:
			self.logger.error(f'Error in model invocation: {str(e)}')

			# Create fallback response
			fallback_response = self._create_fallback_response(e, state)

			return {
				'messages': [fallback_response],
				'error_context': {
					'error_type': 'model_error',
					'error_message': str(e),
					'timestamp': datetime.now().isoformat(),
				},
			}

	def should_continue(self, state: AgentState) -> str:
		"""
		Enhanced conditional edge logic
		"""
		try:
			messages = state.get('messages', [])
			if not messages:
				self.logger.warning('No messages in state')
				return END

			last_message = messages[-1]

			# Check for tool calls
			if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
				self.logger.info(f'🔧 [Routing] Tool calls detected: {len(last_message.tool_calls)}')
				return 'tools'

			# Check for conversation continuation patterns
			if self._should_continue_conversation(state):
				self.logger.info('🔄 [Routing] Continuing conversation')
				return 'agent'

			self.logger.info('🏁 [Routing] Ending conversation')
			return END

		except Exception as e:
			self.logger.error(f'Error in should_continue: {str(e)}')
			return END

	def _build_system_prompt(self, state: AgentState, config: Dict[str, Any], user_message: str) -> str:
		"""Build enhanced system prompt với context awareness"""

		# Get base prompt từ config or detect topic-specific prompt
		base_prompt = config.get('system_prompt')
		if not base_prompt:
			base_prompt = PromptTemplates.get_context_specific_prompt(user_message)

		# Enhance với RAG context if available
		rag_context = state.get('rag_context', [])
		if rag_context:
			# Format RAG context
			context_text = DocumentFormatter.format_docs_as_context(state.get('retrieved_docs', []))

			enhanced_prompt = PromptTemplates.get_rag_enhanced_prompt(base_prompt, context_text)

			self.logger.info(f'📝 [Agent] Enhanced prompt với RAG context ({len(rag_context)} documents)')

			return enhanced_prompt

		return base_prompt

	def _setup_model(self, config: Dict[str, Any]) -> ChatGoogleGenerativeAI:
		"""Setup model với configuration"""

		# Model configuration với fallbacks
		model_config = config.get('model_config', {})

		model_name = model_config.get('model', self.config.model_name)
		temperature = model_config.get('temperature', self.config.temperature)
		max_tokens = model_config.get('max_tokens', self.config.max_tokens)
		api_key = model_config.get('api_key') or self.config.api_key

		# Cache key
		cache_key = f'{model_name}_{temperature}_{max_tokens}'

		# Check cache
		if cache_key in self._model_cache:
			return self._model_cache[cache_key]

		# Create new model instance
		model = ChatGoogleGenerativeAI(
			model=model_name,
			temperature=temperature,
			max_output_tokens=max_tokens,
			google_api_key=api_key,
			convert_system_message_to_human=True,  # For Gemini compatibility
		)

		# Cache model instance
		self._model_cache[cache_key] = model

		return model

	def _create_enhanced_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
		"""Create enhanced prompt template"""

		return ChatPromptTemplate.from_messages([
			SystemMessage(content=system_prompt),
			MessagesPlaceholder(variable_name='messages'),
		])

	def _enhance_messages(self, state: AgentState, config: Dict[str, Any]) -> List[BaseMessage]:
		"""Enhance messages với additional context"""

		messages = state.get('messages', [])
		if not messages:
			return []

		enhanced_messages = messages.copy()

		# Add timestamp context to last user message
		if enhanced_messages and isinstance(enhanced_messages[-1], HumanMessage):
			last_msg = enhanced_messages[-1]
			current_time = datetime.now(timezone.utc).isoformat()

			# Enhanced content với context
			enhanced_content = last_msg.content

			# Add conversation metadata if available
			conversation_metadata = state.get('conversation_metadata', {})
			if conversation_metadata:
				context_parts = []

				# Add session info
				if conversation_metadata.get('session_id'):
					context_parts.append(f'Session: {conversation_metadata["session_id"]}')

				# Add message count
				msg_count = conversation_metadata.get('message_count', 0)
				if msg_count > 1:
					context_parts.append(f'Message #{msg_count}')

				if context_parts:
					enhanced_content += f'\n\n[Context: {", ".join(context_parts)}]'

			enhanced_content += f'\n[Current time: {current_time}]'

			# Create enhanced message
			enhanced_messages[-1] = HumanMessage(
				content=enhanced_content,
				additional_kwargs=(last_msg.additional_kwargs if hasattr(last_msg, 'additional_kwargs') else {}),
			)

		return enhanced_messages

	async def _execute_model_call(self, chain, messages: List[BaseMessage], user_message: str) -> AIMessage:
		"""Execute model call với error handling và monitoring"""

		try:
			# Execute chain
			response = await chain.ainvoke({'messages': messages})

			# Enhance response với metadata
			enhanced_response = self._enhance_response(response, user_message)

			return enhanced_response

		except Exception as e:
			self.logger.error(f'Model execution failed: {str(e)}')
			raise ModelError(f'Model execution failed: {str(e)}', 'execution_error')

	def _enhance_response(self, response: AIMessage, user_message: str) -> AIMessage:
		"""Enhance response với additional metadata"""

		# Get existing additional_kwargs
		additional_kwargs = getattr(response, 'additional_kwargs', {})

		# Add enhancement metadata
		additional_kwargs.update({
			'enhanced_response': True,
			'generation_timestamp': datetime.now(timezone.utc).isoformat(),
			'model_name': self.config.model_name,
			'user_query_preview': (user_message[:100] + '...' if len(user_message) > 100 else user_message),
		})

		# Create enhanced response
		enhanced_response = AIMessage(content=response.content, additional_kwargs=additional_kwargs)

		# Copy tool calls if present
		if hasattr(response, 'tool_calls') and response.tool_calls:
			enhanced_response.tool_calls = response.tool_calls

		return enhanced_response

	def _validate_response(self, response: AIMessage) -> bool:
		"""Validate response content và safety"""

		try:
			# Basic validation
			if not response or not response.content:
				return False

			content = str(response.content)

			# Content length validation
			if len(content.strip()) < 10:  # Too short
				return False

			if len(content) > 10000:  # Too long
				return False

			# Safety validation
			if not ValidationPrompts.validate_response_content(content):
				self.logger.warning('Response failed safety validation')
				return False

			return True

		except Exception as e:
			self.logger.error(f'Response validation error: {str(e)}')
			return False

	def _create_fallback_response(self, error: Exception, state: AgentState) -> AIMessage:
		"""Create fallback response khi model fails"""

		# Analyze error type
		error_type = 'unknown_error'
		if 'rate limit' in str(error).lower():
			error_type = 'rate_limit'
		elif 'timeout' in str(error).lower():
			error_type = 'timeout'
		elif 'network' in str(error).lower():
			error_type = 'network_error'

		# Get user message for context
		user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

		# Create appropriate fallback message
		suggestions = [
			'Thử lại với câu hỏi đơn giản hơn',
			'Kiểm tra kết nối internet',
			'Đợi một chút rồi thử lại',
		]

		if error_type == 'rate_limit':
			suggestions = [
				'Đợi một vài phút rồi thử lại',
				'Hệ thống đang bận, vui lòng thử lại sau',
			]

		fallback_content = self._create_error_response(error_type, user_message or 'câu hỏi của bạn', suggestions)

		return AIMessage(
			content=fallback_content,
			additional_kwargs={
				'is_fallback': True,
				'error_type': error_type,
				'original_error': str(error),
				'timestamp': datetime.now(timezone.utc).isoformat(),
			},
		)

	def _create_error_response(self, error_type: str, user_message: str, suggestions: List[str]) -> str:
		"""Create user-friendly error response"""

		error_messages = {
			'rate_limit': 'hệ thống đang bận',
			'timeout': 'quá thời gian xử lý',
			'network_error': 'gặp sự cố kết nối',
			'unknown_error': 'gặp sự cố không xác định',
		}

		base_message = error_messages.get(error_type, error_messages['unknown_error'])

		response = f'Xin lỗi, {base_message} khi xử lý câu hỏi của bạn.\n\n'

		response += 'Gợi ý:\n'
		for suggestion in suggestions:
			response += f'• {suggestion}\n'

		response += '\nTôi sẵn sàng hỗ trợ bạn với các câu hỏi tài chính khác.'

		return response

	def _should_continue_conversation(self, state: AgentState) -> bool:
		"""Determine if conversation should continue"""

		# For now, always end after response
		# Can be enhanced với conversation flow analysis
		return False

	def _estimate_token_usage(self, messages: List[BaseMessage], response: AIMessage) -> int:
		"""Estimate token usage cho monitoring"""

		# Simple estimation based on character count
		# In production, use proper tokenizer

		total_chars = 0

		# Count input tokens
		for message in messages:
			content = MessageProcessor.get_message_text(message)
			total_chars += len(content)

		# Count output tokens
		response_content = str(response.content)
		total_chars += len(response_content)

		# Rough estimate: 1 token ≈ 4 characters for Vietnamese
		estimated_tokens = total_chars // 4

		return max(estimated_tokens, 1)

	async def health_check(self) -> Dict[str, Any]:
		"""Health check cho agent system"""

		try:
			# Test model initialization
			test_model = self._setup_model({})

			return {
				'status': 'healthy',
				'model_name': self.config.model_name,
				'model_cache_size': len(self._model_cache),
				'api_key_configured': bool(self.config.api_key),
				'timestamp': time.time(),
			}

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}
