"""
Simplified State definition for Chat Workflow
Streamlined state management with essential fields only
"""

from typing import Dict, List, Optional, Annotated, TypedDict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
	"""
	Simplified state definition for LangGraph workflow
	
	Essential state management with core fields only
	"""

	# Core conversation state
	messages: Annotated[List[BaseMessage], add_messages]

	# Basic metadata
	conversation_id: Optional[str]
	user_id: Optional[str]
	
	# Simple workflow control
	current_node: Optional[str]
	
	# Tool execution state
	tool_results: Optional[List[Dict[str, Any]]]
	
	# RAG context
	combined_rag_context: Optional[str]
	rag_used: Optional[bool]
	
	# Business process state
	business_process_type: Optional[str]
	business_process_definition: Optional[str]
	triggered_rules: Optional[List[str]]
	required_tools: Optional[List[str]]
	
	# Tool decision state
	tool_decision: Optional[Dict[str, Any]]
	
	# Guardrails state
	input_validation: Optional[Dict[str, Any]]
	output_validation: Optional[Dict[str, Any]]
	validation_passed: Optional[bool]
	response_safe: Optional[bool]
	
	# Retry management
	retry_count: Optional[int]


class StateManager:
	"""Simplified helper class for state management"""

	@staticmethod
	def create_initial_state(
		user_message: str,
		conversation_id: Optional[str] = None,
		user_id: Optional[str] = None,
	) -> AgentState:
		"""Create initial state from user message"""
		
		initial_message = HumanMessage(content=user_message)

		return AgentState(
			messages=[initial_message],
			conversation_id=conversation_id,
			user_id=user_id,
			current_node=None,
			tool_results=None,
		)

	@staticmethod
	def extract_last_user_message(state: AgentState) -> Optional[str]:
		"""Extract content from last user message"""
		messages = state.get('messages', [])

		for message in reversed(messages):
			if isinstance(message, HumanMessage):
				return message.content

		return None

	@staticmethod
	def get_state_summary(state: AgentState) -> Dict[str, Any]:
		"""Get summary of current state"""
		messages = state.get('messages', [])

		return {
			'message_count': len(messages),
			'conversation_id': state.get('conversation_id'),
			'user_id': state.get('user_id'),
			'current_node': state.get('current_node'),
			'has_tool_results': bool(state.get('tool_results')),
		}
