"""
State definition cho Chat Workflow
Production-ready state management với comprehensive typing
"""

from typing import Dict, List, Optional, Annotated, TypedDict, Any, Union
from datetime import datetime
from langchain_core.messages import (
	BaseMessage,
	HumanMessage,
	AIMessage,
	SystemMessage,
	ToolMessage,
)
from langchain_core.documents import Document
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
	"""
	Production-ready state definition cho LangGraph workflow

	Comprehensive state management với:
	- Message handling
	- RAG context tracking
	- Error handling
	- Performance monitoring
	- Conversation metadata
	"""

	# Core conversation state
	messages: Annotated[List[BaseMessage], add_messages]

	# RAG pipeline state
	rag_context: Optional[List[str]]
	queries: Optional[List[str]]
	retrieved_docs: Optional[List[Document]]
	need_rag: Optional[bool]

	# RAG system state (simplified from dual_rag)
	global_rag_context: Optional[List[Dict[str, Any]]]
	conversation_rag_context: Optional[List[Dict[str, Any]]]
	rag_routing: Optional[Dict[str, Any]]  # routing decision and metadata
	combined_rag_context: Optional[str]  # final combined context

	# Router decision state
	router_decision: Optional[Dict[str, str]]  # {target: str, explanation: str}
	routing_complete: Optional[bool]

	# Decision tracking
	rag_decision_factors: Optional[Dict[str, Any]]
	query_optimization_metadata: Optional[Dict[str, Any]]
	retrieval_metadata: Optional[Dict[str, Any]]

	# Conversation context
	conversation_metadata: Optional[Dict[str, Any]]
	user_profile: Optional[Dict[str, Any]]
	session_context: Optional[Dict[str, Any]]

	# Error handling
	error_context: Optional[Dict[str, Any]]
	retry_count: Optional[int]
	fallback_used: Optional[bool]

	# Performance tracking
	processing_time: Optional[Dict[str, float]]
	model_usage: Optional[Dict[str, Any]]

	# Tool execution state
	pending_tool_calls: Optional[List[Dict[str, Any]]]
	tool_results: Optional[List[Dict[str, Any]]]

	# Workflow control
	current_node: Optional[str]
	next_action: Optional[str]
	workflow_metadata: Optional[Dict[str, Any]]


class StateManager:
	"""Helper class để manage state transitions và validation"""

	@staticmethod
	def create_initial_state(
		user_message: str,
		user_id: Optional[str] = None,
		session_id: Optional[str] = None,
	) -> AgentState:
		"""Create initial state từ user message"""

		initial_message = HumanMessage(content=user_message)

		return AgentState(
			messages=[initial_message],
			rag_context=None,
			queries=None,
			retrieved_docs=None,
			need_rag=None,
			router_decision=None,
			routing_complete=False,
			rag_decision_factors=None,
			query_optimization_metadata=None,
			retrieval_metadata=None,
			conversation_metadata={
				'user_id': user_id,
				'session_id': session_id,
				'started_at': datetime.now().isoformat(),
				'message_count': 1,
				'topic_classification': None,
			},
			user_profile=None,
			session_context=None,
			error_context=None,
			retry_count=0,
			fallback_used=False,
			processing_time={},
			model_usage={},
			pending_tool_calls=None,
			tool_results=None,
			current_node=None,
			next_action=None,
			workflow_metadata={
				'workflow_version': '1.0.0',
				'created_at': datetime.now().isoformat(),
			},
		)

	@staticmethod
	def update_conversation_metadata(state: AgentState, **updates) -> AgentState:
		"""Update conversation metadata"""
		current_metadata = state.get('conversation_metadata', {})
		current_metadata.update(updates)

		# Update message count
		current_metadata['message_count'] = len(state.get('messages', []))
		current_metadata['last_updated'] = datetime.now().isoformat()

		return {**state, 'conversation_metadata': current_metadata}

	@staticmethod
	def add_error_context(
		state: AgentState,
		error_type: str,
		error_message: str,
		node_name: Optional[str] = None,
	) -> AgentState:
		"""Add error context to state"""
		error_context = state.get('error_context', {})

		if 'errors' not in error_context:
			error_context['errors'] = []

		error_context['errors'].append({
			'type': error_type,
			'message': error_message,
			'node': node_name,
			'timestamp': datetime.now().isoformat(),
			'retry_count': state.get('retry_count', 0),
		})

		error_context['last_error'] = {
			'type': error_type,
			'message': error_message,
			'timestamp': datetime.now().isoformat(),
		}

		return {**state, 'error_context': error_context}

	@staticmethod
	def add_processing_time(state: AgentState, node_name: str, duration: float) -> AgentState:
		"""Add processing time tracking"""
		processing_time = state.get('processing_time', {})
		processing_time[node_name] = duration

		# Calculate total time
		processing_time['total'] = sum(processing_time.values())

		return {**state, 'processing_time': processing_time}

	@staticmethod
	def update_model_usage(
		state: AgentState,
		tokens_used: int,
		model_name: str,
		cost: Optional[float] = None,
	) -> AgentState:
		"""Update model usage tracking"""
		model_usage = state.get('model_usage', {})

		if 'calls' not in model_usage:
			model_usage['calls'] = []

		model_usage['calls'].append({
			'model': model_name,
			'tokens': tokens_used,
			'cost': cost,
			'timestamp': datetime.now().isoformat(),
		})

		# Update totals
		model_usage['total_tokens'] = sum(call['tokens'] for call in model_usage['calls'])
		if cost:
			model_usage['total_cost'] = sum(call.get('cost', 0) for call in model_usage['calls'] if call.get('cost'))

		return {**state, 'model_usage': model_usage}

	@staticmethod
	def extract_last_user_message(state: AgentState) -> Optional[str]:
		"""Extract content từ last user message"""
		messages = state.get('messages', [])

		for message in reversed(messages):
			if isinstance(message, HumanMessage):
				return message.content

		return None

	@staticmethod
	def extract_conversation_history(state: AgentState, limit: Optional[int] = None) -> List[Dict[str, str]]:
		"""Extract conversation history trong format đơn giản"""
		messages = state.get('messages', [])

		history = []
		for message in messages:
			if isinstance(message, (HumanMessage, AIMessage)):
				role = 'user' if isinstance(message, HumanMessage) else 'assistant'
				history.append({
					'role': role,
					'content': message.content,
					'timestamp': getattr(message, 'timestamp', None),
				})

		if limit:
			history = history[-limit:]

		return history

	@staticmethod
	def get_state_summary(state: AgentState) -> Dict[str, Any]:
		"""Get summary of current state"""
		messages = state.get('messages', [])
		error_context = state.get('error_context', {})
		processing_time = state.get('processing_time', {})

		return {
			'message_count': len(messages),
			'has_rag_context': bool(state.get('rag_context')),
			'rag_docs_count': len(state.get('retrieved_docs', [])),
			'router_decision': state.get('router_decision'),
			'routing_complete': state.get('routing_complete', False),
			'has_errors': bool(error_context.get('errors')),
			'error_count': len(error_context.get('errors', [])),
			'total_processing_time': processing_time.get('total', 0),
			'retry_count': state.get('retry_count', 0),
			'fallback_used': state.get('fallback_used', False),
			'current_node': state.get('current_node'),
			'next_action': state.get('next_action'),
		}

	@staticmethod
	def validate_state(state: AgentState) -> bool:
		"""Validate state structure và required fields"""
		try:
			# Check required fields
			if 'messages' not in state:
				return False

			# Validate messages
			messages = state['messages']
			if not isinstance(messages, list):
				return False

			# Check message types
			for message in messages:
				if not isinstance(message, BaseMessage):
					return False

			# Validate optional fields structure
			if state.get('retrieved_docs'):
				for doc in state['retrieved_docs']:
					if not isinstance(doc, Document):
						return False

			return True

		except Exception:
			return False


class StateTransitions:
	"""Define valid state transitions cho workflow"""

	VALID_TRANSITIONS = {
		'start': ['rag_decision'],
		'rag_decision': ['generate_query', 'agent'],
		'generate_query': ['retrieve'],
		'retrieve': ['agent'],
		'agent': ['tools', 'end'],
		'tools': ['agent'],
		'end': [],
	}

	@staticmethod
	def is_valid_transition(from_node: str, to_node: str) -> bool:
		"""Check if transition is valid"""
		return to_node in StateTransitions.VALID_TRANSITIONS.get(from_node, [])

	@staticmethod
	def get_next_valid_nodes(current_node: str) -> List[str]:
		"""Get list of valid next nodes"""
		return StateTransitions.VALID_TRANSITIONS.get(current_node, [])
