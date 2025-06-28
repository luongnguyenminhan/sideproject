"""
Enhanced Chat Workflow for EnterViu AI Assistant

This workflow integrates:
1. Persona-based system prompts (EnterViu CV Assistant)
2. Business process management with dynamic tool selection
3. Unified LLM-based guardrails system (input, output, and tool validation)
4. Dynamic tool configuration based on business requirements
5. Robust error handling and retry logic

Workflow Structure:
input_validation → business_process_analysis → agent → tool_decision → tools/output_validation → end/continue

Key Features:
- Only LLM-based guardrails (no other guardrail types)
- Business process-aware tool selection
- Persona-driven responses focused on CV building and career support
- Tool validation through guardrails before execution
- Retry logic for critical validation failures
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .state.workflow_state import AgentState, StateManager
from .config.workflow_config import WorkflowConfig
from .tools.basic_tools import get_tools, get_tool_definitions
from .config.business_process import get_business_process_manager, BusinessProcessType
from .config.llm_guardrails import (
	get_llm_guardrails_manager,
	initialize_guardrails_with_llm,
)

load_dotenv()

# Simple logger
import logging

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = """Bạn là EnterViu AI Assistant - Trợ lý thông minh chuyên nghiệp hỗ trợ người dùng xây dựng CV và tìm kiếm việc làm.

VAI TRÒ CỦA BẠN:
- Hỗ trợ tạo CV chuyên nghiệp từ A đến Z
- Tư vấn về kỹ năng, kinh nghiệm cần có cho từng vị trí
- Phân tích CV và đưa ra góp ý cải thiện
- Tạo câu hỏi khảo sát để hiểu rõ hơn về ứng viên
- Tư vấn chiến lược tìm việc và phát triển sự nghiệp

NGUYÊN TẮC LÀM VIỆC:
- Luôn thân thiện, chuyên nghiệp và nhiệt tình
- Đưa ra lời khuyên thực tế và có thể áp dụng được
- Tôn trọng thông tin cá nhân của người dùng
- Khuyến khích và động viên người dùng

Khi cần thông tin chi tiết hoặc thực hiện tác vụ cụ thể, hãy sử dụng các công cụ hỗ trợ."""

TOOL_DECISION_SYSTEM_PROMPT = """Bạn là Tool Decision Agent - Chuyên gia quyết định việc sử dụng công cụ cho Enterview AI Assistant.

NHIỆM VỤ: Phân tích yêu cầu của người dùng và quyết định có cần sử dụng tools hay không.

QUYẾT ĐỊNH "use_tools" KHI:
- Người dùng yêu cầu tìm kiếm thông tin cụ thể
- Cần tra cứu dữ liệu từ cơ sở dữ liệu
- Cần thực hiện tính toán, xử lý dữ liệu
- Yêu cầu thông tin real-time hoặc cập nhật
- Cần gọi API hoặc dịch vụ bên ngoài
- Yêu cầu tạo, lưu, hoặc cập nhật dữ liệu

QUYẾT ĐỊNH "no_tools" KHI:
- Trò chuyện thông thường
- Giải thích khái niệm, định nghĩa

Hãy phân tích kỹ yêu cầu và đưa ra quyết định chính xác."""


# Tool Decision Schema
class ToolDecision(BaseModel):
	"""Schema for tool usage decision"""

	decision: str = Field(description="Quyết định sử dụng tool: 'use_tools' hoặc 'no_tools'")
	reasoning: str = Field(description='Lý do cho quyết định này')
	confidence: float = Field(description='Độ tin cậy của quyết định (0.0-1.0)')
	tools_needed: List[str] = Field(default=[], description='Danh sách tools cần thiết (nếu có)')


class Workflow:
	"""Enhanced Chat Workflow: EnterViu AI Assistant with Business Process Management and LLM Guardrails

	This workflow provides:
	1. Persona-based responses focused on CV building and career support
	2. Business process-aware tool selection and validation
	3. Unified LLM-based guardrails for input, output, and tool validation
	4. Dynamic tool configuration based on business requirements
	5. Retry logic for critical validation failures

	Workflow integrates:
	- EnterViu persona prompts for CV assistant behavior
	- Business process management for context-aware responses
	- LLM guardrails manager for content safety and compliance
	- Dynamic tool selection based on business process requirements
	- RAG integration for knowledge context
	"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize enhanced workflow with business process and guardrails"""
		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		self.config.db_session = db_session

		# Initialize LLM
		self.llm = ChatGoogleGenerativeAI(model=self.config.model_name, temperature=self.config.temperature)

		# Initialize Tool Decision LLM (with structured output)
		self.tool_decision_llm = ChatGoogleGenerativeAI(
			model=self.config.model_name,
			temperature=0.1,  # Lower temperature for more consistent decisions
		).with_structured_output(ToolDecision)

		# Initialize Business Process Manager
		self.business_process_manager = get_business_process_manager()

		# Initialize LLM Guardrails Manager
		self.guardrails_manager = initialize_guardrails_with_llm(self.llm)

		# Initialize Global KB Service
		self._init_global_kb_service()

		# Build workflow
		self.compiled_graph = self._build_workflow()

	def _init_global_kb_service(self):
		"""Initialize Global Knowledge Base Service"""
		try:
			from app.modules.agentic_rag.services.global_kb_service import (
				GlobalKBService,
			)

			self.global_kb_service = GlobalKBService(self.db_session)
		except Exception:
			self.global_kb_service = None

	def _build_workflow(self) -> StateGraph:
		"""Build enhanced workflow with business process management and guardrails"""
		workflow = StateGraph(AgentState)

		# Get tools
		tools = get_tools(self.config)

		# Store tools for runtime updates
		self._tools = tools
		tool_node = ToolNode(tools)

		# Add nodes
		workflow.add_node('input_validation', self._input_validation_node)
		workflow.add_node('business_process_analysis', self._business_process_analysis_node)
		workflow.add_node('agent', self._agent_node)
		workflow.add_node('tool_decision', self._tool_decision_node)
		workflow.add_node('tools', self._tools_node)
		workflow.add_node('output_validation', self._output_validation_node)

		# Set entry point
		workflow.set_entry_point('input_validation')

		# Enhanced workflow flow with guardrails and business process
		workflow.add_edge('input_validation', 'business_process_analysis')
		workflow.add_edge('business_process_analysis', 'agent')
		workflow.add_edge('agent', 'tool_decision')
		workflow.add_conditional_edges(
			'tool_decision',
			self._route_after_tool_decision,
			{'use_tools': 'tools', 'no_tools': 'output_validation'},
		)
		workflow.add_edge('tools', 'output_validation')
		workflow.add_conditional_edges(
			'output_validation',
			self._route_after_output_validation,
			{'continue': 'agent', 'end': END},
		)

		# Compile with memory
		checkpointer = MemorySaver()
		return workflow.compile(checkpointer=checkpointer)

	async def _input_validation_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Input Validation Node - Validates user input through LLM guardrails"""
		logger.info('[_input_validation_node] Starting input validation')

		# Get user message
		user_message = StateManager.extract_last_user_message(state)
		if not user_message:
			logger.warning('[_input_validation_node] No user message found')
			return state

		try:
			# Validate user input through guardrails
			validation_result = await self.guardrails_manager.validate_user_input(
				user_message,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'timestamp': datetime.now().isoformat(),
				},
			)

			logger.info(f'[_input_validation_node] Validation result: {validation_result["is_safe"]} - {validation_result["summary"]}')

			# Store validation results in state
			return {
				**state,
				'input_validation': validation_result,
				'validation_passed': validation_result['is_safe'],
			}

		except Exception as e:
			logger.error(f'[_input_validation_node] Validation failed: {str(e)}')
			# Allow processing to continue on validation error
			return {
				**state,
				'input_validation': {'is_safe': True, 'error': str(e)},
				'validation_passed': True,
			}

	async def _business_process_analysis_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Business Process Analysis Node - Identifies process type and applicable rules"""
		logger.info('[_business_process_analysis_node] Starting business process analysis')

		# Get user message
		user_message = StateManager.extract_last_user_message(state)
		if not user_message:
			logger.warning('[_business_process_analysis_node] No user message found')
			return state

		try:
			# Identify business process type
			process_type = self.business_process_manager.identify_process_type(
				user_message,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'has_cv_context': bool(state.get('cv_context')),
					'has_valid_auth_token': bool(config.get('configurable', {}).get('authorization_token')),
					'user_input': user_message,
				},
			)

			logger.info(f'[_business_process_analysis_node] Identified process type: {process_type.value}')

			# Get process definition
			process_def = self.business_process_manager.get_process_definition(process_type)

			# Evaluate business rules
			triggered_rules = self.business_process_manager.evaluate_rules(
				process_type,
				{
					'user_input': user_message,
					'has_cv_context': bool(state.get('cv_context')),
					'has_valid_auth_token': bool(config.get('configurable', {}).get('authorization_token')),
					'profile_completeness': 1.0,  # Default complete
					'context_completeness': 1.0,  # Default complete
				},
			)

			logger.info(f'[_business_process_analysis_node] Triggered {len(triggered_rules)} business rules')

			# Store business process information
			return {
				**state,
				'business_process_type': process_type.value,
				'business_process_definition': (process_def.name if process_def else None),
				'triggered_rules': [rule.name for rule in triggered_rules],
				'required_tools': process_def.required_tools if process_def else [],
			}

		except Exception as e:
			logger.error(f'[_business_process_analysis_node] Analysis failed: {str(e)}')
			# Default to general conversation
			return {
				**state,
				'business_process_type': BusinessProcessType.GENERAL_CONVERSATION.value,
				'business_process_error': str(e),
			}

	async def _output_validation_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Output Validation Node - Validates AI response through LLM guardrails"""
		logger.info('[_output_validation_node] Starting output validation')

		# Get the last AI message
		messages = state.get('messages', [])
		ai_response = None
		for msg in reversed(messages):
			if isinstance(msg, AIMessage):
				ai_response = msg.content
				break

		if not ai_response:
			logger.warning('[_output_validation_node] No AI response found')
			return {
				**state,
				'output_validation': {'is_safe': True, 'no_response': True},
			}

		try:
			# Validate AI response through guardrails
			validation_result = await self.guardrails_manager.validate_ai_response(
				ai_response,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'business_process_type': state.get('business_process_type'),
					'timestamp': datetime.now().isoformat(),
				},
			)

			logger.info(f'[_output_validation_node] Output validation: {validation_result["is_safe"]} - {validation_result["summary"]}')

			# Store validation results
			return {
				**state,
				'output_validation': validation_result,
				'response_safe': validation_result['is_safe'],
			}

		except Exception as e:
			logger.error(f'[_output_validation_node] Output validation failed: {str(e)}')
			# Allow response to proceed on validation error
			return {
				**state,
				'output_validation': {'is_safe': True, 'error': str(e)},
				'response_safe': True,
			}

	def _route_after_output_validation(self, state: AgentState) -> str:
		"""Route after output validation - check if we need to continue or end"""
		validation_result = state.get('output_validation', {})

		# If output validation failed critically, we might want to retry
		if not validation_result.get('is_safe', True):
			severity = validation_result.get('overall_severity', 'low')
			if severity in ['high', 'critical']:
				# For high/critical violations, try to regenerate response
				retry_count = state.get('retry_count', 0)
				if retry_count < 2:  # Max 2 retries
					logger.warning(f'[_route_after_output_validation] Critical violation detected, retrying (attempt {retry_count + 1})')
					# Increment retry count for next attempt
					state['retry_count'] = retry_count + 1
					return 'continue'
				else:
					logger.error('[_route_after_output_validation] Max retries exceeded, ending with safety warning')
					# Add safety message to final response
					messages = state.get('messages', [])
					if messages:
						last_msg = messages[-1]
						if hasattr(last_msg, 'content'):
							last_msg.content += '\n\n⚠️ Lưu ý: Phản hồi này có thể cần được xem xét thêm.'

		# Normal flow - end the conversation
		return 'end'

	async def _tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		logger.info('[_tools_node] Executing tools node')

		# Validate tool calls through guardrails before execution
		last_message = state.get('messages', [])[-1] if state.get('messages') else None
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			try:
				for tool_call in last_message.tool_calls:
					tool_validation = await self.guardrails_manager.validate_tool_usage(
						tool_call.get('name', 'unknown'),
						tool_call.get('args', {}),
						context={
							'user_id': state.get('user_id'),
							'business_process_type': state.get('business_process_type'),
							'conversation_id': state.get('conversation_id'),
						},
					)
					if not tool_validation.get('is_safe', True):
						logger.warning(f'[_tools_node] Tool call validation failed: {tool_validation["summary"]}')
						# Continue with execution but log the concern
			except Exception as e:
				logger.error(f'[_tools_node] Tool validation failed: {str(e)}')
				# Continue with execution on validation error

		# Update tools with authorization token if available
		auth_token = config.get('configurable', {}).get('authorization_token')
		logger.info(f'[_tools_node] Authorization token available: {bool(auth_token)}')

		if auth_token:
			logger.info(f'[_tools_node] Setting authorization token for tools: {auth_token[:20]}...')

			# Set authorization token for question composer tool using global function
			try:
				from .tools.question_composer_tool import set_authorization_token

				set_authorization_token(auth_token)
				logger.info('[_tools_node] Authorization token set for question composer tool')
			except ImportError as e:
				logger.warning(f'[_tools_node] Could not import question composer token setter: {e}')

			# For any other tools that support set_authorization_token method
			for tool in self._tools:
				if hasattr(tool, 'set_authorization_token'):
					logger.info(f'[_tools_node] Setting token for tool: {tool.name}')
					tool.set_authorization_token(auth_token)
				else:
					logger.debug(f'[_tools_node] Tool {getattr(tool, "name", "unknown")} does not support authorization token')
		else:
			logger.warning('[_tools_node] No authorization token provided in config')

		# Execute tools
		tool_node = ToolNode(self._tools)
		result = await tool_node.ainvoke(state, config or {})
		logger.info('[_tools_node] Tools execution completed')
		return result

	async def _agent_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Main Agent Node with RAG context - generates response without deciding on tools"""
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		# Get RAG context if available
		if not state.get('combined_rag_context'):
			state = await self._get_rag_context(state, thread_id)

		# Build system prompt with persona
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.config and self.config.persona_enabled:
			persona_prompt = self.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt
				logger.info(f'[_agent_node] Using persona prompt: {self.config.persona_type.value}')

		# Add business process context
		business_process_type = state.get('business_process_type')
		if business_process_type:
			process_context = f'\n\nBUSINESS PROCESS: {business_process_type}'
			triggered_rules = state.get('triggered_rules', [])
			if triggered_rules:
				process_context += f'\nActive Rules: {", ".join(triggered_rules)}'
			system_prompt += process_context

		# Add RAG context if available
		combined_context = state.get('combined_rag_context')
		if combined_context:
			system_prompt += f'\n\nKNOWLEDGE CONTEXT:\n{combined_context[:1000]}\n'

		# Prepare messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=system_prompt)]}

		# Check if this is a tool response cycle
		tool_decision = state.get('tool_decision', {})
		if tool_decision.get('decision') == 'use_tools':
			# If we decided to use tools, bind appropriate tools based on business process
			required_tools = state.get('required_tools', [])
			all_tools = get_tool_definitions(self.config)

			# Filter tools based on business process requirements if specified
			if required_tools:
				filtered_tools = [tool for tool in all_tools if getattr(tool, 'name', '') in required_tools]
				if filtered_tools:
					all_tools = filtered_tools
					logger.info(f'[_agent_node] Using filtered tools for business process: {required_tools}')

			model_with_tools = self.llm.bind_tools(all_tools)

			# Add instruction to use tools with business context
			enhanced_system_prompt = system_prompt + '\n\nBạn có thể sử dụng các công cụ có sẵn để trả lời câu hỏi tốt hơn. Hãy sử dụng chúng phù hợp với quy trình nghiệp vụ hiện tại.'
			enhanced_messages = [SystemMessage(content=enhanced_system_prompt)] + messages
			response = await model_with_tools.ainvoke(enhanced_messages)
		else:
			# Normal response without tools
			enhanced_messages = [SystemMessage(content=system_prompt)] + messages
			response = await self.llm.ainvoke(enhanced_messages)

		return {**state, 'messages': messages + [response]}

	async def _tool_decision_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Tool Decision Node - Decides whether to use tools based on user query and business process"""
		messages = state.get('messages', [])
		if not messages:
			return {
				**state,
				'tool_decision': {
					'decision': 'no_tools',
					'reasoning': 'No messages found',
				},
			}

		# Get the latest user message
		user_message = None
		for msg in reversed(messages):
			if isinstance(msg, HumanMessage) or (hasattr(msg, 'content') and not isinstance(msg, (AIMessage, SystemMessage))):
				user_message = msg.content if hasattr(msg, 'content') else str(msg)
				break

		if not user_message:
			return {
				**state,
				'tool_decision': {
					'decision': 'no_tools',
					'reasoning': 'No user message found',
				},
			}

		# Get available tools and business process context
		available_tools = get_tools(self.config)
		tool_names = [tool.name for tool in available_tools]
		business_process_type = state.get('business_process_type', 'general_conversation')
		required_tools = state.get('required_tools', [])
		triggered_rules = state.get('triggered_rules', [])

		# Create enhanced decision prompt with business context
		decision_prompt = f"""
Yêu cầu của người dùng: "{user_message}"

Quy trình nghiệp vụ: {business_process_type}
{f'Công cụ bắt buộc: {", ".join(required_tools)}' if required_tools else ''}
{f'Quy tắc đã kích hoạt: {", ".join(triggered_rules)}' if triggered_rules else ''}

Tất cả công cụ có sẵn: {', '.join(tool_names)}

Context hiện tại: {state.get('combined_rag_context', 'Không có context')[:200]}...

Dựa trên quy trình nghiệp vụ và yêu cầu người dùng, hãy quyết định có cần sử dụng tools hay không.
"""

		# Get tool decision
		try:
			decision_messages = [
				SystemMessage(content=TOOL_DECISION_SYSTEM_PROMPT),
				HumanMessage(content=decision_prompt),
			]

			decision_response = await self.tool_decision_llm.ainvoke(decision_messages)

			# Convert to dict if it's a Pydantic model
			if hasattr(decision_response, 'model_dump'):
				tool_decision = decision_response.model_dump()
			else:
				tool_decision = decision_response

			# Override decision if business process requires tools
			if required_tools and tool_decision.get('decision') == 'no_tools':
				logger.info(f'[_tool_decision_node] Overriding decision due to business process requirements: {required_tools}')
				tool_decision.update({
					'decision': 'use_tools',
					'reasoning': f'Business process {business_process_type} requires tools: {", ".join(required_tools)}',
					'business_override': True,
				})

			logger.info(f'Tool Decision: {tool_decision.get("decision")} - {tool_decision.get("reasoning")}')

			return {**state, 'tool_decision': tool_decision}

		except Exception as e:
			logger.error(f'Tool decision failed: {str(e)}')
			# Default based on business process requirements
			default_decision = 'use_tools' if required_tools else 'no_tools'
			return {
				**state,
				'tool_decision': {
					'decision': default_decision,
					'reasoning': f'Decision failed: {str(e)}. Using business process default.',
					'confidence': 0.5,
					'fallback': True,
				},
			}

	def _route_after_tool_decision(self, state: AgentState) -> str:
		"""Route based on tool decision"""
		tool_decision = state.get('tool_decision', {})
		decision = tool_decision.get('decision', 'no_tools')

		if decision == 'use_tools':
			return 'use_tools'
		else:
			return 'no_tools'

	async def _get_rag_context(self, state: AgentState, thread_id: str) -> AgentState:
		"""Get RAG context from both conversation and global KB"""
		messages = state.get('messages', [])
		if not messages:
			return state

		# Get user query
		user_query = None
		for msg in reversed(messages):
			if hasattr(msg, 'content') and msg.content:
				user_query = msg.content
				break

		if not user_query:
			return state

		combined_context = ''

		# Search Conversation KB
		try:
			collection_id = f'conversation_{thread_id}'
			from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
			from app.modules.agentic_rag.repository.kb_repo import KBRepository

			kb_repo = KBRepository(collection_name=collection_id)
			rag_agent = RAGAgentGraph(kb_repo=kb_repo, collection_id=collection_id)
			conv_result = await rag_agent.answer_query(query=user_query, collection_id=collection_id)

			conv_answer = conv_result.get('answer', '')
			if conv_answer:
				combined_context += f'Conversation Knowledge: {conv_answer}\n\n'
		except Exception:
			pass

		# Search Global KB
		if self.global_kb_service:
			try:
				global_results = await self.global_kb_service.search_global_knowledge(user_query, top_k=2)
				if global_results:
					contexts = []
					for item in global_results:
						content = item.get('content', '')
						if content:
							contexts.append(content)
					if contexts:
						combined_context += f'Global Knowledge: {" ".join(contexts)}'
			except Exception:
				pass

		return {
			**state,
			'combined_rag_context': combined_context,
			'rag_used': bool(combined_context),
		}

	def _should_continue(self, state: AgentState) -> str:
		"""Determine if agent should continue with tools or end (used after tool execution)"""
		messages = state.get('messages', [])
		if not messages:
			return END

		last_message = messages[-1]
		# After tool execution, check if there are more tool calls needed
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			return 'tool_decision'  # Go back to tool decision for another round
		return END

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		conversation_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Process message with simplified workflow"""
		session_id = conversation_id or f'session_{int(time.time())}'

		try:
			# Create initial state
			initial_state = StateManager.create_initial_state(user_message=user_message, user_id=user_id, session_id=session_id)

			# Prepare config
			runtime_config = {
				'configurable': {
					'thread_id': session_id,
					**self.config.to_dict(),
				}
			}

			if config_override:
				runtime_config['configurable'].update(config_override)

			# Execute workflow
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)  # Extract response
			response = self._extract_response(final_state)

			return {
				'response': response,
				'state': final_state,
				'metadata': {
					'workflow_type': 'enhanced_enterview_workflow',
					'persona_type': (self.config.persona_type.value if self.config else 'enterview_assistant'),
					'rag_used': bool(final_state.get('combined_rag_context')),
					'tool_decision': final_state.get('tool_decision', {}),
					'tools_used': self._count_tool_usage(final_state),
					'business_process': {
						'type': final_state.get('business_process_type'),
						'definition': final_state.get('business_process_definition'),
						'triggered_rules': final_state.get('triggered_rules', []),
						'required_tools': final_state.get('required_tools', []),
					},
					'guardrails': {
						'input_validation': final_state.get('input_validation', {}),
						'output_validation': final_state.get('output_validation', {}),
						'validation_passed': final_state.get('validation_passed', True),
						'response_safe': final_state.get('response_safe', True),
					},
				},
			}
		except Exception as e:
			return {
				'response': f'Xin lỗi, có lỗi xảy ra trong hệ thống EnterViu. Vui lòng thử lại: {str(e)}',
				'state': {},
				'metadata': {
					'error': str(e),
					'workflow_type': 'enhanced_enterview_workflow',
					'persona_type': (self.config.persona_type.value if self.config else 'enterview_assistant'),
					'guardrails_active': True,
					'business_process_active': True,
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response from final state with safety considerations"""
		messages = final_state.get('messages', [])
		if messages:
			last_message = messages[-1]
			response = last_message.content if hasattr(last_message, 'content') else str(last_message)

			# Check if there were validation issues and add appropriate notices
			validation_result = final_state.get('output_validation', {})
			if not validation_result.get('is_safe', True):
				severity = validation_result.get('overall_severity', 'low')
				if severity in ['medium', 'high', 'critical']:
					response += '\n\n⚠️ Lưu ý: Phản hồi này đã được xem xét qua hệ thống kiểm duyệt.'

			return response
		return 'Xin lỗi, không thể tạo phản hồi phù hợp. Vui lòng thử lại với câu hỏi khác.'

	def _count_tool_usage(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
		"""Count tool usage in the workflow with business process context"""
		messages = final_state.get('messages', [])
		tool_calls_count = 0
		tools_used = []
		tool_validations = []

		for msg in messages:
			if hasattr(msg, 'tool_calls') and msg.tool_calls:
				tool_calls_count += len(msg.tool_calls)
				for tc in msg.tool_calls:
					tool_name = tc.get('name', 'unknown')
					if tool_name not in tools_used:
						tools_used.append(tool_name)

		return {
			'total_tool_calls': tool_calls_count,
			'unique_tools_used': tools_used,
			'tool_decision_made': bool(final_state.get('tool_decision')),
			'business_process_type': final_state.get('business_process_type'),
			'required_tools_met': all(tool in tools_used for tool in final_state.get('required_tools', [])),
			'triggered_rules': final_state.get('triggered_rules', []),
			'guardrails_passed': final_state.get('validation_passed', True) and final_state.get('response_safe', True),
		}

	async def initialize_global_knowledge(self) -> Dict[str, Any]:
		"""Initialize Global Knowledge Base"""
		if not self.global_kb_service:
			return {'error': 'Global KB Service not available'}

		try:
			result = await self.global_kb_service.initialize_default_knowledge()
			return result
		except Exception as e:
			return {'error': str(e)}


# Factory functions
def create_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Factory function to create enhanced EnterViu workflow with business process management and LLM guardrails"""
	return Workflow(db_session, config)
