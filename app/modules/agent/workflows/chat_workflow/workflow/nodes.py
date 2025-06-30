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
	TOOL_DECISION_SYSTEM_PROMPT,
	ToolDecision,
	has_survey_keywords as check_survey_keywords,
	get_matched_keywords,
	build_enhanced_system_prompt,
	build_tool_decision_prompt,
	SURVEY_KEYWORDS,
	SURVEY_SAFETY_KEYWORDS,
	SURVEY_FALLBACK_KEYWORDS,
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
		logger.info('[business_process_analysis_node] 🔍 Starting business process analysis')

		# Get user message
		user_message = StateManager.extract_last_user_message(state)
		if not user_message:
			logger.warning('[business_process_analysis_node] ⚠️ No user message found')
			return state

		logger.info(f'[business_process_analysis_node] 💬 Analyzing user message: "{user_message[:100]}..."')

		try:
			# ENHANCED: Pre-check for survey keywords to force survey_generation process
			survey_keywords_detected = check_survey_keywords(user_message, SURVEY_KEYWORDS)

			logger.info(f'[business_process_analysis_node] 🔍 Survey keywords check: {survey_keywords_detected}')
			if survey_keywords_detected:
				matched_keywords = get_matched_keywords(user_message, SURVEY_KEYWORDS)
				logger.info(f'[business_process_analysis_node] 🎯 Matched survey keywords: {matched_keywords}')

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

			logger.info(f'[business_process_analysis_node] 📋 Identified process type: {process_type.value}')

			# OVERRIDE: Force survey_generation if keywords detected
			if survey_keywords_detected and process_type.value != 'survey_generation':
				logger.info(f'[business_process_analysis_node] 🚀 FORCE OVERRIDE: Changing process type from {process_type.value} to survey_generation')
				from app.modules.agent.workflows.chat_workflow.config.business_process import (
					BusinessProcessType,
				)

				process_type = BusinessProcessType.SURVEY_GENERATION

			# Get process definition
			process_def = self.workflow.business_process_manager.get_process_definition(process_type)
			logger.info(f'[business_process_analysis_node] 📖 Process definition: {process_def.name if process_def else "None"}')

			# Evaluate business rules
			triggered_rules = self.workflow.business_process_manager.evaluate_rules(
				process_type,
				{
					'user_input': user_message,
					'has_cv_context': bool(state.get('cv_context')),
					'has_valid_auth_token': bool(config.get('configurable', {}).get('authorization_token')),
					'profile_completeness': 1.0,  # Default complete
					'context_completeness': 1.0,  # Default complete
				},
			)

			logger.info(f'[business_process_analysis_node] ⚡ Triggered {len(triggered_rules)} business rules')
			logger.info(f'[business_process_analysis_node] ⚡ Rule names: {[rule.name for rule in triggered_rules]}')
			logger.info(f'[business_process_analysis_node] 🛠️ Required tools: {process_def.required_tools if process_def else []}')

			# Store business process information
			return {
				**state,
				'business_process_type': process_type.value,
				'business_process_definition': (process_def.name if process_def else None),
				'triggered_rules': [rule.name for rule in triggered_rules],
				'required_tools': process_def.required_tools if process_def else [],
			}

		except Exception as e:
			logger.error(f'[business_process_analysis_node] ❌ Analysis failed: {str(e)}')

			# FALLBACK: Check for survey keywords even in error case
			survey_keywords_detected = check_survey_keywords(user_message, SURVEY_FALLBACK_KEYWORDS)

			if survey_keywords_detected:
				logger.info(f'[business_process_analysis_node] 🚀 FALLBACK: Survey keywords detected, using survey_generation process')
				from app.modules.agent.workflows.chat_workflow.config.business_process import (
					BusinessProcessType,
				)

				return {
					**state,
					'business_process_type': BusinessProcessType.SURVEY_GENERATION.value,
					'business_process_error': str(e),
					'required_tools': ['generate_survey_questions'],
					'fallback_survey_detection': True,
				}
			else:
				logger.info(f'[business_process_analysis_node] 🔄 FALLBACK: Using general conversation')
				from app.modules.agent.workflows.chat_workflow.config.business_process import (
					BusinessProcessType,
				)

				return {
					**state,
					'business_process_type': BusinessProcessType.GENERAL_CONVERSATION.value,
					'business_process_error': str(e),
				}

	async def tool_decision_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
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
		available_tools = get_tools(self.workflow.config)
		tool_names = [tool.name for tool in available_tools]
		business_process_type = state.get('business_process_type', 'general_conversation')
		required_tools = state.get('required_tools', [])
		triggered_rules = state.get('triggered_rules', [])

		# Create enhanced decision prompt with business context
		decision_prompt = build_tool_decision_prompt(
			user_message=user_message,
			business_process_type=business_process_type,
			required_tools=required_tools,
			triggered_rules=triggered_rules,
			tool_names=tool_names,
			context=state.get('combined_rag_context', ''),
		)

		print(f'[tool_decision_node] User message: {user_message[:100]}...')
		print(f'[tool_decision_node] Available tools: {tool_names}')
		print(f'[tool_decision_node] Business process: {business_process_type}')
		print(f'[tool_decision_node] Required tools: {required_tools}')

		# ENHANCED FORCE FOR TESTING: Force question_composer_tool on certain keywords
		logger.info(f'[tool_decision_node] 🔍 Checking for force keywords in message: "{user_message}"')
		logger.info(f'[tool_decision_node] 🎯 Test keywords: {SURVEY_KEYWORDS}')

		should_force_survey = check_survey_keywords(user_message, SURVEY_KEYWORDS)
		matched_keywords = get_matched_keywords(user_message, SURVEY_KEYWORDS)

		logger.info(f'[tool_decision_node] 🚀 Should force survey: {should_force_survey}')
		logger.info(f'[tool_decision_node] ✅ Matched keywords: {matched_keywords}')

		if should_force_survey:
			logger.info(f'[tool_decision_node] 🎯 FORCE TEST: Detected survey keywords, forcing question_composer_tool')
			logger.info(f'[tool_decision_node] 🎯 Matched keywords: {matched_keywords}')
			return {
				**state,
				'tool_decision': {
					'decision': 'use_tools',
					'reasoning': f'FORCE TEST: Survey keywords detected: {matched_keywords}, using question_composer_tool for testing',
					'confidence': 1.0,
					'tools_needed': ['generate_survey_questions'],
					'force_test': True,
					'matched_keywords': matched_keywords,
				},
			}

		# Get tool decision
		try:
			decision_messages = [
				SystemMessage(content=TOOL_DECISION_SYSTEM_PROMPT),
				HumanMessage(content=decision_prompt),
			]

			decision_response = await self.workflow.tool_decision_llm.ainvoke(decision_messages)

			# Convert to dict if it's a Pydantic model
			if hasattr(decision_response, 'model_dump'):
				tool_decision = decision_response.model_dump()
			else:
				tool_decision = decision_response

			# Override decision if business process requires tools
			logger.info(f'[tool_decision_node] 📋 Required tools from business process: {required_tools}')
			logger.info(f'[tool_decision_node] 🤖 LLM Tool decision: {tool_decision.get("decision")}')
			logger.info(f'[tool_decision_node] 💭 LLM Reasoning: {tool_decision.get("reasoning")}')

			if required_tools and tool_decision.get('decision') == 'no_tools':
				logger.info(f'[tool_decision_node] 🔄 Overriding decision due to business process requirements: {required_tools}')
				tool_decision.update({
					'decision': 'use_tools',
					'reasoning': f'Business process {business_process_type} requires tools: {", ".join(required_tools)}',
					'business_override': True,
				})

			# ADDITIONAL FORCE: If business process is survey_generation, force tools regardless
			if business_process_type == 'survey_generation' and tool_decision.get('decision') == 'no_tools':
				logger.info(f'[tool_decision_node] 🚀 BUSINESS PROCESS FORCE: survey_generation detected, forcing tools')
				tool_decision.update({
					'decision': 'use_tools',
					'reasoning': f'Business process {business_process_type} requires survey tools',
					'confidence': 1.0,
					'tools_needed': ['generate_survey_questions'],
					'business_override': True,
					'force_test': True,
				})

			# ADDITIONAL SAFETY: Check if any survey keywords in user message and force if needed
			has_survey_keyword = check_survey_keywords(user_message, SURVEY_SAFETY_KEYWORDS)

			if has_survey_keyword and tool_decision.get('decision') == 'no_tools':
				found_keywords = get_matched_keywords(user_message, SURVEY_SAFETY_KEYWORDS)
				logger.warning(f'[tool_decision_node] 🚨 SAFETY OVERRIDE: Survey keywords detected but LLM said no_tools, forcing use_tools')
				logger.warning(f'[tool_decision_node] 🚨 Found keywords: {found_keywords}')
				tool_decision.update({
					'decision': 'use_tools',
					'reasoning': f'Safety override: Survey keywords detected in user message',
					'confidence': 1.0,
					'tools_needed': ['generate_survey_questions'],
					'safety_override': True,
				})

			logger.info(f'[tool_decision_node] 🎯 FINAL Tool Decision: {tool_decision.get("decision")} - {tool_decision.get("reasoning")}')
			logger.info(f'[tool_decision_node] 🛠️ Tools needed: {tool_decision.get("tools_needed", [])}')

			return {**state, 'tool_decision': tool_decision}

		except Exception as e:
			logger.error(f'[tool_decision_node] ❌ Tool decision failed: {str(e)}')
			logger.error(f'[tool_decision_node] ❌ Falling back to business process default')

			# Default based on business process requirements or keyword detection
			has_survey_keyword = check_survey_keywords(user_message, SURVEY_FALLBACK_KEYWORDS)

			if required_tools or has_survey_keyword:
				default_decision = 'use_tools'
				default_tools = ['generate_survey_questions'] if has_survey_keyword else required_tools
				reasoning = f'Fallback decision due to error: {str(e)}. Detected survey keywords or business requirements.'
			else:
				default_decision = 'no_tools'
				default_tools = []
				reasoning = f'Fallback decision due to error: {str(e)}. No clear tool requirements detected.'

			logger.info(f'[tool_decision_node] 🔄 FALLBACK Decision: {default_decision}')
			logger.info(f'[tool_decision_node] 🔄 FALLBACK Tools: {default_tools}')

			return {
				**state,
				'tool_decision': {
					'decision': default_decision,
					'reasoning': reasoning,
					'confidence': 0.5,
					'tools_needed': default_tools,
					'fallback': True,
				},
			}

	async def agent_with_tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Agent Node WITH Tools - direct tool usage, NO RAG"""
		logger.info('[agent_with_tools_node] � Starting agent WITH tools (NO RAG)')

		# ===== APPROACH =====
		# Skip all RAG, business process analysis, complex tool decision
		# Go directly to agent with tools for survey generation

		# Simple system prompt focused on survey generation
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.workflow.config and self.workflow.config.persona_enabled:
			persona_prompt = self.workflow.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt
				logger.info(f'[agent_with_tools_node] 🎭 Using persona prompt')

		# Add simple survey focus instruction
		system_prompt += '\n\n🎯 FOCUS: Use generate_survey_questions tool when users ask about surveys, questions, or assessments.'
		system_prompt += '\n\n⚡ DIRECT MODE: No RAG retrieval, direct tool usage for efficient responses.'

		# Get messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=system_prompt)]}

		# Get ALL available tools (no filtering, no complex logic)
		all_tools = get_tool_definitions(self.workflow.config)

		logger.info(f'[agent_with_tools_node] � Available tools: {[getattr(tool, "name", "unknown") for tool in all_tools]}')

		# Bind tools to model
		try:
			model_with_tools = self.workflow.llm.bind_tools(all_tools)
			logger.info(f'[agent_with_tools_node] ✅ Successfully bound {len(all_tools)} tools to LLM')
		except Exception as e:
			logger.error(f'[agent_with_tools_node] ❌ ERROR binding tools: {str(e)}')
			raise

		# Prepare messages for LLM
		enhanced_messages = [SystemMessage(content=system_prompt)] + messages

		logger.info(f'[agent_with_tools_node] � Calling LLM with {len(enhanced_messages)} messages and {len(all_tools)} tools')

		try:
			response = await model_with_tools.ainvoke(enhanced_messages)
			logger.info('[agent_with_tools_node] ✅ LLM response received')
		except Exception as e:
			logger.error(f'[agent_with_tools_node] ❌ LLM call failed: {str(e)}')
			raise

		# Return updated state
		return {**state, 'messages': messages + [response]}

	async def agent_no_tools_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Agent Node WITHOUT Tools - for regular conversation"""
		print('[agent_no_tools_node] Starting agent WITHOUT tools')
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		# Get RAG context if available
		if not state.get('combined_rag_context'):
			state = await self.workflow._get_rag_context(state, thread_id)

		# Build system prompt with persona
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.workflow.config and self.workflow.config.persona_enabled:
			persona_prompt = self.workflow.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt
				print(f'[agent_no_tools_node] Using persona prompt: {self.workflow.config.persona_type.value}')

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

		# No tools needed - just get a regular response
		print(f'[agent_no_tools_node] No tools needed, getting regular response')
		print(f'[agent_no_tools_node] System prompt length: {len(system_prompt)}')

		enhanced_messages = [SystemMessage(content=system_prompt)] + messages

		try:
			response = await self.workflow.llm.ainvoke(enhanced_messages)
			print(f'[agent_no_tools_node] Regular LLM response received: {type(response)}')
			print(f'[agent_no_tools_node] Response content: {getattr(response, "content", "No content")[:200]}...')
		except Exception as e:
			print(f'[agent_no_tools_node] ERROR in regular LLM call: {str(e)}')
			raise

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
