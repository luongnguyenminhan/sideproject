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
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .state.workflow_state import AgentState, StateManager
from .config.workflow_config import WorkflowConfig
from .tools.basic_tools import get_tools, get_tool_definitions
from .utils.color_logger import get_color_logger
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
Bạn là Enterview AI Assistant - Trợ lý thông minh của Enterview, công cụ AI hỗ trợ người dùng khám phá bản thân và trong việc tìm kiếm việc làm.
   Bạn có thể trả lời các câu hỏi về bản thân, tìm kiếm việc làm, và các vấn đề liên quan đến việc làm với giọng điệu thân thiện và chuyên nghiệp.
   
   SỨ MỆNH CỦA ENTERVIEW:
   - Giúp người dùng tìm hiểu bản thân và khám phá những gì họ thực sự muốn.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   TÍNH NĂNG CHÍNH:
   - Tìm hiểu bản thân và nhu cầu việc làm của người dùng.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu việc làm của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   LƯU Ý:
   - Từ chối trả lời các câu hỏi không liên quan đến việc làm.
   - Trả lời các câu hỏi một cách chuyên nghiệp và thân thiện.
   Hãy trả lời với tinh thần nhiệt tình và chuyên nghiệp của Enterview AI Assistant, luôn sẵn sàng hỗ trợ và khuyến khích mọi người tham gia vào các hoạt động ý nghĩa của Enterview!
"""
ROUTER_SYSTEM_PROMPT = """
🧭 Bạn là Router Agent cho hệ thống Enterview AI Assistant với TOOL PRIORITIZATION.

🎯 ROUTING STRATEGY:
- "agent" - CHO TẤT CẢ câu hỏi (ƯU TIÊN để agent có thể sử dụng tools)
- "rag_query" - CHỈ cho những câu hỏi ĐƠN GIẢN, cần trả lời nhanh

📋 QUY TẮC ROUTING:
⚠️ MẶC ĐỊNH: Chọn "agent" để agent có thể sử dụng tools

🎯 Chọn "agent" KHI:
✅ User hỏi về thông tin (để agent có thể dùng RAG tool)
✅ User đề cập CV, profile, questions (để agent dùng Question Composer)
✅ Bất kỳ câu hỏi nào có thể hưởng lợi từ tools
✅ Câu hỏi phức tạp cần tools hỗ trợ

🎯 Chỉ chọn "rag_query" KHI:
❌ Câu hỏi cực kỳ đơn giản, không cần tools
❌ Trường hợp hiếm hoi cần response nhanh

🚀 MỤC TIÊU: Ưu tiên "agent" để maximize tool usage efficiency!
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

		async def tools_wrapper(state, config=None):
			return await self._tools_node(state, config or {}, tool_node)

		def route_wrapper(state):
			return self._route_decision(state)

		def should_continue_wrapper(state):
			return self._should_continue(state)

		# Add simplified nodes
		workflow.add_node('router', router_wrapper)
		workflow.add_node('rag_query', rag_query_wrapper)
		workflow.add_node('agent', agent_wrapper)
		workflow.add_node('tools', tools_wrapper)
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
			logger.info(
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
			logger.info(
				'RAG Query Node - Dual RAG Retrieval',
				processing_time,
				context_retrieved=bool(combined_context),
				conv_context_found=bool(conv_context),
				global_context_found=bool(global_context),
			)

			return {
				**state,
				'combined_rag_context': combined_context,
				'rag_used': True,
				'retrieval_quality': 'good' if combined_context else 'no_results',
			}

		except Exception as e:
			logger.error(f'Dual RAG Query failed: {str(e)}')
			return {
				**state,
				'combined_rag_context': '',
				'rag_used': False,
				'retrieval_quality': 'error',
			}

	async def _agent_node(self, state: AgentState, config: Dict[str, Any]) -> AgentState:
		"""Main Agent Node - ALWAYS USE TOOLS FIRST, minimize direct responses"""
		start_time = time.time()
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		# Extract user context từ state và config
		user_id = config.get('configurable', {}).get('user_id') or StateManager.get_user_id_from_state(state)

		conversation_id = config.get('configurable', {}).get('conversation_id') or StateManager.get_conversation_id_from_state(state) or thread_id

		logger.workflow_start(
			'Agent Node - TOOL-FIRST Model Invocation',
			thread_id=thread_id,
			user_id=user_id,
			conversation_id=conversation_id,
			has_context=bool(state.get('combined_rag_context')),
		)

		# Get system prompt with persona support
		system_prompt = DEFAULT_SYSTEM_PROMPT
		if self.config and self.config.persona_enabled:
			persona_prompt = self.config.get_persona_prompt()
			if persona_prompt:
				system_prompt = persona_prompt

		# ULTRA-AGGRESSIVE tool prioritization system prompt với user context
		enhanced_system = f"""{system_prompt}

🤖 ENTERVIEW AI ASSISTANT - SESSION: {thread_id}

🧑‍💼 USER CONTEXT:
- User ID: {user_id or 'Unknown'}
- Conversation ID: {conversation_id or 'Unknown'}
- Thread ID: {thread_id}

🔥 CRITICAL TOOL-FIRST PROTOCOL:
⚠️ BẮT BUỘC SỬ DỤNG TOOLS - KHÔNG ĐƯỢC TRẢ LỜI TRỰC TIẾP!

🚫 MANDATORY TOOL USAGE RULES:
1. 🔍 RAG_RETRIEVAL tool - SỬ DỤNG CHO 99% CÂU HỎI:
   ✅ BẮT BUỘC cho mọi câu hỏi thông tin
   ✅ BẮT BUỘC cho câu hỏi về Enterview, công ty, việc làm  
   ✅ BẮT BUỘC cho tìm kiếm kiến thức
   ✅ BẮT BUỘC khi user hỏi về bất cứ điều gì
   ✅ Ngay cả câu hỏi đơn giản cũng dùng RAG để có thông tin đầy đủ

2. ❓ QUESTION_COMPOSER tool - BẮT BUỘC KHI:
   ✅ User đề cập "CV", "profile", "resume", "hồ sơ"
   ✅ User nói về "câu hỏi", "questions", "phỏng vấn"
   ✅ User muốn "analyze", "phân tích" profile
   ✅ User hỏi về career, skills, experience

🚫 CẤM TRẢ LỢI TRỰC TIẾP KHI CÓ THỂ DÙNG TOOLS!

🎯 EXECUTION PRIORITY:
- 1st: Luôn cân nhắc RAG_RETRIEVAL tool
- 2nd: Nếu về CV/profile → Question Composer tool  
- 3rd: CHỈ khi tools hoàn toàn không phù hợp mới trả lời trực tiếp

⚠️ NẾU KHÔNG DÙNG TOOL: PHẢI giải thích tại sao không dùng tool

📊 AVAILABLE CONTEXT: {bool(state.get('combined_rag_context'))}

🔧 TOOL PARAMETERS:
- conversation_id: {conversation_id}
- user_id: {user_id}
- Always include these IDs when calling tools!
"""

		# Add RAG context if available
		combined_context = state.get('combined_rag_context')
		if combined_context:
			enhanced_system += f'\n📚 CURRENT CONTEXT:\n{combined_context[:600]}...\n'

		# Prepare messages
		messages = state.get('messages', [])
		if not messages:
			return {'messages': [SystemMessage(content=enhanced_system)]}

		# ULTRA-AGGRESSIVE tool analysis
		last_user_message = None
		for msg in reversed(messages):
			if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
				last_user_message = msg.content
				break

		# Force tool recommendation for almost everything
		tool_recommendation = ''
		if last_user_message:
			logger.info(f'🎯 [Agent] ANALYZING message for MANDATORY tool usage: "{last_user_message[:100]}..."')

			message_lower = last_user_message.lower()

			# Ultra-broad tool triggers
			rag_triggers = [
				'gì',
				'ai',
				'nào',
				'sao',
				'thế nào',
				'như thế nào',
				'bao nhiêu',
				'ở đâu',
				'khi nào',
				'tại sao',
				'?',
				'là',
				'có',
				'được',
				'làm',
				'enterview',
				'công ty',
				'company',
				'việc làm',
				'job',
				'tuyển dụng',
				'thông tin',
				'info',
				'biết',
				'hiểu',
				'tìm',
				'search',
				'hỏi',
			]

			cv_triggers = [
				'cv',
				'resume',
				'câu hỏi',
				'question',
				'profile',
				'phỏng vấn',
				'interview',
				'analyze',
				'phân tích',
				'hồ sơ',
				'kinh nghiệm',
				'experience',
				'skill',
				'kỹ năng',
				'career',
				'nghề nghiệp',
			]

			has_rag_trigger = any(trigger in message_lower for trigger in rag_triggers)
			has_cv_trigger = any(trigger in message_lower for trigger in cv_triggers)

			if has_cv_trigger:
				tool_recommendation = f"""
🔥 MANDATORY: Bạn PHẢI sử dụng question_composer tool!
📋 Parameters: conversation_id="{conversation_id}", user_id="{user_id}"
"""
				logger.warning(
					'🔥 [Agent] CV/Profile detected - QUESTION_COMPOSER tool MANDATORY!',
					user_id=user_id,
					conversation_id=conversation_id,
				)
			elif has_rag_trigger:
				tool_recommendation = f"""
🔥 MANDATORY: Bạn PHẢI sử dụng rag_retrieval tool!
📋 Parameters: conversation_id="{conversation_id}", user_id="{user_id}", query="{last_user_message[:100]}"
"""
				logger.warning(
					'🔥 [Agent] Information query detected - RAG_RETRIEVAL tool MANDATORY!',
					user_id=user_id,
					conversation_id=conversation_id,
				)
			else:
				# Even for edge cases, try to use RAG
				tool_recommendation = f"""
💡 STRONG RECOMMENDATION: Hãy cân nhắc sử dụng rag_retrieval tool để cung cấp thông tin đầy đủ hơn!
📋 Parameters: conversation_id="{conversation_id}", user_id="{user_id}"
"""
				logger.info(
					'💡 [Agent] No clear triggers - but still recommend RAG tool',
					user_id=user_id,
					conversation_id=conversation_id,
				)

			logger.info(f'📊 [Agent] Tool analysis:')
			logger.info(f'   - RAG triggers found: {has_rag_trigger}')
			logger.info(f'   - CV triggers found: {has_cv_trigger}')
			logger.info(f'   - User ID: {user_id}')
			logger.info(f'   - Conversation ID: {conversation_id}')
			logger.info(f'   - Tool recommendation: {tool_recommendation.strip()}')

		# Create ULTRA-AGGRESSIVE tool prompt
		final_system_prompt = (
			enhanced_system
			+ tool_recommendation
			+ """

🎯 REMINDER: Your primary job is to USE TOOLS, not give direct answers!
Think: "What tool can help me answer this better?" before responding directly.
"""
		)

		# Create prompt with EXTREME tool encouragement
		prompt = ChatPromptTemplate.from_messages([
			('system', final_system_prompt),
			MessagesPlaceholder(variable_name='chat_history'),
			MessagesPlaceholder(variable_name='agent_scratchpad'),
		])

		formatted_prompt = prompt.format_messages(
			chat_history=messages,
			agent_scratchpad=[],
		)

		# Get tools and bind to model with ENHANCED tool binding
		tools = get_tools(self.config)
		if not tools:
			logger.error('🚨 [Agent] NO TOOLS AVAILABLE - This is a major issue!')

		# Bind tools with extra parameters to encourage usage
		model_with_tools = self.llm.bind_tools(
			tools,
			tool_choice='auto',  # Let model decide but encourage usage
		)

		logger.warning(f'🛠️ [Agent] {len(tools)} tools bound to model - EXPECTING TOOL USAGE!')

		# Invoke model with MAXIMUM tool encouragement
		response = await model_with_tools.ainvoke(
			formatted_prompt,
			{
				'system_time': datetime.now(tz=timezone.utc).isoformat(),
				'unified_mode': True,
				'conversation_id': conversation_id,
				'tool_priority': 'MAXIMUM',  # Maximum tool priority signal
				'force_tools': True,  # Force tool consideration
				'user_id': user_id,
			},
		)
		print(f'🔍 [Agent] Model response: {response}...')
		# Add user context to tool calls if any
		if hasattr(response, 'tool_calls') and response.tool_calls:
			logger.info(f'🔧 [Agent] Processing {len(response.tool_calls)} tool calls')
			for i, tool_call in enumerate(response.tool_calls):
				# Ensure user_id and conversation_id are in tool arguments
				if 'args' in tool_call:
					if 'user_id' not in tool_call['args'] and user_id:
						tool_call['args']['user_id'] = user_id
						logger.info(f'   - Tool {i + 1}: Added user_id={user_id}')
					if 'conversation_id' not in tool_call['args'] and conversation_id:
						tool_call['args']['conversation_id'] = conversation_id
						logger.info(f'   - Tool {i + 1}: Added conversation_id={conversation_id}')

					logger.info(f'   - Tool {i + 1}: {tool_call.get("name", "unknown")} with context')

		processing_time = time.time() - start_time
		logger.info(
			'Agent Node - TOOL-FIRST Model Invocation',
			processing_time,
			response_length=(len(str(response.content)) if hasattr(response, 'content') else 0),
			tools_called=(len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0),
			tool_usage_success=bool(hasattr(response, 'tool_calls') and response.tool_calls),
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
			routing_info = state.get('rag_routing', {})
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

	async def _tools_node(self, state: AgentState, config: Dict[str, Any], tool_node) -> AgentState:
		"""Simplified Tools Node"""
		thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

		logger.info(f'🔧 [Tools] Starting tool execution for thread: {thread_id}')

		# Track tool iterations to prevent infinite loops
		tool_iterations = state.get('tool_iterations', 0) + 1
		logger.info(f'🔄 [Tools] Tool iteration: {tool_iterations}')

		# Get messages and check for tool calls
		messages = state.get('messages', [])
		if not messages:
			logger.warning('🔧 [Tools] No messages found')
			return {**state, 'tool_iterations': tool_iterations}

		last_message = messages[-1]
		if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
			logger.warning('🔧 [Tools] No tool calls found')
			return {**state, 'tool_iterations': tool_iterations}

		# Log tool calls
		for i, tool_call in enumerate(last_message.tool_calls, 1):
			tool_name = tool_call.get('name', 'unknown_tool')
			logger.info(f'🔧 [Tools] Executing Tool #{i}: {tool_name}')

		try:
			# Execute tools using the tool node
			result_state = await tool_node.ainvoke(state, config)

			logger.info(f'🔧 [Tools] All tools executed successfully')
			return {**result_state, 'tool_iterations': tool_iterations}

		except Exception as e:
			logger.error(f'🔧 [Tools] Tool execution failed: {str(e)}')
			# Return state with error info
			return {
				**state,
				'tool_execution_error': str(e),
				'tool_execution_failed': True,
				'tool_iterations': tool_iterations,
			}

	def _route_decision(self, state: AgentState) -> str:
		"""Simplified route decision logic"""
		router_decision = state.get('router_decision', {})
		target = router_decision.get('target', 'agent') if isinstance(router_decision, dict) else 'agent'

		# Simple mapping
		if target == 'rag_query':
			actual_target = 'rag_query'
		else:
			actual_target = 'agent'
		logger.info(f'🔀 Routing Decision: {target} → {actual_target}')
		logger.info(f'📝 Routing Explanation: {router_decision.get("explanation", "No explanation provided")}')

		return actual_target

	def _should_continue(self, state: AgentState) -> str:
		"""Determine if agent should continue with tools or end"""
		messages = state.get('messages', [])
		if not messages:
			logger.info('🔚 No messages found - ending workflow')
			return END

		# Check for maximum iterations to prevent infinite loops
		tool_iterations = state.get('tool_iterations', 0)
		max_iterations = 3  # Maximum 3 tool iterations

		if tool_iterations >= max_iterations:
			logger.warning(f'🔄 Maximum tool iterations ({max_iterations}) reached - ending workflow')
			return END

		last_message = messages[-1]
		if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
			logger.info('🔚 No tool calls detected - ending workflow')
			return END
		else:
			tool_count = len(last_message.tool_calls)
			tool_names = [tc.get('name', 'unknown') for tc in last_message.tool_calls]
			logger.info(
				f'🔧 Tool calls detected - continuing to tools (iteration {tool_iterations + 1})',
				tool_count=tool_count,
				tools=tool_names,
			)
			return 'tools'

	async def process_message(
		self,
		user_message: str,
		user_id: Optional[str] = None,
		conversation_id: Optional[str] = None,
		config_override: Optional[Dict[str, Any]] = None,
		timeout: float = 30.0,  # Add timeout parameter
	) -> Dict[str, Any]:
		"""Process message với unified workflow và timeout protection"""
		start_time = time.time()
		session_id = conversation_id or f'session_{int(time.time())}'

		logger.workflow_start(
			'Simplified Workflow Message Processing',
			user_id=user_id,
			conversation_id=conversation_id,
			message_length=len(user_message),
			timeout_seconds=timeout,
		)

		try:
			# Create initial state với user_id và conversation_id
			initial_state = StateManager.create_initial_state(
				user_message=user_message,
				user_id=user_id,
				session_id=session_id,
				conversation_id=conversation_id,
			)
			initial_state['tool_iterations'] = 0  # Initialize tool iterations counter

			# Prepare config với user context
			runtime_config = {
				'configurable': {
					'thread_id': session_id,
					'user_id': user_id,  # Add user_id to config
					'conversation_id': conversation_id,  # Add conversation_id to config
					**self.config.to_dict(),
				}
			}

			if config_override:
				runtime_config['configurable'].update(config_override)

			# Log runtime config
			logger.info(f'🔧 Runtime config prepared with user context:')
			logger.info(f'   - User ID: {user_id}')
			logger.info(f'   - Conversation ID: {conversation_id}')
			logger.info(f'   - Thread ID: {session_id}')

			# Execute workflow with timeout protection
			try:
				final_state = await asyncio.wait_for(
					self.compiled_graph.ainvoke(initial_state, config=runtime_config),
					timeout=timeout,
				)
			except asyncio.TimeoutError:
				logger.error(f'⏰ Workflow timeout after {timeout} seconds')
				return {
					'response': 'Xin lỗi, yêu cầu của bạn mất quá nhiều thời gian để xử lý. Vui lòng thử lại.',
					'state': initial_state,
					'metadata': {
						'processing_time': time.time() - start_time,
						'error': 'timeout',
						'timeout_seconds': timeout,
						'workflow_type': 'simplified',
					},
				}

			# Extract response
			response = self._extract_response(final_state)
			processing_time = time.time() - start_time

			logger.success(
				'Simplified Workflow processing completed',
				processing_time=processing_time,
				response_length=len(response),
				tool_iterations=final_state.get('tool_iterations', 0),
				features_used={
					'router': final_state.get('routing_complete', False),
					'rag': bool(final_state.get('combined_rag_context')),
					'guardrails': not final_state.get('guardrail_blocked', False),
					'tools': final_state.get('tool_execution_failed', False) == False and 'tool_execution_error' not in final_state,
				},
			)

			# Log tool usage summary if tools were used
			if 'tool_execution_error' not in final_state and not final_state.get('tool_execution_failed', False):
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

				if tool_calls_count > 0:
					logger.success(
						f'🔧 Workflow completed with {tool_calls_count} tool calls',
						tools_used=tools_used,
						iterations=final_state.get('tool_iterations', 0),
					)

			# Log comprehensive workflow summary
			self._log_workflow_summary(final_state, processing_time)

			return {
				'response': response,
				'state': final_state,
				'metadata': {
					'processing_time': processing_time,
					'workflow_type': 'simplified',
					'router_decision': final_state.get('router_decision'),
					'rag_used': bool(final_state.get('combined_rag_context')),
					'guardrails_passed': not final_state.get('guardrail_blocked', False),
					'tool_iterations': final_state.get('tool_iterations', 0),
				},
			}
		except Exception as e:
			logger.error(f'Simplified workflow error: {str(e)}')
			logger.error(f'Error type: {type(e).__name__}')
			logger.error(f'Error occurred at processing time: {time.time() - start_time:.2f}s')

			return {
				'response': f'Xin lỗi, có lỗi xảy ra trong quá trình xử lý: {str(e)}',
				'state': {},
				'metadata': {
					'processing_time': time.time() - start_time,
					'error': str(e),
					'error_type': type(e).__name__,
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

	def _log_workflow_summary(self, final_state: Dict[str, Any], processing_time: float):
		"""Simple workflow summary"""
		logger.info('=' * 40)
		logger.info('🎯 WORKFLOW SUMMARY')
		logger.info('=' * 40)

		logger.info(f'⏱️  Processing Time: {processing_time:.2f}s')
		logger.info(f'🔀 Router Target: {final_state.get("router_decision", {}).get("target", "unknown")}')
		logger.info(f'📚 RAG Used: {bool(final_state.get("combined_rag_context"))}')

		# Count tools used
		messages = final_state.get('messages', [])
		tool_count = 0
		for msg in messages:
			if hasattr(msg, 'tool_calls') and msg.tool_calls:
				tool_count += len(msg.tool_calls)

		logger.info(f'🔧 Total Tool Calls: {tool_count}')

		# Check for errors
		if final_state.get('tool_execution_failed'):
			logger.warning('⚠️  Tool execution failed')
		if final_state.get('guardrail_blocked'):
			logger.warning('⚠️  Input was blocked by guardrails')

		logger.info('=' * 40)

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


def create_enhanced_rag_workflow(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)


def create_workflow_with_rag(db_session: Session, config: Optional[WorkflowConfig] = None) -> Workflow:
	"""Alias for create_workflow - backward compatibility"""
	return create_workflow(db_session, config)
