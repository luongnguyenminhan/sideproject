"""
Basic Chat Workflow with integrated Agentic RAG functionality
Advanced workflow with query analysis, routing, and self-correction using Agentic RAG KBRepository
"""

from datetime import datetime, timezone
import time
from typing import Literal
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from .tools.basic_tools import tools
from .state.workflow_state import AgentState
from .config.workflow_config import WorkflowConfig
from .utils.color_logger import get_color_logger, Colors

load_dotenv()

# Initialize colorful logger
color_logger = get_color_logger(__name__)


# Router Schema theo LangChain pattern với Pydantic BaseModel
class RouterDecision(BaseModel):
	"""Router decision schema for query routing."""

	target: Literal['rag_query', 'direct_agent', 'math_tools', 'general'] = Field(description='Target node để route query đến')
	explanation: str = Field(description='Explanation cho quyết định routing')


# Default system prompt for CGSEM AI Assistant
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
6. Sử dụng kiến thức từ tài liệu CGSEM để tư vấn chuyên nghiệp

🛠️ CÔNG CỤ CÓ SẴN:
- Phép tính: add, subtract, multiply, divide
- RAG: answer_query_collection - Trả lời câu hỏi từ knowledge base của CGSEM
- Search: search_knowledge_base - Tìm kiếm thông tin trong knowledge base CGSEM

🔍 HƯỚNG DẪN SỬ DỤNG RAG:
- Khi được hỏi về thông tin cụ thể về CGSEM, sử dụng answer_query_collection
- Sử dụng search_knowledge_base để tìm kiếm thông tin trước khi trả lời
- Luôn ưu tiên thông tin từ knowledge base CGSEM

🗣️ PHONG CÁCH GIAO TIẾP:
- Nhiệt tình, tích cực và truyền cảm hứng
- Gần gũi với học sinh và giới trẻ
- Khuyến khích sáng tạo và dám thử thách
- Trả lời tự nhiên như thành viên thực sự của CGSEM

⚡ PHƯƠNG CHÂM: "CGSEM - tiên quyết, tiên phong, sáng tạo"

Bạn luôn phân tích query và sử dụng công cụ phù hợp nhất để trả lời với tinh thần nhiệt huyết của tuổi trẻ CGSEM!
"""

# Router system prompt cho CGSEM theo meobeo-ai-rule standards
ROUTER_SYSTEM_PROMPT = """
🧭 Bạn là Router Agent thông minh cho hệ thống CGSEM AI Assistant. Nhiệm vụ của bạn là phân tích user query và quyết định route phù hợp nhất.

🎯 TARGET NODES AVAILABLE:
1. "rag_query" - Cho câu hỏi cần tìm kiếm thông tin từ knowledge base hoặc file người dùng đã upload
2. "direct_agent" - Cho câu hỏi đơn giản, general knowledge, chat thông thường, chào hỏi
3. "math_tools" - Cho các phép tính, calculation, tính toán cơ bản
4. "general" - Cho các trường hợp khác

📋 QUY TẮC ROUTING:
- RAG Query: Khi user hỏi về:
    * **Thông tin từ file/tài liệu đã upload (ưu tiên cao nhất)**
    * Nội dung cụ thể mà có thể có trong file người dùng
    * Thông tin về CGSEM chỉ khi user đề cập rõ ràng về CLB
    * Kiến thức chuyên môn cần tra cứu từ tài liệu
    * **Khi user hỏi về thông tin cụ thể mà có thể đến từ file đã upload**

- Direct Agent: 
    * Chat thông thường và chào hỏi
    * Câu hỏi general knowledge không cần tra cứu file
    * Thông tin chung mà AI có thể trả lời từ kiến thức có sẵn
    * Khi chắc chắn không cần thông tin từ file người dùng

- Math Tools: 
    * Phép tính toán học cơ bản
    * Calculations và computations

- General: 
    * Các trường hợp đặc biệt khác

⚠️ NGUYÊN TẮC: Ưu tiên route "rag_query" khi user hỏi về thông tin cụ thể có thể đến từ file đã upload, không bias về thông tin CGSEM trừ khi user đề cập rõ ràng.

💡 Phân tích context để xác định user đang hỏi về file của họ hay thông tin general!
"""

# Initialize the default model
model = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)

# Global workflow config
workflow_config = None


def initialize_services(db_session, config=None):
	"""Initialize workflow configuration for Agentic RAG"""
	global workflow_config

	color_logger.workflow_start(
		'Agentic RAG Workflow Configuration',
		db_session_id=id(db_session),
		config_provided=config is not None,
	)

	try:
		workflow_config = config or WorkflowConfig.from_env()
		color_logger.info(
			f'📋 {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} Agentic RAG workflow configured',
			Colors.CYAN,
			model_name=workflow_config.model_name,
			collection_name=workflow_config.collection_name,
		)

		color_logger.workflow_complete(
			'Agentic RAG Workflow Configuration',
			time.time(),
			services_count=1,
			status='success',
		)
		return True
	except Exception as e:
		color_logger.error(
			f'Failed to initialize Agentic RAG workflow config: {str(e)}',
			error_type=type(e).__name__,
			traceback_available=True,
		)
		return False


def should_continue(state):
	"""Determine if the agent should continue with tool execution or end."""
	messages = state.get('messages', [])
	if not messages:
		return END

	last_message = messages[-1]
	if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
		return END
	else:
		return 'tools'


def get_tool_defs(config):
	"""Get tool definitions for binding to the model."""
	from .tools.basic_tools import get_tool_definitions

	return get_tool_definitions(config)


def get_tools(config):
	"""Get tool instances for the tool node."""
	from .tools.basic_tools import get_tools as get_basic_tools

	return get_basic_tools(config)


async def rag_query_node(state, config):
	"""RAG Query Node - Bắt buộc search knowledge base trước khi đưa cho agent"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start(
		'RAG Query Node - Mandatory Knowledge Retrieval',
		thread_id=thread_id,
		mandatory_rag=True,
	)

	# Get user message để làm query
	messages = state.get('messages', [])
	if not messages:
		return state

	# Lấy message cuối cùng từ user
	user_query = None
	for msg in reversed(messages):
		if hasattr(msg, 'content') and msg.content:
			user_query = msg.content
			break

	if not user_query:
		color_logger.warning('No user query found for RAG')
		return state

	# Thực hiện RAG query bắt buộc
	try:
		# Collection ID sử dụng conversation_id format
		collection_id = f'conversation_{thread_id}'

		color_logger.info(
			f'🔍 {Colors.BOLD}MANDATORY RAG:{Colors.RESET}{Colors.BRIGHT_YELLOW} Searching knowledge base',
			Colors.BRIGHT_YELLOW,
			query_preview=user_query[:100],
			collection_id=collection_id,
		)

		# Import RAG dependencies
		from app.modules.agentic_rag.agent.rag_graph import RAGAgentGraph
		from app.modules.agentic_rag.repositories.kb_repo import KBRepository

		# Initialize RAG agent for the collection
		kb_repo = KBRepository(collection_name=collection_id)
		rag_agent = RAGAgentGraph(kb_repo=kb_repo, collection_id=collection_id)

		# Process the query
		result = await rag_agent.answer_query(query=user_query, collection_id=collection_id)

		# Format the response with answer and sources
		answer = result.get('answer', 'No answer found')
		sources = result.get('sources', [])

		# Create a formatted response that includes source information
		rag_response = answer

		if sources:
			rag_response += '\n\n📚 Sources:'
			for i, source in enumerate(sources, 1):
				source_info = f'\n{i}. Document ID: {source.get("id", "Unknown")}'
				if 'metadata' in source and 'source' in source['metadata']:
					source_info += f' (File: {source["metadata"]["source"]})'
				rag_response += source_info

		color_logger.info(
			f"[RAG Query] RAG query completed for collection '{collection_id}' with {len(sources)} sources",
			source_count=len(sources),
			answer_length=len(answer),
		)

		# Lưu RAG context vào state
		rag_context = [rag_response] if rag_response else []

		color_logger.info(
			f'🧠 {Colors.BOLD}RAG CONTEXT RETRIEVED:{Colors.RESET}{Colors.BRIGHT_GREEN} Context length: {len(rag_response) if rag_response else 0}',
			Colors.BRIGHT_GREEN,
			context_available=bool(rag_response),
			response_preview=rag_response[:200] if rag_response else 'No context',
		)

		# Update state với RAG context
		updated_state = {
			**state,
			'rag_context': rag_context,
			'retrieval_quality': 'good' if rag_response else 'no_results',
			'agentic_rag_used': True,
			'mandatory_rag_complete': True,
		}

		processing_time = time.time() - start_time
		color_logger.workflow_complete(
			'RAG Query Node - Mandatory Knowledge Retrieval',
			processing_time,
			rag_context_retrieved=bool(rag_response),
			context_length=len(rag_response) if rag_response else 0,
		)

		return updated_state

	except Exception as e:
		color_logger.error(
			f'RAG Query Node failed: {str(e)}',
			error_type=type(e).__name__,
		)
		# Continue với empty context thay vì fail
		return {
			**state,
			'rag_context': [],
			'retrieval_quality': 'error',
			'agentic_rag_used': False,
			'mandatory_rag_complete': True,
		}


async def call_model(state, config):
	"""Agentic RAG - Enhanced Model Call với RAG Context có sẵn và Persona Support"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start(
		'Agentic RAG - Model Invocation with Pre-loaded Context and Persona',
		thread_id=thread_id,
		has_context=bool(state.get('rag_context')),
		mandatory_rag_complete=state.get('mandatory_rag_complete', False),
		agentic_rag_enabled=True,
		persona_enabled=workflow_config.persona_enabled if workflow_config else False,
	)

	# Get system prompt - Use persona if enabled
	if workflow_config and workflow_config.persona_enabled:
		persona_prompt = workflow_config.get_persona_prompt()
		persona_name = workflow_config.get_persona_name()

		color_logger.info(
			f'🎭 {Colors.BOLD}PERSONA ACTIVATED:{Colors.RESET}{Colors.BRIGHT_MAGENTA} {persona_name}',
			Colors.BRIGHT_MAGENTA,
			persona_name=persona_name,
			persona_type=(workflow_config.persona_type.value if workflow_config.persona_type else 'none'),
		)
		system = persona_prompt
	else:
		system = config.get('configurable', {}).get('system_prompt', DEFAULT_SYSTEM_PROMPT)

	# Enhanced system prompt for Agentic RAG với CGSEM context và Persona
	persona_info = ''
	if workflow_config and workflow_config.persona_enabled:
		persona_info = f"""
🎭 PERSONA ACTIVE: {workflow_config.get_persona_name()}
Persona Type: {workflow_config.persona_type.value if workflow_config.persona_type else 'none'}
"""

	agentic_system = f"""{system}

🤖 BẠN LÀ CGSEM AGENTIC RAG AI với KNOWLEDGE CONTEXT - Context đã được load sẵn:{persona_info}

🛠️ BASIC TOOLS AVAILABLE:
- add(a, b): Cộng hai số
- subtract(a, b): Trừ hai số  
- multiply(a, b): Nhân hai số
- divide(a, b): Chia hai số

📊 CONVERSATION CONTEXT: {thread_id}
📈 RAG Status: {state.get('retrieval_quality', 'unknown')}
✅ Context Pre-loaded: {state.get('mandatory_rag_complete', False)}
🔥 Agentic RAG: {state.get('agentic_rag_used', True)}

🌟 HƯỚNG DẪN ĐẶC BIỆT CHO CGSEM:
1. 📚 CONTEXT CGSEM ĐÃ CÓ SẴN: Sử dụng knowledge context CGSEM được cung cấp bên dưới làm nguồn chính
2. 🧮 TÍNH TOÁN: Sử dụng math tools khi cần thực hiện phép tính cho dự án, sự kiện
3. 💡 Kết hợp context CGSEM với kiến thức về truyền thông, sự kiện để trả lời toàn diện
4. 🎯 TRẢ LỜI TỰ NHIÊN: KHÔNG ghi "(Theo thông tin từ context)" - trả lời như thành viên thực sự của CGSEM
5. 🗣️ Nói như thể bạn là một phần của CLB CGSEM, sử dụng "chúng mình", "CLB của mình", "team CGSEM"
6. ⚡ Context CGSEM đã được retrieve tự động, không cần gọi thêm RAG tools
7. 🎭 Giữ tinh thần nhiệt huyết, sáng tạo và truyền cảm hứng của CGSEM
8. 🌈 Luôn khuyến khích tham gia hoạt động và phát triển bản thân cùng CGSEM
"""

	# Add RAG context if available (from mandatory RAG query)
	rag_context = state.get('rag_context')
	if rag_context:
		context_quality = state.get('retrieval_quality', 'unknown')
		context_length = sum(len(ctx) for ctx in rag_context)

		color_logger.info(
			f'🧠 {Colors.BOLD}PRE-LOADED RAG CONTEXT:{Colors.RESET}{Colors.BRIGHT_YELLOW} Quality={context_quality}',
			Colors.BRIGHT_YELLOW,
			sources_count=len(rag_context),
			total_context_length=context_length,
			quality=context_quality,
			pre_loaded=True,
		)

		enhanced_system = f'{agentic_system}\n\n🔗 KIẾN THỨC TỪ CGSEM KNOWLEDGE BASE (Quality: {context_quality}):\n' + '\n'.join(rag_context)
	else:
		color_logger.info(
			f'📝 {Colors.BOLD}NO RAG CONTEXT:{Colors.RESET}{Colors.DIM} No context retrieved from knowledge base',
			Colors.DIM,
			context_available=False,
		)
		enhanced_system = agentic_system

	# Prepare messages
	messages = state.get('messages', [])
	if not messages:
		return {'messages': [SystemMessage(content=enhanced_system)]}

	# Create enhanced prompt
	prompt = ChatPromptTemplate.from_messages([
		('system', enhanced_system),
		MessagesPlaceholder(variable_name='chat_history'),
		MessagesPlaceholder(variable_name='agent_scratchpad'),
	])

	formatted_prompt = prompt.format_messages(
		chat_history=messages,
		agent_scratchpad=[],
	)

	color_logger.info(
		f'🤖 {Colors.BOLD}AGENTIC RAG MODEL + TOOLS:{Colors.RESET}{Colors.BRIGHT_BLUE} Processing with enhanced context and math tools',
		Colors.BRIGHT_BLUE,
		model_name=getattr(model, 'model', 'unknown'),
		total_messages=len(formatted_prompt),
		math_tools_count=len(get_tool_defs(config)),
	)

	# Invoke model with RAG tools bound
	model_with_tools = model.bind_tools(get_tool_defs(config))
	response = await model_with_tools.ainvoke(
		formatted_prompt,
		{
			'system_time': datetime.now(tz=timezone.utc).isoformat(),
			'agentic_mode': True,
			'agentic_rag': True,
			'rag_tools_enabled': True,
			'conversation_id': thread_id,
		},
	)

	processing_time = time.time() - start_time
	color_logger.model_invocation(
		getattr(model, 'model', 'unknown'),
		len(str(response.content)) // 4,  # Token estimate
		processing_time=processing_time,
		response_length=len(str(response.content)),
		agentic_mode=True,
		agentic_rag=True,
		rag_tools_enabled=True,
	)

	return {'messages': response}


async def run_tools(input, config, **kwargs):
	"""Execute tools in Agentic RAG context"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start('Agentic RAG - Tool Execution', thread_id=thread_id)

	messages = input.get('messages', [])
	tool_calls = []
	if messages:
		last_message = messages[-1]
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			tool_calls = last_message.tool_calls

	tool_node = ToolNode(get_tools(config))
	response = await tool_node.ainvoke(input, config, **kwargs)

	processing_time = time.time() - start_time
	tool_names = [tc.get('name', 'unknown') for tc in tool_calls] if tool_calls else []

	color_logger.tool_execution(
		tool_names,
		processing_time,
		thread_id=thread_id,
		agentic_mode=True,
	)

	return response


async def router_node(state, config):
	"""Router Node - Intelligent query routing với LLM router sử dụng structured output"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start(
		'Router Node - Intelligent Query Routing',
		thread_id=thread_id,
		router_enabled=True,
	)

	# Get user message để phân tích routing
	messages = state.get('messages', [])
	if not messages:
		color_logger.warning('No messages found for routing')
		return {
			**state,
			'router_decision': {'target': 'general', 'explanation': 'No user input'},
		}

	# Lấy message cuối cùng từ user
	user_query = None
	for msg in reversed(messages):
		if hasattr(msg, 'content') and msg.content:
			user_query = msg.content
			break

	if not user_query:
		color_logger.warning('No user query found for routing')
		return {
			**state,
			'router_decision': {'target': 'general', 'explanation': 'Empty query'},
		}

	try:
		# Create router prompt theo LangChain pattern
		router_prompt = ChatPromptTemplate.from_messages([
			('system', ROUTER_SYSTEM_PROMPT),
			(
				'human',
				'User query: {input}\n\nAnalyze this query and determine the best routing target.',
			),
		])

		# Create router chain với structured output
		router_chain = router_prompt | model.with_structured_output(RouterDecision)

		color_logger.info(
			f'🧭 {Colors.BOLD}ROUTER ANALYSIS:{Colors.RESET}{Colors.BRIGHT_YELLOW} Analyzing query for routing',
			Colors.BRIGHT_YELLOW,
			query_preview=user_query[:100],
			available_targets=['rag_query', 'direct_agent', 'math_tools', 'general'],
		)

		# Execute router decision
		router_result = await router_chain.ainvoke({'input': user_query})

		target = router_result.target if hasattr(router_result, 'target') else 'general'
		explanation = router_result.explanation if hasattr(router_result, 'explanation') else 'Default routing'

		color_logger.info(
			f'🎯 {Colors.BOLD}ROUTER DECISION:{Colors.RESET}{Colors.BRIGHT_GREEN} Target={target}',
			Colors.BRIGHT_GREEN,
			target=target,
			explanation=explanation,
			query_length=len(user_query),
		)

		# Update state với router decision
		updated_state = {
			**state,
			'router_decision': {'target': target, 'explanation': explanation},
			'routing_complete': True,
		}

		processing_time = time.time() - start_time
		color_logger.workflow_complete(
			'Router Node - Intelligent Query Routing',
			processing_time,
			target_selected=target,
			routing_successful=True,
		)

		return updated_state

	except Exception as e:
		color_logger.error(
			f'Router Node failed: {str(e)}',
			error_type=type(e).__name__,
		)

		# Fallback routing on error
		return {
			**state,
			'router_decision': {
				'target': 'general',
				'explanation': f'Router error: {str(e)[:100]}',
			},
			'routing_complete': True,
		}


def router_conditional_edge(state):
	"""Conditional edge function for router decisions"""
	router_decision = state.get('router_decision', {})
	target = router_decision.get('target', 'general') if isinstance(router_decision, dict) else 'general'

	# Map router targets to actual nodes
	target_mapping = {
		'rag_query': 'rag_query',
		'direct_agent': 'agent',
		'math_tools': 'agent',  # Will use tools via agent
		'general': 'agent',
	}

	actual_target = target_mapping.get(target, 'agent')

	color_logger.info(
		f'🔀 {Colors.BOLD}ROUTER EDGE:{Colors.RESET}{Colors.CYAN} {target} → {actual_target}',
		Colors.CYAN,
		logical_target=target,
		actual_node=actual_target,
	)

	return actual_target


def create_agentic_rag_workflow(db_session, config=None):
	"""Create Agentic RAG Workflow with Router + KBRepository and RAG Tools - Intelligent routing với LLM router và Persona support"""
	color_logger.workflow_start(
		'Agentic RAG Workflow Creation with Router + KBRepository + RAG Tools + Persona',
		router_enabled=True,
		intelligent_routing=True,
		db_session_provided=db_session is not None,
		rag_tools_enabled=True,
		persona_enabled=workflow_config.persona_enabled if workflow_config else False,
	)

	# Initialize workflow configuration
	services_ready = initialize_services(db_session, config)

	# Log persona information if enabled
	persona_info = ''
	if workflow_config and workflow_config.persona_enabled:
		persona_name = workflow_config.get_persona_name()
		persona_info = f' + {persona_name} Persona'

		color_logger.info(
			f'🎭 {Colors.BOLD}PERSONA ENABLED:{Colors.RESET}{Colors.BRIGHT_MAGENTA} {persona_name}',
			Colors.BRIGHT_MAGENTA,
			persona_name=persona_name,
			persona_type=(workflow_config.persona_type.value if workflow_config.persona_type else 'none'),
		)

	color_logger.info(
		f'🚀 {Colors.BOLD}AGENTIC RAG + TOOLS{persona_info}:{Colors.RESET}{Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED} {"READY" if services_ready else "FAILED"}',
		Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED,
		services_initialized=services_ready,
		agentic_rag=True,
		rag_tools_enabled=True,
		persona_enabled=workflow_config.persona_enabled if workflow_config else False,
	)

	# Define Agentic RAG workflow with Router and tools
	workflow = StateGraph(AgentState)

	# Add Router and Agentic RAG nodes
	workflow.add_node('router', router_node)  # Router node - entry point
	workflow.add_node('rag_query', rag_query_node)  # RAG query node
	workflow.add_node('agent', call_model)  # Agent node
	workflow.add_node('tools', run_tools)  # Tools node

	available_tools = get_tools(config)
	tool_names = [tool.name for tool in available_tools]

	color_logger.info(
		f'📊 {Colors.BOLD}ROUTER + AGENTIC RAG WORKFLOW NODES:{Colors.RESET}{Colors.MAGENTA} Workflow nodes configured',
		Colors.MAGENTA,
		node_count=4,
		nodes=['router', 'rag_query', 'agent', 'tools'],
		available_tools=tool_names,
		math_tools_count=len([t for t in tool_names if t in ['add', 'subtract', 'multiply', 'divide']]),
		router_enabled=True,
		intelligent_routing=True,
	)

	# Router-based flow: router → (rag_query | agent) → tools (if needed) → agent → END
	workflow.set_entry_point('router')  # Bắt đầu với Router

	# Router → conditional routing to rag_query or agent
	workflow.add_conditional_edges('router', router_conditional_edge, {'rag_query': 'rag_query', 'agent': 'agent'})

	# RAG query → agent (when RAG is needed)
	workflow.add_edge('rag_query', 'agent')

	# Agent → tools (if needed) or END
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	color_logger.info(
		f'🔗 {Colors.BOLD}INTELLIGENT ROUTER FLOW:{Colors.RESET}{Colors.CYAN} Router → (RAG Query | Direct Agent) → Math Tools (if needed) → Agent → END',
		Colors.CYAN,
		entry_point='router',
		router_enabled=True,
		intelligent_routing=True,
		agentic_rag=True,
		math_tools_enabled=True,
	)

	# Compile with memory
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	color_logger.workflow_complete(
		'Agentic RAG Workflow Creation with Router + KBRepository + RAG Tools + Persona',
		time.time(),
		router_enabled=True,
		intelligent_routing=True,
		agentic_rag_enabled=True,
		agentic_rag=True,
		rag_tools_enabled=True,
		persona_enabled=workflow_config.persona_enabled if workflow_config else False,
		persona_name=(workflow_config.get_persona_name() if workflow_config and workflow_config.persona_enabled else None),
		compilation_successful=True,
	)

	return compiled_workflow


# Create default Agentic RAG workflow
def create_workflow_with_rag(db_session, config=None):
	"""Backward compatibility - now creates Agentic RAG workflow with KBRepository"""
	return create_agentic_rag_workflow(db_session, config)
