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
from ..utils.color_logger import get_color_logger, Colors

logger = logging.getLogger(__name__)
color_logger = get_color_logger(__name__)


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
		self.start_time = time.time()

		color_logger.workflow_start(
			'AgentNodes Initialization',
			config_type=type(config).__name__,
			model_name=config.model_name,
			temperature=config.temperature,
		)

	@handle_errors(
		fallback_response='Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.',
		error_type='model_invocation',
	)
	async def call_model(self, state: AgentState, config: Dict[str, Any]) -> Dict[str, Any]:
		"""
		Enhanced model calling với RAG context integration
		"""
		start_time = time.time()

		color_logger.workflow_start(
			'Model Invocation',
			state_keys=list(state.keys()),
			config_keys=list(config.keys()),
			rag_context_available=bool(state.get('rag_context')),
		)

		try:
			color_logger.info(
				f'🤖 {Colors.BOLD}AGENT_START:{Colors.RESET}{Colors.BRIGHT_BLUE} Initializing model invocation pipeline',
				Colors.BRIGHT_BLUE,
			)

			# Extract user message for context analysis
			user_message = MessageProcessor.extract_last_user_message(state.get('messages', []))

			if not user_message:
				color_logger.error(
					f'❌ {Colors.BOLD}INPUT_ERROR:{Colors.RESET}{Colors.BRIGHT_RED} No user message found in state',
					Colors.BRIGHT_RED,
					state_messages_count=len(state.get('messages', [])),
				)
				raise ModelError('No user message found', 'missing_input')

			color_logger.info(
				f'📝 {Colors.BOLD}USER_INPUT:{Colors.RESET}{Colors.BRIGHT_CYAN} Processing user message',
				Colors.BRIGHT_CYAN,
				message_length=len(user_message),
				word_count=len(user_message.split()),
				preview=(user_message[:100] + '...' if len(user_message) > 100 else user_message),
			)

			# Build enhanced system prompt
			color_logger.info(
				f'🔧 {Colors.BOLD}PROMPT_BUILD:{Colors.RESET}{Colors.YELLOW} Building enhanced system prompt',
				Colors.YELLOW,
			)
			system_prompt = self._build_system_prompt(state, config, user_message)

			# Setup model với proper configuration
			color_logger.info(
				f'⚙️ {Colors.BOLD}MODEL_SETUP:{Colors.RESET}{Colors.MAGENTA} Setting up model configuration',
				Colors.MAGENTA,
			)
			model = self._setup_model(config)

			# Create enhanced prompt với RAG context
			color_logger.info(
				f'📋 {Colors.BOLD}TEMPLATE_CREATE:{Colors.RESET}{Colors.CYAN} Creating enhanced prompt template',
				Colors.CYAN,
			)
			prompt_template = self._create_enhanced_prompt_template(system_prompt)

			# Create chain
			chain = prompt_template | model
			color_logger.info(
				f'🔗 {Colors.BOLD}CHAIN_BUILD:{Colors.RESET}{Colors.BRIGHT_GREEN} Model chain constructed successfully',
				Colors.BRIGHT_GREEN,
			)

			# Prepare messages với enhancements
			color_logger.info(
				f'💬 {Colors.BOLD}MESSAGE_ENHANCE:{Colors.RESET}{Colors.BRIGHT_YELLOW} Enhancing messages with context',
				Colors.BRIGHT_YELLOW,
			)
			enhanced_messages = self._enhance_messages(state, config)

			# Execute model call với monitoring
			color_logger.info(
				f'🚀 {Colors.BOLD}MODEL_EXECUTE:{Colors.RESET}{Colors.BRIGHT_BLUE} Executing model call',
				Colors.BRIGHT_BLUE,
				enhanced_messages_count=len(enhanced_messages),
			)
			response = await self._execute_model_call(chain, enhanced_messages, user_message)

			# Validate response
			color_logger.info(
				f'✅ {Colors.BOLD}RESPONSE_VALIDATE:{Colors.RESET}{Colors.GREEN} Validating model response',
				Colors.GREEN,
			)
			if not self._validate_response(response):
				color_logger.error(
					f'❌ {Colors.BOLD}VALIDATION_FAIL:{Colors.RESET}{Colors.BRIGHT_RED} Response validation failed',
					Colors.BRIGHT_RED,
					response_length=len(str(response.content)) if response else 0,
				)
				raise ModelError('Response validation failed', 'invalid_response')

			color_logger.success(
				'Response validation passed',
				response_length=len(str(response.content)),
				has_tool_calls=hasattr(response, 'tool_calls') and bool(response.tool_calls),
			)

			# Calculate processing time và update state
			processing_time = time.time() - start_time
			updated_state = StateManager.add_processing_time(state, 'agent', processing_time)

			color_logger.performance_metric('agent_processing_time', f'{processing_time:.3f}', 's')

			# Track model usage
			tokens_used = self._estimate_token_usage(enhanced_messages, response)
			updated_state = StateManager.update_model_usage(updated_state, tokens_used, self.config.model_name)

			color_logger.performance_metric('tokens_used', tokens_used, '', model_name=self.config.model_name)

			color_logger.workflow_complete(
				'Model Invocation',
				processing_time,
				success=True,
				tokens_used=tokens_used,
				response_length=len(str(response.content)),
				validation_passed=True,
			)

			return {**updated_state, 'messages': [response]}

		except Exception as e:
			processing_time = time.time() - start_time
			color_logger.error(
				f'Model invocation failed: {str(e)}',
				error_type=type(e).__name__,
				processing_time=processing_time,
				user_message_preview=(user_message[:50] if 'user_message' in locals() else 'unknown'),
			)

			# Create fallback response
			fallback_response = self._create_fallback_response(e, state)

			color_logger.warning(
				f'🔄 {Colors.BOLD}FALLBACK:{Colors.RESET}{Colors.BRIGHT_YELLOW} Using fallback response',
				Colors.BRIGHT_YELLOW,
				fallback_content_length=len(str(fallback_response.content)),
			)

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
		color_logger.info(
			f'🔄 {Colors.BOLD}ROUTING_DECISION:{Colors.RESET}{Colors.MAGENTA} Determining workflow continuation',
			Colors.MAGENTA,
		)

		try:
			messages = state.get('messages', [])
			if not messages:
				color_logger.warning(
					'No messages in state for routing decision',
					decision='END',
					reason='empty_messages',
				)
				return END

			last_message = messages[-1]
			color_logger.debug(
				f'Analyzing last message for routing',
				message_type=type(last_message).__name__,
				has_content=hasattr(last_message, 'content') and bool(last_message.content),
				has_tool_calls=hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls),
			)

			# Check for tool calls
			if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
				tool_names = [tc.get('name', 'unknown') for tc in last_message.tool_calls]
				color_logger.info(
					f'🔧 {Colors.BOLD}TOOL_ROUTING:{Colors.RESET}{Colors.YELLOW} Tool calls detected, routing to tools',
					Colors.YELLOW,
					tool_count=len(last_message.tool_calls),
					tool_names=tool_names,
				)
				return 'tools'

			# Check for conversation continuation patterns
			should_continue = self._should_continue_conversation(state)
			if should_continue:
				color_logger.info(
					f'🔄 {Colors.BOLD}CONTINUE_CHAT:{Colors.RESET}{Colors.BRIGHT_CYAN} Continuing conversation flow',
					Colors.BRIGHT_CYAN,
					conversation_length=len(messages),
				)
				return 'agent'

			color_logger.info(
				f'🏁 {Colors.BOLD}END_CONVERSATION:{Colors.RESET}{Colors.BRIGHT_GREEN} Ending conversation gracefully',
				Colors.BRIGHT_GREEN,
				final_message_count=len(messages),
			)
			return END

		except Exception as e:
			color_logger.error(
				f'Error in routing decision: {str(e)}',
				error_type=type(e).__name__,
				fallback_decision='END',
			)
			return END

	def _build_system_prompt(self, state: AgentState, config: Dict[str, Any], user_message: str) -> str:
		"""Build enhanced system prompt với context awareness"""
		color_logger.info(
			f'📋 {Colors.BOLD}PROMPT_ANALYSIS:{Colors.RESET}{Colors.CYAN} Analyzing context for prompt selection',
			Colors.CYAN,
			user_message_length=len(user_message),
		)

		# Get base prompt từ config or detect topic-specific prompt
		base_prompt = config.get('system_prompt')
		print(f"📝 [Agent] Using system prompt: '{base_prompt}...'")
		if not base_prompt:
			color_logger.info(
				f'🎯 {Colors.BOLD}TOPIC_DETECTION:{Colors.RESET}{Colors.BRIGHT_MAGENTA} Detecting topic-specific prompt',
				Colors.BRIGHT_MAGENTA,
			)
			base_prompt = PromptTemplates.get_context_specific_prompt(user_message)
			color_logger.success(
				'Topic-specific prompt selected',
				prompt_type='context_specific',
				prompt_length=len(base_prompt),
			)

		# Enhance với RAG context if available
		rag_context = state.get('rag_context', [])
		if rag_context:
			color_logger.info(
				f'🧠 {Colors.BOLD}RAG_ENHANCEMENT:{Colors.RESET}{Colors.BRIGHT_YELLOW} Enhancing prompt with RAG context',
				Colors.BRIGHT_YELLOW,
				context_sources=len(rag_context),
			)

			# Format RAG context
			context_text = DocumentFormatter.format_docs_as_context(state.get('retrieved_docs', []))
			enhanced_prompt = PromptTemplates.get_rag_enhanced_prompt(base_prompt, context_text)

			color_logger.success(
				'RAG-enhanced prompt created',
				base_prompt_length=len(base_prompt),
				context_length=len(context_text),
				enhanced_prompt_length=len(enhanced_prompt),
				sources_count=len(rag_context),
			)

			return enhanced_prompt
		else:
			color_logger.info(
				f'📝 {Colors.BOLD}BASE_PROMPT:{Colors.RESET}{Colors.DIM} Using base prompt without RAG enhancement',
				Colors.DIM,
				prompt_length=len(base_prompt),
			)

		return base_prompt

	def _setup_model(self, config: Dict[str, Any]) -> ChatGoogleGenerativeAI:
		"""Setup model với configuration"""
		color_logger.info(
			f'⚙️ {Colors.BOLD}MODEL_CONFIG:{Colors.RESET}{Colors.BLUE} Setting up model configuration',
			Colors.BLUE,
		)

		# Model configuration với fallbacks
		model_config = config.get('model_config', {})

		model_name = model_config.get('model', self.config.model_name)
		temperature = model_config.get('temperature', self.config.temperature)
		max_tokens = model_config.get('max_tokens', self.config.max_tokens)
		api_key = model_config.get('api_key') or self.config.api_key

		color_logger.info(
			f'🔧 {Colors.BOLD}MODEL_PARAMS:{Colors.RESET}{Colors.BRIGHT_BLUE} Model parameters configured',
			Colors.BRIGHT_BLUE,
			model_name=model_name,
			temperature=temperature,
			max_tokens=max_tokens,
			api_key_available=bool(api_key),
		)

		# Cache key
		cache_key = f'{model_name}_{temperature}_{max_tokens}'
		color_logger.debug(
			f'Cache key generated',
			cache_key=cache_key,
			cache_size=len(self._model_cache),
		)

		# Check cache
		if cache_key in self._model_cache:
			color_logger.info(
				f'🗄️ {Colors.BOLD}CACHE_HIT:{Colors.RESET}{Colors.BRIGHT_GREEN} Using cached model instance',
				Colors.BRIGHT_GREEN,
				cache_key=cache_key,
			)
			return self._model_cache[cache_key]

		color_logger.info(
			f'🆕 {Colors.BOLD}MODEL_CREATE:{Colors.RESET}{Colors.YELLOW} Creating new model instance',
			Colors.YELLOW,
		)

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
		color_logger.success(
			'Model instance created and cached',
			cache_key=cache_key,
			cache_size=len(self._model_cache),
		)

		return model

	def _create_enhanced_prompt_template(self, system_prompt: str) -> ChatPromptTemplate:
		"""Create enhanced prompt template"""
		color_logger.info(
			f'📝 {Colors.BOLD}TEMPLATE_CREATE:{Colors.RESET}{Colors.CYAN} Creating enhanced prompt template',
			Colors.CYAN,
			system_prompt_length=len(system_prompt),
		)

		template = ChatPromptTemplate.from_messages([
			SystemMessage(content=system_prompt),
			MessagesPlaceholder(variable_name='messages'),
		])

		color_logger.success(
			'Prompt template created successfully',
			template_type='ChatPromptTemplate',
			message_placeholders=1,
		)

		return template

	def _enhance_messages(self, state: AgentState, config: Dict[str, Any]) -> List[BaseMessage]:
		"""Enhance messages với additional context"""
		color_logger.info(
			f'💬 {Colors.BOLD}MESSAGE_ENHANCEMENT:{Colors.RESET}{Colors.BRIGHT_YELLOW} Enhancing messages with context',
			Colors.BRIGHT_YELLOW,
		)

		messages = state.get('messages', [])
		if not messages:
			color_logger.warning('No messages to enhance')
			return []

		enhanced_messages = messages.copy()
		color_logger.debug(f'Base messages copied', original_count=len(messages))

		# Add timestamp context to last user message
		if enhanced_messages and isinstance(enhanced_messages[-1], HumanMessage):
			color_logger.info(
				f'🕒 {Colors.BOLD}TIMESTAMP_ADD:{Colors.RESET}{Colors.MAGENTA} Adding timestamp context to user message',
				Colors.MAGENTA,
			)

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
					color_logger.debug(
						f'Conversation context added',
						context_parts=len(context_parts),
						session_id=conversation_metadata.get('session_id'),
						message_count=msg_count,
					)

			enhanced_content += f'\n[Current time: {current_time}]'

			# Create enhanced message
			enhanced_messages[-1] = HumanMessage(
				content=enhanced_content,
				additional_kwargs=(last_msg.additional_kwargs if hasattr(last_msg, 'additional_kwargs') else {}),
			)

			color_logger.success(
				'Message enhancement completed',
				original_length=len(last_msg.content),
				enhanced_length=len(enhanced_content),
				context_added=True,
			)

		color_logger.info(
			f'✅ {Colors.BOLD}ENHANCEMENT_COMPLETE:{Colors.RESET}{Colors.BRIGHT_GREEN} Messages enhanced successfully',
			Colors.BRIGHT_GREEN,
			final_message_count=len(enhanced_messages),
		)

		return enhanced_messages

	async def _execute_model_call(self, chain, messages: List[BaseMessage], user_message: str) -> AIMessage:
		"""Execute model call với error handling và monitoring"""
		start_time = time.time()
		color_logger.info(
			f'🚀 {Colors.BOLD}MODEL_CALL:{Colors.RESET}{Colors.BRIGHT_BLUE} Executing model chain invocation',
			Colors.BRIGHT_BLUE,
			input_messages_count=len(messages),
		)

		try:
			# Execute chain
			response = await chain.ainvoke({'messages': messages})

			execution_time = time.time() - start_time
			color_logger.performance_metric('model_execution_time', f'{execution_time:.3f}', 's')

			# Enhance response với metadata
			enhanced_response = self._enhance_response(response, user_message)

			color_logger.success(
				'Model call executed successfully',
				execution_time=execution_time,
				response_length=len(str(enhanced_response.content)),
				has_additional_kwargs=bool(getattr(enhanced_response, 'additional_kwargs', {})),
			)

			return enhanced_response

		except Exception as e:
			execution_time = time.time() - start_time
			color_logger.error(
				f'Model execution failed: {str(e)}',
				error_type=type(e).__name__,
				execution_time=execution_time,
				input_messages_count=len(messages),
			)
			raise ModelError(f'Model execution failed: {str(e)}', 'execution_error')

	def _enhance_response(self, response: AIMessage, user_message: str) -> AIMessage:
		"""Enhance response với additional metadata"""
		color_logger.info(
			f'✨ {Colors.BOLD}RESPONSE_ENHANCE:{Colors.RESET}{Colors.BRIGHT_MAGENTA} Enhancing response with metadata',
			Colors.BRIGHT_MAGENTA,
		)

		# Get existing additional_kwargs
		additional_kwargs = getattr(response, 'additional_kwargs', {})

		# Add enhancement metadata
		enhancement_metadata = {
			'enhanced_response': True,
			'generation_timestamp': datetime.now(timezone.utc).isoformat(),
			'model_name': self.config.model_name,
			'user_query_preview': (user_message[:100] + '...' if len(user_message) > 100 else user_message),
		}

		additional_kwargs.update(enhancement_metadata)

		color_logger.debug(
			f'Enhancement metadata added',
			metadata_keys=list(enhancement_metadata.keys()),
			total_kwargs=len(additional_kwargs),
		)

		# Create enhanced response
		enhanced_response = AIMessage(content=response.content, additional_kwargs=additional_kwargs)

		# Copy tool calls if present
		if hasattr(response, 'tool_calls') and response.tool_calls:
			enhanced_response.tool_calls = response.tool_calls
			color_logger.debug(f'Tool calls preserved', tool_calls_count=len(response.tool_calls))

		color_logger.success(
			'Response enhancement completed',
			original_kwargs_count=len(getattr(response, 'additional_kwargs', {})),
			enhanced_kwargs_count=len(additional_kwargs),
			has_tool_calls=bool(getattr(enhanced_response, 'tool_calls', [])),
		)

		return enhanced_response

	def _validate_response(self, response: AIMessage) -> bool:
		"""Validate response content và safety"""
		color_logger.info(
			f'✅ {Colors.BOLD}VALIDATION_START:{Colors.RESET}{Colors.GREEN} Starting response validation',
			Colors.GREEN,
		)

		try:
			# Basic validation
			if not response or not response.content:
				color_logger.warning(
					'Response validation failed - empty response',
					has_response=bool(response),
					has_content=bool(response.content) if response else False,
				)
				return False

			content = str(response.content)
			color_logger.debug(
				f'Validating response content',
				content_length=len(content),
				content_preview=(content[:100] + '...' if len(content) > 100 else content),
			)

			# Content length validation
			if len(content.strip()) < 10:  # Too short
				color_logger.warning(
					'Response validation failed - content too short',
					content_length=len(content.strip()),
					minimum_required=10,
				)
				return False

			if len(content) > 10000:  # Too long
				color_logger.warning(
					'Response validation failed - content too long',
					content_length=len(content),
					maximum_allowed=10000,
				)
				return False

			# Safety validation
			color_logger.info(
				f'🛡️ {Colors.BOLD}SAFETY_CHECK:{Colors.RESET}{Colors.YELLOW} Running safety validation',
				Colors.YELLOW,
			)

			if not ValidationPrompts.validate_response_content(content):
				color_logger.warning(
					'Response failed safety validation',
					safety_check='failed',
					content_preview=content[:50],
				)
				return False

			color_logger.success(
				'Response validation passed all checks',
				content_length=len(content),
				safety_validated=True,
				length_valid=True,
			)

			return True

		except Exception as e:
			color_logger.error(
				f'Response validation error: {str(e)}',
				error_type=type(e).__name__,
				validation_result=False,
			)
			return False

	def _create_fallback_response(self, error: Exception, state: AgentState) -> AIMessage:
		"""Create fallback response khi model fails"""
		color_logger.info(
			f'🔄 {Colors.BOLD}FALLBACK_CREATE:{Colors.RESET}{Colors.BRIGHT_YELLOW} Creating fallback response',
			Colors.BRIGHT_YELLOW,
			error_type=type(error).__name__,
		)

		# Analyze error type
		error_type = 'unknown_error'
		error_str = str(error).lower()

		if 'rate limit' in error_str:
			error_type = 'rate_limit'
		elif 'timeout' in error_str:
			error_type = 'timeout'
		elif 'network' in error_str:
			error_type = 'network_error'

		color_logger.debug(
			f'Error type classified',
			original_error=str(error)[:100],
			classified_type=error_type,
		)

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

		color_logger.debug(
			f'Fallback suggestions prepared',
			suggestions_count=len(suggestions),
			error_type=error_type,
		)

		fallback_content = self._create_error_response(error_type, user_message or 'câu hỏi của bạn', suggestions)

		fallback_response = AIMessage(
			content=fallback_content,
			additional_kwargs={
				'is_fallback': True,
				'error_type': error_type,
				'original_error': str(error),
				'timestamp': datetime.now(timezone.utc).isoformat(),
			},
		)

		color_logger.success(
			'Fallback response created',
			error_type=error_type,
			fallback_length=len(fallback_content),
			suggestions_included=len(suggestions),
		)

		return fallback_response

	def _create_error_response(self, error_type: str, user_message: str, suggestions: List[str]) -> str:
		"""Create user-friendly error response"""
		color_logger.debug(
			f'Creating user-friendly error response',
			error_type=error_type,
			user_message_preview=user_message[:50],
			suggestions_count=len(suggestions),
		)

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
		color_logger.debug(
			f'Evaluating conversation continuation',
			messages_count=len(state.get('messages', [])),
		)

		# For now, always end after response
		# Can be enhanced với conversation flow analysis
		return False

	def _estimate_token_usage(self, messages: List[BaseMessage], response: AIMessage) -> int:
		"""Estimate token usage cho monitoring"""
		color_logger.debug(
			f'Estimating token usage',
			input_messages=len(messages),
			has_response=bool(response),
		)

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

		color_logger.debug(
			f'Token estimation completed',
			total_characters=total_chars,
			estimated_tokens=estimated_tokens,
			calculation_method='chars_div_4',
		)

		return max(estimated_tokens, 1)

	async def health_check(self) -> Dict[str, Any]:
		"""Health check cho agent system"""
		start_time = time.time()
		color_logger.workflow_start('Agent Health Check', comprehensive=True)

		try:
			color_logger.info(
				f'🔍 {Colors.BOLD}HEALTH_CHECK:{Colors.RESET}{Colors.BRIGHT_CYAN} Running agent system health check',
				Colors.BRIGHT_CYAN,
			)

			# Test model initialization
			color_logger.info(
				f'🤖 {Colors.BOLD}MODEL_TEST:{Colors.RESET}{Colors.BLUE} Testing model initialization',
				Colors.BLUE,
			)
			test_model = self._setup_model({})

			health_data = {
				'status': 'healthy',
				'model_name': self.config.model_name,
				'model_cache_size': len(self._model_cache),
				'api_key_configured': bool(self.config.api_key),
				'timestamp': time.time(),
			}

			check_time = time.time() - start_time
			color_logger.workflow_complete(
				'Agent Health Check',
				check_time,
				status='healthy',
				model_initialized=True,
				cache_size=len(self._model_cache),
			)

			return health_data

		except Exception as e:
			check_time = time.time() - start_time
			color_logger.error(
				f'Agent health check failed: {str(e)}',
				error_type=type(e).__name__,
				check_time=check_time,
			)
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}
