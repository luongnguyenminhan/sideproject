"""
Simplified Chat Workflow
Agent → Tools (if needed) → End
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

load_dotenv()

# Simple logger
import logging

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = """Bạn là Enterview AI Assistant - Trợ lý thông minh hỗ trợ người dùng trong việc tìm kiếm việc làm và phát triển sự nghiệp. Hãy trả lời một cách chuyên nghiệp và thân thiện."""

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
- Câu hỏi chung về tư vấn nghề nghiệp
- Trò chuyện thông thường
- Giải thích khái niệm, định nghĩa
- Câu hỏi về kinh nghiệm cá nhân
- Chỉ cần thông tin từ context đã có

Hãy phân tích kỹ yêu cầu và đưa ra quyết định chính xác."""


# Tool Decision Schema
class ToolDecision(BaseModel):
	"""Schema for tool usage decision"""

	decision: str = Field(description="Quyết định sử dụng tool: 'use_tools' hoặc 'no_tools'")
	reasoning: str = Field(description='Lý do cho quyết định này')
	confidence: float = Field(description='Độ tin cậy của quyết định (0.0-1.0)')
	tools_needed: List[str] = Field(default=[], description='Danh sách tools cần thiết (nếu có)')


class Workflow:
	"""Simplified Chat Workflow: Agent → Tool Decision → Tools (if needed) → End"""

	def __init__(self, db_session: Session, config: Optional[WorkflowConfig] = None):
		"""Initialize simplified workflow"""
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
		"""Build simplified workflow: Agent → Tool Decision → Tools (if needed) → End"""
		workflow = StateGraph(AgentState)

		# Get tools
		tools = get_tools(self.config)
		
		# Store tools for runtime updates
		self._tools = tools
		tool_node = ToolNode(tools)

		# Add nodes
		workflow.add_node('agent', self._agent_node)
		workflow.add_node('tool_decision', self._tool_decision_node)
		workflow.add_node('tools', self._tools_node)

		# Set entry point
		workflow.set_entry_point('agent')

		# Workflow flow: agent → tool_decision → (tools | END)
		workflow.add_edge('agent', 'tool_decision')
		workflow.add_conditional_edges(
			'tool_decision',
			self._route_after_tool_decision,
			{'use_tools': 'tools', 'no_tools': END},
		)
		workflow.add_edge('tools', 'agent')

		# Compile with memory
		checkpointer = MemorySaver()
		return workflow.compile(checkpointer=checkpointer)

	async def _tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Tools node with runtime authorization token update"""
		# Update QuestionComposer tool with authorization token if available
		auth_token = config.get('configurable', {}).get('authorization_token')
		if auth_token:
			for tool in self._tools:
				if hasattr(tool, 'set_authorization_token'):
					tool.set_authorization_token(auth_token)
		
		# Execute tools
		tool_node = ToolNode(self._tools)
		return await tool_node.ainvoke(state, config or {})

	async def _agent_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Main Agent Node with RAG context - generates response without deciding on tools"""
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		# Get RAG context if available
		if not state.get('combined_rag_context'):
			state = await self._get_rag_context(state, thread_id)

		# Build system prompt
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.config and self.config.persona_enabled:
			persona_prompt = self.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt

		# Add RAG context if available
		combined_context = state.get('combined_rag_context')
		if combined_context:
			system_prompt += f'\n\nCONTEXT:\n{combined_context[:1000]}\n'

		# Prepare messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=system_prompt)]}

		# Check if this is a tool response cycle
		tool_decision = state.get('tool_decision', {})
		if tool_decision.get('decision') == 'use_tools':
			# If we decided to use tools, bind tools to the model
			tool_definitions = get_tool_definitions(self.config)
			model_with_tools = self.llm.bind_tools(tool_definitions)

			# Add instruction to use tools
			enhanced_system_prompt = system_prompt + '\n\nBạn có thể sử dụng các công cụ có sẵn để trả lời câu hỏi tốt hơn. Hãy sử dụng chúng khi cần thiết.'
			enhanced_messages = [SystemMessage(content=enhanced_system_prompt)] + messages
			response = await model_with_tools.ainvoke(enhanced_messages)
		else:
			# Normal response without tools
			enhanced_messages = [SystemMessage(content=system_prompt)] + messages
			response = await self.llm.ainvoke(enhanced_messages)

		return {**state, 'messages': messages + [response]}

	async def _tool_decision_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Tool Decision Node - Decides whether to use tools based on user query"""
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

		# Get available tools list
		available_tools = get_tools(self.config)
		tool_names = [tool.name for tool in available_tools]

		# Create decision prompt
		decision_prompt = f"""
Yêu cầu của người dùng: "{user_message}"

Các công cụ có sẵn: {', '.join(tool_names)}

Context hiện tại: {state.get('combined_rag_context', 'Không có context')[:200]}...

Hãy quyết định có cần sử dụng tools hay không để trả lời yêu cầu này.
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

			logger.info(f'Tool Decision: {tool_decision.get("decision")} - {tool_decision.get("reasoning")}')

			return {**state, 'tool_decision': tool_decision}

		except Exception as e:
			logger.error(f'Tool decision failed: {str(e)}')
			# Default to no tools on error
			return {
				**state,
				'tool_decision': {
					'decision': 'no_tools',
					'reasoning': f'Decision failed: {str(e)}',
					'confidence': 0.5,
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
					'workflow_type': 'simplified_with_tool_decision',
					'rag_used': bool(final_state.get('combined_rag_context')),
					'tool_decision': final_state.get('tool_decision', {}),
					'tools_used': self._count_tool_usage(final_state),
				},
			}
		except Exception as e:
			return {
				'response': f'Xin lỗi, có lỗi xảy ra: {str(e)}',
				'state': {},
				'metadata': {
					'error': str(e),
					'workflow_type': 'simplified_with_tool_decision',
				},
			}

	def _extract_response(self, final_state: Dict[str, Any]) -> str:
		"""Extract response from final state"""
		messages = final_state.get('messages', [])
		if messages:
			last_message = messages[-1]
			return last_message.content if hasattr(last_message, 'content') else str(last_message)
		return 'Không có phản hồi được tạo.'

	def _count_tool_usage(self, final_state: Dict[str, Any]) -> Dict[str, Any]:
		"""Count tool usage in the workflow"""
		messages = final_state.get('messages', [])
		tool_calls_count = 0
		tools_used = []

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
	"""Factory function to create simplified workflow"""
	return Workflow(db_session, config)
