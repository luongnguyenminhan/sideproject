"""
Simplified Chat Workflow
Router → RAG Query (Always Dual) → Agent → Tools → Response Generator
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Literal, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import NodeInterrupt

from .state.workflow_state import AgentState, StateManager
from .config.workflow_config import WorkflowConfig
from .tools.basic_tools import get_tools, get_tool_definitions
from .utils.color_logger import get_color_logger, Colors
from .guardrails.manager import ChatWorkflowGuardrailManager

load_dotenv()

# Initialize colorful logger
logger = get_color_logger(__name__)


# Router Schema
class RouterDecision(BaseModel):
	"""Router decision schema for query routing."""

	target: Literal['rag_query', 'agent'] = Field(description='Target node để route query đến')
	explanation: str = Field(description='Explanation cho quyết định routing')


# System Prompts
DEFAULT_SYSTEM_PROMPT = """
🌟 Bạn là CGSEM AI Assistant - Trợ lý thông minh của CLB Truyền thông và Sự Kiện trường THPT Cần Giuộc

📖 VỀ CGSEM:
CLB Truyền thông và Sự Kiện trường THPT Cần Giuộc (CGSEM) là tổ chức truyền thông phi lợi nhuận được thành lập 14/12/2020, với kim chỉ nam: "Cụ thể - Đa dạng - Văn minh - Công bằng"

🎯 NHIỆM VỤ CỦA BẠN:
1. Hỗ trợ thành viên và người quan tâm đến CGSEM
2. Cung cấp thông tin về hoạt động, dự án của CLB
3. Hướng dẫn tham gia các chương trình truyền thông, sự kiện
4. Truyền cảm hứng về tinh thần "tiên quyết, tiên phong, sáng tạo"
5. Thực hiện các phép tính cơ bản khi cần thiết
6. Sử dụng kiến thức từ tài liệu để tư vấn chuyên nghiệp

🛠️ CÔNG CỤ CÓ SẴN:
- Phép tính: add, subtract, multiply, divide
- RAG: Truy xuất thông tin từ knowledge base
- Dual RAG: Kết hợp Global KB + Conversation KB

🗣️ PHONG CÁCH GIAO TIẾP:
- Nhiệt tình, tích cực và truyền cảm hứng
- Gần gũi với học sinh và giới trẻ
- Khuyến khích sáng tạo và dám thử thách
- Trả lời tự nhiên như thành viên thực sự của CGSEM
- KHÔNG ĐƯỢC SỬ DỤNG QUOTE ` ` (INLINE QUOTE) trong câu trả lời

⚡ PHƯƠNG CHÂM: "CGSEM - tiên quyết, tiên phong, sáng tạo"
"""
ROUTER_SYSTEM_PROMPT = """
🧭 Bạn là Router Agent thông minh cho hệ thống CGSEM AI Assistant. Phân tích user query và quyết định route phù hợp nhất.

🎯 TARGET NODES AVAILABLE:
1. "rag_query" - Cho câu hỏi liên quan đến kiến thức, thông tin cần truy xuất từ knowledge base
2. "agent" - Cho các câu hỏi trò chuyện thông thường, toán học đơn giản

📋 QUY TẮC ROUTING:
- Nếu câu hỏi liên quan đến kiến thức, thông tin, hoạt động, dự án, lịch sử: chọn "rag_query"
- Nếu là câu hỏi trò chuyện thông thường, tính toán đơn giản: chọn "agent"

⚠️ LƯU Ý: Ưu tiên "rag_query" cho hầu hết câu hỏi về thông tin.
"""


class Workflow:
	"""Simplified Chat Workflow: Router → RAG Query (Always Dual) → Agent → Tools → Response Generator"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize simplified workflow"""
		self.start_time = time.time()
		logger.workflow_start(
			'Simplified Workflow Initialization',
			db_session_type=type(db_session).__name__,
			config_provided=config is not None,
		)

		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		self.config.db_session = db_session

		# Initialize LLM
		self.llm = ChatGoogleGenerativeAI(model=self.config.model_name, temperature=self.config.temperature)

		# Initialize services
		self._init_global_kb_service()
		self._init_guardrails()

		# Build workflow
		self.compiled_graph = self._build_workflow()

		logger.success(
			'🚀 Simplified Workflow initialized successfully',
			initialization_time=time.time() - self.start_time,
		)

	def _init_global_kb_service(self):
		"""Initialize Global Knowledge Base Service"""
		try:
			from app.modules.agentic_rag.services.global_kb_service import (
				GlobalKBService,
			)

			self.global_kb_service = GlobalKBService(self.db_session)
			logger.info('Global KB Service initialized successfully')
		except Exception as e:
			logger.error(f'Error initializing Global KB Service: {str(e)}')
			self.global_kb_service = None

	def _init_guardrails(self):
		"""Initialize Guardrail System"""
		try:
			guardrail_config = {
				'enable_input_guardrails': True,
				'enable_output_guardrails': True,
				'max_input_length': 5000,
				'strict_mode': False,
			}
			self.guardrail_manager = ChatWorkflowGuardrailManager(guardrail_config)
			logger.info('Guardrail system initialized successfully')
		except Exception as e:
			logger.error(f'Error initializing guardrails: {str(e)}')
			self.guardrail_manager = None

	def _build_workflow(self) -> StateGraph:
		"""Build simplified workflow với dual RAG mặc định"""
		workflow = StateGraph(AgentState)

		# Get tools
		tools = get_tools(self.config)
		tool_node = ToolNode(tools)

		# Create wrapper functions for nodes
		async def router_wrapper(state, config=None):
			return await self._router_node(state, config or {})

		async def rag_query_wrapper(state, config=None):
			return await self._rag_query_node(state, config or {})

		async def agent_wrapper(state, config=None):
			return await self._agent_node(state, config or {})

		async def response_wrapper(state, config=None):
			return await self._response_generator_node(state, config or {})

		def route_wrapper(state):
			return self._route_decision(state)

		def should_continue_wrapper(state):
			return self._should_continue(state)

		# Add simplified nodes
		workflow.add_node('router', router_wrapper)
		workflow.add_node('rag_query', rag_query_wrapper)
		workflow.add_node('agent', agent_wrapper)
		workflow.add_node('tools', tool_node)
		workflow.add_node('response_generator', response_wrapper)

		# Set entry point
		workflow.set_entry_point('router')

		# Simplified routing: router → (rag_query | agent)
		workflow.add_conditional_edges(
			'router',
			route_wrapper,
			{
				'rag_query': 'rag_query',
				'agent': 'agent',
			},
		)

		# Simple flow: rag_query → response_generator
		workflow.add_edge('rag_query', 'response_generator')

		# Agent flow: agent → (tools | END)
		workflow.add_conditional_edges('agent', should_continue_wrapper, {'tools': 'tools', END: END})
		workflow.add_edge('tools', 'agent')

		# Response generator → END
		workflow.add_edge('response_generator', END)

		# Compile with memory
		checkpointer = MemorySaver()
		return workflow.compile(checkpointer=checkpointer)

	async def _router_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Router Node với Intelligent routing + Guardrails"""
		start_time = time.time()
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		logger.workflow_start(
			'Router Node - Intelligent Query Routing with Guardrails',
			thread_id=thread_id,
			router_enabled=True,
			guardrails_enabled=True,
		)

		# Get user message
		messages = state.get('messages', [])
		if not messages:
			return {
				**state,
				'router_decision': {
					'target': 'general',
					'explanation': 'No user input',
				},
			}

		# Extract user query
		user_query = None
		for msg in reversed(messages):
			if hasattr(msg, 'content') and msg.content:
				user_query = msg.content
				break

		if not user_query:
			return {
				**state,
				'router_decision': {'target': 'general', 'explanation': 'Empty query'},
			}

		# Apply guardrails
		if self.guardrail_manager:
			try:
				guardrail_context = {
					'thread_id': thread_id,
					'user_id': config.get('configurable', {}).get('user_id', 'unknown'),
					'conversation_step': 'router_input',
				}

				guardrail_result = self.guardrail_manager.check_user_input(user_query, guardrail_context)

				if not guardrail_result.passed:
					logger.error('Input BLOCKED by guardrails')
					return {
						**state,
						'router_decision': {
							'target': 'general',
							'explanation': 'Input blocked by content safety guardrails',
						},
						'guardrail_blocked': True,
					}

				if guardrail_result.modified_content:
					user_query = guardrail_result.modified_content

			except Exception as e:
				logger.error(f'Guardrail check failed: {str(e)}')

		# Route decision using LLM
		try:
			router_prompt = ChatPromptTemplate.from_messages([
				('system', ROUTER_SYSTEM_PROMPT),
				(
					'human',
					'User query: {input}\n\nAnalyze and determine the best routing target.',
				),
			])

			router_chain = router_prompt | self.llm.with_structured_output(RouterDecision)
			router_result = await router_chain.ainvoke({'input': user_query})

			target = router_result.target if hasattr(router_result, 'target') else 'general'
			explanation = router_result.explanation if hasattr(router_result, 'explanation') else 'Default routing'

			logger.info(f'🎯 Router Decision: {target} - {explanation}')

			processing_time = time.time() - start_time
			logger.workflow_complete(
				'Router Node - Intelligent Query Routing with Guardrails',
				processing_time,
				target_selected=target,
			)

			return {
				**state,
				'router_decision': {'target': target, 'explanation': explanation},
				'routing_complete': True,
			}

		except Exception as e:
			logger.error(f'Router failed: {str(e)}')
			return {
				**state,
				'router_decision': {
					'target': 'general',
					'explanation': f'Router error: {str(e)[:100]}',
				},
				'routing_complete': True,
			}

	async def _rag_query_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""RAG Query Node - Always use Dual RAG (Global KB + Conversation KB)"""
		start_time = time.time()
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		logger.workflow_start('RAG Query Node - Dual RAG Retrieval', thread_id=thread_id)

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

		try:
			# Always use dual RAG approach
			conv_context = ''
			global_context = ''

			# 1. Search Conversation KB
			try:
				collection_id = f'conversation_{thread_id}'
				logger.info(f'🔍 Searching conversation KB: {collection_id}')

				from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
				from app.modules.agentic_rag.repository.kb_repo import KBRepository

				kb_repo = KBRepository(collection_name=collection_id)
				rag_agent = RAGAgentGraph(kb_repo=kb_repo, collection_id=collection_id)
				conv_result = await rag_agent.answer_query(query=user_query, collection_id=collection_id)

				conv_answer = conv_result.get('answer', '')
				conv_sources = conv_result.get('sources', [])

				if conv_answer:
					conv_context = f'📁 Conversation Knowledge:\n{conv_answer}'
					if conv_sources:
						conv_context += '\n📚 Sources:'
						for i, source in enumerate(conv_sources, 1):
							source_info = f'\n{i}. Document ID: {source.get("id", "Unknown")}'
							if 'metadata' in source and 'source' in source['metadata']:
								source_info += f' (File: {source["metadata"]["source"]})'
							conv_context += source_info

			except Exception as e:
				logger.warning(f'Conversation KB search failed: {str(e)}')

			# 2. Search Global KB
			if self.global_kb_service:
				try:
					logger.info('🌍 Searching global KB')
					global_results = await self.global_kb_service.search_global_knowledge(user_query, top_k=3)
					logger.debug(f'[DEBUG] Global KB search results: {global_results}')
					if global_results:
						# Combine top results into a single context string
						contexts = []
						for i, item in enumerate(global_results, 1):
							content = item.get('content', '')
							title = item.get('metadata', {}).get('title', '')
							source = item.get('metadata', {}).get('source', '')
							if title or source:
								contexts.append(f'{i}. {title}\n{content}\n(Source: {source})')
							else:
								contexts.append(f'{i}. {content}')
						global_context = '🌍 Global Knowledge:\n' + '\n\n'.join(contexts)
				except Exception as e:
					logger.warning(f'Global KB search failed: {str(e)}')

			# 3. Combine both contexts
			combined_context = ''
			if conv_context and global_context:
				combined_context = f'{conv_context}\n\n{global_context}'
			elif conv_context:
				combined_context = conv_context
			elif global_context:
				combined_context = global_context

			processing_time = time.time() - start_time
			logger.workflow_complete(
				'RAG Query Node - Dual RAG Retrieval',
				processing_time,
				context_retrieved=bool(combined_context),
				conv_context_found=bool(conv_context),
				global_context_found=bool(global_context),
			)

			return {
				**state,
				'combined_rag_context': combined_context,
				'dual_rag_used': True,
				'retrieval_quality': 'good' if combined_context else 'no_results',
			}

		except Exception as e:
			logger.error(f'Dual RAG Query failed: {str(e)}')
			return {
				**state,
				'combined_rag_context': '',
				'dual_rag_used': False,
				'retrieval_quality': 'error',
			}

	async def _agent_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Main Agent Node với RAG context và tools"""
		start_time = time.time()
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		logger.workflow_start(
			'Agent Node - Model Invocation with Context and Tools',
			thread_id=thread_id,
			has_context=bool(state.get('combined_rag_context')),
		)

		# Get system prompt with persona support
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.config and self.config.persona_enabled:
			persona_prompt = self.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt

		# Build enhanced system prompt
		persona_info = ''
		if self.config and self.config.persona_enabled:
			persona_info = f"""
🎭 PERSONA ACTIVE: {self.config.get_persona_name()}
Persona Type: {self.config.persona_type.value if self.config.persona_type else 'none'}
"""

		enhanced_system = f"""{system_prompt}

🤖 SIMPLIFIED WORKFLOW AI:{persona_info}

🛠️ AVAILABLE TOOLS:
- add(a, b): Cộng hai số
- subtract(a, b): Trừ hai số  
- multiply(a, b): Nhân hai số
- divide(a, b): Chia hai số

📊 CONTEXT: {thread_id}
📈 RAG Status: {state.get('retrieval_quality', 'unknown')}
🔥 Features: Router + Dual RAG + Guardrails + Tools

🌟 HƯỚNG DẪN:
1. 📚 Sử dụng dual RAG context được cung cấp làm nguồn chính
2. 🧮 Sử dụng math tools khi cần tính toán
3. 💡 Kết hợp kiến thức để trả lời toàn diện
4. 🎯 Trả lời tự nhiên, không ghi nguồn context
5. 🗣️ Giữ tinh thần CGSEM nhiệt huyết và sáng tạo
"""

		# Add dual RAG context if available
		combined_context = state.get('combined_rag_context')
		if combined_context:
			enhanced_system += f'\n\n🔗 DUAL RAG KNOWLEDGE BASE:\n{combined_context}'

		# Prepare messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=enhanced_system)]}

		# Create prompt
		prompt = ChatPromptTemplate.from_messages([
			('system', enhanced_system),
			MessagesPlaceholder(variable_name='chat_history'),
			MessagesPlaceholder(variable_name='agent_scratchpad'),
		])

		formatted_prompt = prompt.format_messages(
			chat_history=messages,
			agent_scratchpad=[],
		)

		# Invoke model with tools
		tool_definitions = get_tool_definitions(self.config)
		model_with_tools = self.llm.bind_tools(tool_definitions)

		response = await model_with_tools.ainvoke(
			formatted_prompt,
			{
				'system_time': datetime.now(tz=timezone.utc).isoformat(),
				'unified_mode': True,
				'conversation_id': thread_id,
			},
		)

		processing_time = time.time() - start_time
		logger.workflow_complete(
			'Agent Node - Model Invocation',
			processing_time,
			response_length=len(str(response.content)),
		)

		return {**state, 'messages': messages + [response]}

	async def _response_generator_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Generate final response với RAG context"""
		logger.info('📝 Response generator executing...')

		try:
			messages = state.get('messages', [])
			combined_context = state.get('combined_rag_context', '')

			# Build enhanced prompt
			if combined_context:
				system_prompt = f"""Bạn là AI assistant thông minh với khả năng truy cập kiến thức từ nhiều nguồn.

CONTEXT TỪ KNOWLEDGE BASES:
{combined_context}

HƯỚNG DẪN:
- Sử dụng thông tin từ context để trả lời câu hỏi
- Nếu context không đủ, hãy thừa nhận và đưa ra câu trả lời tốt nhất có thể
- Luôn cung cấp thông tin chính xác và hữu ích
- Trả lời bằng tiếng Việt trừ khi được yêu cầu khác
- Ghi rõ nguồn thông tin khi cần thiết
"""
			else:
				system_prompt = DEFAULT_SYSTEM_PROMPT

			# Generate response
			enhanced_messages = [SystemMessage(content=system_prompt)] + messages
			response = await self.llm.ainvoke(enhanced_messages)

			# Add metadata
			routing_info = state.get('dual_rag_routing', {})
			if routing_info:
				metadata_note = f'\n\n_[Sử dụng {routing_info} knowledge base(s)]_'
				response.content += metadata_note

			return {
				**state,
				'messages': messages + [response],
				'current_node': 'response_generator',
			}

		except Exception as e:
			logger.error(f'Response generator error: {str(e)}')
			error_response = AIMessage(content=f'Xin lỗi, có lỗi trong quá trình tạo phản hồi: {str(e)}')
			return {**state, 'messages': state.get('messages', []) + [error_response]}

	def _route_decision(self, state: AgentState) -> str:
		"""Simplified route decision logic"""
		router_decision = state.get('router_decision', {})
		target = router_decision.get('target', 'agent') if isinstance(router_decision, dict) else 'agent'

		# Simple mapping
		if target == 'rag_query':
			actual_target = 'rag_query'
		else:
			actual_target = 'agent'

		logger.info(f'🔀 Routing: {target} → {actual_target}')
		return actual_target

	def _should_continue(self, state: AgentState) -> str:
		"""Determine if agent should continue with tools or end"""
		messages = state.get('messages', [])
		if not messages:
			return END

		last_message = messages[-1]
		if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
			return END
		else:
			return 'tools'

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		conversation_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Process message với unified workflow"""
		start_time = time.time()
		session_id = conversation_id or f'session_{int(time.time())}'

		logger.workflow_start(
			'Simplified Workflow Message Processing',
			user_id=user_id,
			conversation_id=conversation_id,
			message_length=len(user_message),
		)

		try:
			# Create initial state
			initial_state = StateManager.create_initial_state(user_message=user_message, user_id=user_id, session_id=session_id)

			# Add conversation_id to metadata
			if conversation_id:
				initial_state['conversation_metadata']['conversation_id'] = conversation_id

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
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)

			# Extract response
			response = self._extract_response(final_state)
			processing_time = time.time() - start_time

			logger.success(
				'Simplified Workflow processing completed',
				processing_time=processing_time,
				response_length=len(response),
				features_used={
					'router': final_state.get('routing_complete', False),
					'dual_rag': bool(final_state.get('combined_rag_context')),
					'guardrails': not final_state.get('guardrail_blocked', False),
				},
			)

			return {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'workflow_type': 'simplified',
					'router_decision': final_state.get('router_decision'),
					'dual_rag_used': bool(final_state.get('combined_rag_context')),
					'guardrails_passed': not final_state.get('guardrail_blocked', False),
				},
			}

		except Exception as e:
			logger.error(f'Simplified workflow error: {str(e)}')
			return {
				'response': f'Xin lỗi, có lỗi xảy ra trong quá trình xử lý: {str(e)}',
				'state': {},
				'metadata': {
					'processing_time': time.time() - start_time,
					'error': str(e),
					'workflow_type': 'simplified',
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response from final state"""
		messages = final_state.get('messages', [])
		if messages:
			last_message = messages[-1]
			return last_message.content if hasattr(last_message, 'content') else str(last_message)
		return 'Không có phản hồi được tạo.'

	async def initialize_global_knowledge(self) -> Dict[str, Any]:
		"""Initialize Global Knowledge Base"""
		if not self.global_kb_service:
			return {'error': 'Global KB Service not available'}

		try:
			result = await self.global_kb_service.initialize_default_knowledge()
			logger.info('Global Knowledge Base initialized successfully')
			return result
		except Exception as e:
			logger.error(f'Error initializing global knowledge: {str(e)}')
			return {'error': str(e)}


# Factory functions
def create_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Factory function để tạo simplified workflow"""
	return Workflow(db_session, config)


# Backward compatibility aliases
def create_unified_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)


def create_agentic_rag_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)


def create_enhanced_dual_rag_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)


def create_workflow_with_rag(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)
