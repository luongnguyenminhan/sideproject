"""
Main Workflow Class for Enhanced Chat Workflow

This module contains the main Workflow class and factory functions
for creating the enhanced chat workflow for EnterViu AI Assistant.

Main Components:
- Workflow class (refactored from large workflow.py)
- Factory functions
- Message processing logic
- RAG integration
- Response extraction and metadata
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage

from ..state.workflow_state import AgentState, StateManager
from ..config.workflow_config import WorkflowConfig
from ..config.business_process import get_business_process_manager
from ..config.llm_guardrails import initialize_guardrails_with_llm
from .prompts import ToolDecision
from .workflow_builder import WorkflowBuilder

load_dotenv()
logger = logging.getLogger(__name__)


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

		# Build workflow using WorkflowBuilder
		self.workflow_builder = WorkflowBuilder(self)
		self.compiled_graph = self.workflow_builder.build_workflow()

	def _init_global_kb_service(self):
		"""Initialize Global Knowledge Base Service"""
		try:
			from app.modules.agentic_rag.services.global_kb_service import (
				GlobalKBService,
			)

			self.global_kb_service = GlobalKBService(self.db_session)
		except Exception:
			self.global_kb_service = None

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

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		conversation_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
	) -> Dict[str, Any]:
		"""Process message with workflow"""
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
			final_state = await self.compiled_graph.ainvoke(initial_state, config=runtime_config)

			# Extract response
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
