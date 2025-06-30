"""
Node Functions for Chat Workflow

This module contains all node functions that handle different stages
of the enhanced chat workflow for EnterViu AI Assistant.

Nodes:
- Input validation
- Business process analysis
- Tool decision
- Agent with tools
- Agent without tools
- Tools execution
- Output validation
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.prebuilt import ToolNode

from ..state.workflow_state import AgentState, StateManager
from ..tools.basic_tools import get_tools, get_tool_definitions
from .prompts import (
	DEFAULT_SYSTEM_PROMPT,
	has_survey_keywords as check_survey_keywords,
	get_matched_keywords,
	build_enhanced_system_prompt,
	SURVEY_KEYWORDS,
)

logger = logging.getLogger(__name__)


class WorkflowNodes:
	"""Container for all workflow node functions"""

	def __init__(self, workflow_instance):
		"""Initialize with reference to main workflow instance"""
		self.workflow = workflow_instance

	async def input_validation_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Input Validation Node - Validates user input through LLM guardrails"""
		print('[input_validation_node] Starting input validation')

		# Get user message
		user_message = StateManager.extract_last_user_message(state)
		if not user_message:
			logger.warning('[input_validation_node] No user message found')
			return state

		try:
			# Validate user input through guardrails
			validation_result = await self.workflow.guardrails_manager.validate_user_input(
				user_message,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'timestamp': datetime.now().isoformat(),
				},
			)

			print(f'[input_validation_node] Validation result: {validation_result["is_safe"]} - {validation_result["summary"]}')

			# Store validation results in state
			return {
				**state,
				'input_validation': validation_result,
				'validation_passed': validation_result['is_safe'],
			}

		except Exception as e:
			print(f'[input_validation_node] Validation failed: {str(e)}')
			# Allow processing to continue on validation error
			return {
				**state,
				'input_validation': {'is_safe': True, 'error': str(e)},
				'validation_passed': True,
			}

	async def business_process_analysis_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Business Process Analysis Node - Identifies process type and applicable rules"""
		logger.info('[business_process_analysis_node] Starting business process analysis')

		# Get user message
		user_message = StateManager.extract_last_user_message(state)
		if not user_message:
			logger.warning('[business_process_analysis_node] No user message found')
			return state

		try:
			# Identify business process type
			process_type = self.workflow.business_process_manager.identify_process_type(
				user_message,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'has_cv_context': bool(state.get('cv_context')),
					'has_valid_auth_token': bool(config.get('configurable', {}).get('authorization_token')),
					'user_input': user_message,
				},
			)

			# Get process definition
			process_def = self.workflow.business_process_manager.get_process_definition(process_type)

			# Evaluate business rules
			triggered_rules = self.workflow.business_process_manager.evaluate_rules(
				process_type,
				{
					'user_input': user_message,
					'has_cv_context': bool(state.get('cv_context')),
					'has_valid_auth_token': bool(config.get('configurable', {}).get('authorization_token')),
					'profile_completeness': 1.0,
					'context_completeness': 1.0,
				},
			)

			return {
				**state,
				'business_process_type': process_type.value,
				'business_process_definition': (process_def.name if process_def else None),
				'triggered_rules': [rule.name for rule in triggered_rules],
				'required_tools': process_def.required_tools if process_def else [],
			}

		except Exception as e:
			logger.error(f'[business_process_analysis_node] Analysis failed: {str(e)}')

			# Simple fallback
			from app.modules.agent.workflows.chat_workflow.config.business_process import (
				BusinessProcessType,
			)

			return {
				**state,
				'business_process_type': BusinessProcessType.GENERAL_CONVERSATION.value,
				'business_process_error': str(e),
			}

	

	async def agent_with_tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Agent Node WITH Tools - Uses tools when needed"""
		logger.info('[agent_with_tools_node] Starting agent WITH tools')

		# Get system prompt
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.workflow.config and self.workflow.config.persona_enabled:
			persona_prompt = self.workflow.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt

		# Get messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=system_prompt)]}

		# Get ALL available tools
		all_tools = get_tool_definitions(self.workflow.config)
		logger.info(f'[agent_with_tools_node] Available tools: {[getattr(tool, "name", "unknown") for tool in all_tools]}')

		# Bind tools to model
		try:
			model_with_tools = self.workflow.llm.bind_tools(all_tools)
			logger.info(f'[agent_with_tools_node] Successfully bound {len(all_tools)} tools to LLM')
		except Exception as e:
			logger.error(f'[agent_with_tools_node] ERROR binding tools: {str(e)}')
			raise

		# Prepare messages for LLM
		enhanced_messages = [SystemMessage(content=system_prompt)] + messages

		logger.info(f'[agent_with_tools_node] Calling LLM with {len(enhanced_messages)} messages and {len(all_tools)} tools')

		try:
			response = await model_with_tools.ainvoke(enhanced_messages)
			logger.info('[agent_with_tools_node] LLM response received')

			# Check if response contains tool calls
			if hasattr(response, 'tool_calls') and response.tool_calls:
				logger.info(f'[agent_with_tools_node] {len(response.tool_calls)} tool calls generated!')
				for i, tool_call in enumerate(response.tool_calls):
					logger.info(f'[agent_with_tools_node] Tool {i + 1}: {tool_call.get("name", "unknown")}')
			else:
				logger.info('[agent_with_tools_node] No tool calls in response')

		except Exception as e:
			logger.error(f'[agent_with_tools_node] LLM call failed: {str(e)}')
			raise

		# Return updated state
		return {**state, 'messages': messages + [response]}



	async def tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Tools execution node"""
		print('[tools_node] Executing tools node')

		# Extract conversation context from config
		conversation_id = config.get('configurable', {}).get('conversation_id')
		user_id = config.get('configurable', {}).get('user_id')
		print(f'[tools_node] Conversation ID: {conversation_id}')
		print(f'[tools_node] User ID: {user_id}')

		# Add conversation context to state for tools access
		updated_state = {
			**state,
			'conversation_id': conversation_id,
			'user_id': user_id,
		}

		# Validate tool calls through guardrails before execution
		last_message = state.get('messages', [])[-1] if state.get('messages') else None
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			try:
				for tool_call in last_message.tool_calls:
					tool_validation = await self.workflow.guardrails_manager.validate_tool_usage(
						tool_call.get('name', 'unknown'),
						tool_call.get('args', {}),
						context={
							'user_id': state.get('user_id'),
							'business_process_type': state.get('business_process_type'),
							'conversation_id': state.get('conversation_id'),
						},
					)
					if not tool_validation.get('is_safe', True):
						logger.warning(f'[tools_node] Tool call validation failed: {tool_validation["summary"]}')
						# Continue with execution but log the concern
			except Exception as e:
				print(f'[tools_node] Tool validation failed: {str(e)}')
				# Continue with execution on validation error

		# Update tools with authorization token and conversation context if available
		auth_token = config.get('configurable', {}).get('authorization_token')
		print(f'[tools_node] Authorization token available: {bool(auth_token)}')

		if auth_token:
			print(f'[tools_node] Setting authorization token for tools: {auth_token[:20]}...')

			# Set authorization token for question composer tool using global function
			try:
				from ..tools.question_composer_tool import (
					set_authorization_token,
					set_conversation_context,
				)

				set_authorization_token(auth_token)
				set_conversation_context(conversation_id, user_id)
				print(f'[tools_node] Context set for question composer tool - Conversation: {conversation_id}, User: {user_id}')
			except ImportError as e:
				logger.warning(f'[tools_node] Could not import question composer functions: {e}')

			# For any other tools that support set_authorization_token method
			for tool in self.workflow._tools:
				if hasattr(tool, 'set_authorization_token'):
					print(f'[tools_node] Setting token for tool: {tool.name}')
					tool.set_authorization_token(auth_token)
				else:
					logger.debug(f'[tools_node] Tool {getattr(tool, "name", "unknown")} does not support authorization token')
		else:
			logger.warning('[tools_node] No authorization token provided in config')

		# Execute tools
		tool_node = ToolNode(self.workflow._tools)
		result = await tool_node.ainvoke(updated_state, config or {})

		# Track survey generation in state
		survey_generated = False
		survey_questions_count = 0

		# Check if survey generation tool was called
		last_message = result.get('messages', [])[-1] if result.get('messages') else None
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			for tool_call in last_message.tool_calls:
				if tool_call.get('name') == 'generate_survey_questions':
					survey_generated = True
					print('[tools_node] ✅ Survey generation tool was executed')
					break

		# Add survey tracking to result state
		result_with_survey_tracking = {
			**result,
			'survey_generated': survey_generated,
			'survey_questions_count': survey_questions_count,
		}

		print('[tools_node] Tools execution completed')
		return result_with_survey_tracking

	async def output_validation_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Output Validation Node - Validates AI response through LLM guardrails"""
		print('[output_validation_node] Starting output validation')

		# Get the last AI message
		messages = state.get('messages', [])
		ai_response = None
		for msg in reversed(messages):
			if isinstance(msg, AIMessage):
				ai_response = msg.content
				break

		if not ai_response:
			logger.warning('[output_validation_node] No AI response found')
			return {
				**state,
				'output_validation': {'is_safe': True, 'no_response': True},
			}

		try:
			# Validate AI response through guardrails
			validation_result = await self.workflow.guardrails_manager.validate_ai_response(
				ai_response,
				context={
					'user_id': state.get('user_id'),
					'conversation_id': state.get('conversation_id'),
					'business_process_type': state.get('business_process_type'),
					'timestamp': datetime.now().isoformat(),
				},
			)

			print(f'[output_validation_node] Output validation: {validation_result["is_safe"]} - {validation_result["summary"]}')

			# Store validation results
			return {
				**state,
				'output_validation': validation_result,
				'response_safe': validation_result['is_safe'],
			}

		except Exception as e:
			print(f'[output_validation_node] Output validation failed: {str(e)}')
			# Allow response to proceed on validation error
			return {
				**state,
				'output_validation': {'is_safe': True, 'error': str(e)},
				'response_safe': True,
			}
