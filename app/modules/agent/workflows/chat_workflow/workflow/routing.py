"""
Routing Functions for Chat Workflow

This module contains all routing logic that determines the flow
of the enhanced chat workflow for EnterViu AI Assistant.

Routing Functions:
- Route after tool decision
- Route after agent execution
- Route after output validation
"""

import logging
from typing import Dict, Any

from ..state.workflow_state import AgentState

logger = logging.getLogger(__name__)


class WorkflowRouter:
	"""Container for all workflow routing functions"""

	def __init__(self, workflow_instance):
		"""Initialize with reference to main workflow instance"""
		self.workflow = workflow_instance

	def route_after_tool_decision(self, state: AgentState) -> str:
		"""Route based on tool decision"""
		tool_decision = state.get('tool_decision', {})
		decision = tool_decision.get('decision', 'no_tools')
		tools_needed = tool_decision.get('tools_needed', [])
		reasoning = tool_decision.get('reasoning', 'No reasoning provided')

		logger.info(f'[route_after_tool_decision] 🧭 Routing decision: {decision}')
		logger.info(f'[route_after_tool_decision] 🛠️ Tools needed: {tools_needed}')
		logger.info(f'[route_after_tool_decision] 💭 Reasoning: {reasoning}')

		if decision == 'use_tools':
			logger.info(f'[route_after_tool_decision] ✅ Routing to: use_tools (agent_with_tools)')
			return 'use_tools'
		else:
			logger.info(f'[route_after_tool_decision] ❌ Routing to: no_tools (agent_no_tools)')
			return 'no_tools'

	def should_continue_after_agent(self, state: AgentState) -> str:
		"""Determine if agent should continue with tools or end (used after agent_with_tools)"""
		messages = state.get('messages', [])
		if not messages:
			print('[should_continue_after_agent] No messages, ending')
			return 'end'

		last_message = messages[-1]
		print(f'[should_continue_after_agent] Last message type: {type(last_message)}')

		# Check if agent made tool calls
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			print(f'[should_continue_after_agent] Found {len(last_message.tool_calls)} tool calls, proceeding to tools')
			return 'tools'
		else:
			print('[should_continue_after_agent] No tool calls found, ending workflow')
			return 'end'

	def route_after_output_validation(self, state: AgentState) -> str:
		"""Route after output validation - check if we need to continue or end"""
		validation_result = state.get('output_validation', {})

		# If output validation failed critically, we might want to retry
		if not validation_result.get('is_safe', True):
			severity = validation_result.get('overall_severity', 'low')
			if severity in ['high', 'critical']:
				# For high/critical violations, try to regenerate response
				retry_count = state.get('retry_count', 0)
				if retry_count < 2:  # Max 2 retries
					logger.warning(f'[route_after_output_validation] Critical violation detected, retrying (attempt {retry_count + 1})')
					# Increment retry count for next attempt
					state['retry_count'] = retry_count + 1
					return 'continue'
				else:
					print('[route_after_output_validation] Max retries exceeded, ending with safety warning')
					# Add safety message to final response
					messages = state.get('messages', [])
					if messages:
						last_msg = messages[-1]
						if hasattr(last_msg, 'content'):
							last_msg.content += '\n\n⚠️ Lưu ý: Phản hồi này có thể cần được xem xét thêm.'

		# Normal flow - end the conversation
		return 'end'
