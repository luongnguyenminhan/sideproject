"""
Enhanced Dual RAG Workflow for Chat System
Tích hợp Global KB + Conversation KB với intelligent routing
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from .state.workflow_state import AgentState, StateManager
from .config.workflow_config import WorkflowConfig
from .tools.basic_tools import get_tools
from .utils.color_logger import get_color_logger, Colors

logger = get_color_logger(__name__)


class EnhancedDualRAGWorkflow:
	"""Enhanced Chat Workflow với Dual RAG system"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize enhanced dual RAG workflow"""
		self.start_time = time.time()
		logger.workflow_start(
			'Enhanced Dual RAG Workflow Initialization',
			db_session_type=type(db_session).__name__,
			config_provided=config is not None,
		)

		self.db_session = db_session
		self.config = config or WorkflowConfig.from_env()
		self.config.db_session = db_session

		# Initialize LLM
		self.llm = ChatGoogleGenerativeAI(model=self.config.model_name, temperature=self.config.temperature)

		# Initialize Global KB Service
		self._init_global_kb_service()

		# Build workflow
		self.compiled_graph = self._build_enhanced_workflow()

		logger.success(
			'🚀 Enhanced Dual RAG Workflow initialized successfully',
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

	def _build_enhanced_workflow(self) -> StateGraph:
		"""Build enhanced workflow với dual RAG capabilities"""
		workflow = StateGraph(AgentState)

		# Get enhanced tools including dual RAG tool
		tools = get_tools(self.config)
		tool_node = ToolNode(tools)

		# Add nodes
		workflow.add_node('agent', self._agent_node)
		workflow.add_node('dual_rag_processor', self._dual_rag_processor_node)
		workflow.add_node('tools', tool_node)
		workflow.add_node('response_generator', self._response_generator_node)

		# Add edges
		workflow.add_edge(START, 'agent')
		workflow.add_conditional_edges(
			'agent',
			self._route_agent_decision,
			{
				'dual_rag': 'dual_rag_processor',
				'tools': 'tools',
				'respond': 'response_generator',
			},
		)
		workflow.add_edge('dual_rag_processor', 'response_generator')
		workflow.add_edge('tools', 'agent')
		workflow.add_edge('response_generator', END)

		# Compile với memory saver
		checkpointer = MemorySaver()
		return workflow.compile(checkpointer=checkpointer)

	async def _agent_node(self, state: AgentState) -> AgentState:
		"""Main agent node với dual RAG routing logic"""
		logger.info('🤖 Agent node processing...')

		try:
			messages = state.get('messages', [])
			last_message = messages[-1] if messages else None

			if not last_message:
				return state

			# Analyze message để quyết định có cần dual RAG hay không
			needs_rag = await self._analyze_message_for_rag(last_message.content)

			if needs_rag:
				# Mark for dual RAG processing
				return {
					**state,
					'need_rag': True,
					'current_node': 'agent',
					'next_action': 'dual_rag',
				}
			else:
				# Direct response hoặc use tools
				tools = get_tools(self.config)
				llm_with_tools = self.llm.bind_tools(tools)

				response = await llm_with_tools.ainvoke(messages)

				if response.tool_calls:
					return {
						**state,
						'messages': messages + [response],
						'pending_tool_calls': response.tool_calls,
						'next_action': 'tools',
					}
				else:
					return {
						**state,
						'messages': messages + [response],
						'next_action': 'respond',
					}

		except Exception as e:
			logger.error(f'Error in agent node: {str(e)}')
			error_response = AIMessage(content=f'Xin lỗi, có lỗi xảy ra: {str(e)}')
			return {
				**state,
				'messages': state.get('messages', []) + [error_response],
				'next_action': 'respond',
			}

	async def _dual_rag_processor_node(self, state: AgentState) -> AgentState:
		"""Process dual RAG retrieval và routing"""
		logger.info('🔍 Dual RAG processor node executing...')

		try:
			messages = state.get('messages', [])
			last_message = messages[-1] if messages else None

			if not last_message:
				return state

			# Get conversation metadata
			conv_metadata = state.get('conversation_metadata', {})
			conversation_id = conv_metadata.get('conversation_id', 'default')
			user_id = conv_metadata.get('user_id', 'anonymous')

			# Execute dual RAG using the tool
			from .tools.dual_rag_tool import DualRAGTool

			dual_rag_tool = DualRAGTool(db_session=self.db_session)
			rag_result = dual_rag_tool._run(
				conversation_id=conversation_id,
				user_id=user_id,
				query=last_message.content,
				top_k=5,
			)

			# Parse RAG result
			rag_data = json.loads(rag_result) if isinstance(rag_result, str) else rag_result

			# Update state với dual RAG context
			return {
				**state,
				'dual_rag_routing': rag_data.get('routing_decision'),
				'combined_rag_context': rag_data.get('context', ''),
				'global_rag_context': [s for s in rag_data.get('sources', []) if s.get('source_type') == 'global'],
				'conversation_rag_context': [s for s in rag_data.get('sources', []) if s.get('source_type') == 'conversation'],
				'current_node': 'dual_rag_processor',
				'next_action': 'respond',
			}

		except Exception as e:
			logger.error(f'Error in dual RAG processor: {str(e)}')
			return {
				**state,
				'error_context': {'dual_rag_error': str(e)},
				'next_action': 'respond',
			}

	async def _response_generator_node(self, state: AgentState) -> AgentState:
		"""Generate final response với RAG context"""
		logger.info('📝 Response generator node executing...')

		try:
			messages = state.get('messages', [])
			combined_context = state.get('combined_rag_context', '')

			# Build enhanced prompt với RAG context
			if combined_context:
				system_prompt = f"""Bạn là AI assistant thông minh với khả năng truy cập kiến thức từ nhiều nguồn.

CONTEXT TỪ KNOWLEDGE BASES:
{combined_context}

HƯỚNG DẪN:
- Sử dụng thông tin từ context để trả lời câu hỏi
- Nếu context không đủ, hãy thừa nhận và đưa ra câu trả lời tốt nhất có thể
- Luôn cung cấp thông tin chính xác và hữu ích
- Trả lời bằng tiếng Việt trừ khi được yêu cầu khác
- Ghi rõ nguồn thông tin khi cần thiết (Global KB hoặc Conversation KB)
"""
			else:
				system_prompt = """Bạn là AI assistant thông minh và hữu ích.
Trả lời câu hỏi một cách chính xác và thân thiện.
Sử dụng tiếng Việt trừ khi được yêu cầu khác."""

			# Generate response
			enhanced_messages = [SystemMessage(content=system_prompt)] + messages
			response = await self.llm.ainvoke(enhanced_messages)

			# Add metadata về RAG usage
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
			logger.error(f'Error in response generator: {str(e)}')
			error_response = AIMessage(content=f'Xin lỗi, có lỗi trong quá trình tạo phản hồi: {str(e)}')
			return {**state, 'messages': state.get('messages', []) + [error_response]}

	def _route_agent_decision(self, state: AgentState) -> str:
		"""Route based on agent's decision"""
		next_action = state.get('next_action', 'respond')

		logger.info(f'🔀 Routing decision: {next_action}')

		if next_action == 'dual_rag':
			return 'dual_rag'
		elif next_action == 'tools':
			return 'tools'
		else:
			return 'respond'

	async def _analyze_message_for_rag(self, message_content: str) -> bool:
		"""Phân tích message để quyết định có cần RAG hay không"""
		try:
			# Keywords indicate need for knowledge retrieval
			rag_keywords = [
				'thế nào',
				'là gì',
				'cách',
				'hướng dẫn',
				'giải thích',
				'tại sao',
				'khi nào',
				'ở đâu',
				'ai',
				'how',
				'what',
				'why',
				'when',
				'where',
				'who',
				'explain',
				'tell me',
				'cv',
				'resume',
				'experience',
				'skill',
				'code',
				'programming',
				'development',
			]

			message_lower = message_content.lower()
			needs_rag = any(keyword in message_lower for keyword in rag_keywords)

			# Hoặc có thể dùng LLM để quyết định phức tạp hơn
			if not needs_rag and len(message_content) > 50:
				# For longer messages, use LLM to decide
				decision_prompt = f"""
                Phân tích câu hỏi sau và quyết định có cần tìm kiếm thông tin từ knowledge base không:
                
                Câu hỏi: "{message_content}"
                
                Trả lời chỉ "YES" hoặc "NO".
                """

				decision_response = await self.llm.ainvoke([HumanMessage(content=decision_prompt)])
				needs_rag = 'YES' in decision_response.content.upper()

			logger.info(f'RAG analysis for "{message_content[:50]}...": {needs_rag}')
			return needs_rag

		except Exception as e:
			logger.error(f'Error analyzing message for RAG: {str(e)}')
			return True  # Default to using RAG on error

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		conversation_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Process message với enhanced dual RAG"""
		start_time = time.time()
		session_id = conversation_id or f'session_{int(time.time())}'

		logger.workflow_start(
			'Enhanced Dual RAG Message Processing',
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
				'Enhanced Dual RAG processing completed',
				processing_time=processing_time,
				response_length=len(response),
				dual_rag_used=bool(final_state.get('combined_rag_context')),
			)

			return {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'dual_rag_used': bool(final_state.get('combined_rag_context')),
					'routing_decision': final_state.get('dual_rag_routing'),
					'global_sources': len(final_state.get('global_rag_context', [])),
					'conversation_sources': len(final_state.get('conversation_rag_context', [])),
					'workflow_type': 'enhanced_dual_rag',
				},
			}

		except Exception as e:
			logger.error(f'Error in enhanced dual RAG processing: {str(e)}')
			return {
				'response': f'Xin lỗi, có lỗi xảy ra trong quá trình xử lý: {str(e)}',
				'state': {},
				'metadata': {
					'processing_time': time.time() - start_time,
					'error': str(e),
					'workflow_type': 'enhanced_dual_rag',
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response từ final state"""
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


def create_enhanced_dual_rag_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> EnhancedDualRAGWorkflow:
	"""Factory function để tạo enhanced dual RAG workflow"""
	return EnhancedDualRAGWorkflow(db_session, config)
