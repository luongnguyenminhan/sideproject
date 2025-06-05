"""
Basic Chat Workflow with integrated Agentic RAG functionality
Advanced workflow with query analysis, routing, and self-correction using Agentic RAG KBRepository
"""

from datetime import datetime, timezone
import time
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver

from .tools.basic_tools import tools
from .state.workflow_state import AgentState
from .config.workflow_config import WorkflowConfig
from .utils.color_logger import get_color_logger, Colors

load_dotenv()

# Initialize colorful logger
color_logger = get_color_logger(__name__)

# Default system prompt for the financial assistant
DEFAULT_SYSTEM_PROMPT = """
Bạn là trợ lý tài chính thông minh MoneyEZ với khả năng RAG (Retrieval-Augmented Generation), một trợ lý AI được tạo ra để giúp người dùng quản lý tài chính cá nhân.

Nhiệm vụ của bạn:
1. Giúp người dùng theo dõi chi tiêu hàng ngày
2. Phân loại các khoản chi tiêu vào các danh mục phù hợp
3. Cung cấp thông tin và tư vấn tài chính từ knowledge base
4. Trả lời mọi câu hỏi liên quan đến tài chính cá nhân một cách chính xác và hữu ích
5. Thực hiện các phép tính cơ bản khi cần thiết
6. Sử dụng kiến thức từ tài liệu đã upload để tư vấn chuyên nghiệp

Công cụ có sẵn:
- Phép tính: add, subtract, multiply, divide
- RAG: answer_query_collection - Trả lời câu hỏi từ knowledge base của conversation cụ thể
- Search: search_knowledge_base - Tìm kiếm thông tin trong knowledge base

Hướng dẫn sử dụng RAG:
- Khi được hỏi về thông tin cụ thể, hãy sử dụng answer_query_collection với conversation_id
- Sử dụng search_knowledge_base để tìm kiếm thông tin trước khi trả lời
- Luôn ưu tiên thông tin từ knowledge base khi có

Bạn luôn phân tích query và sử dụng công cụ phù hợp nhất để trả lời.
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

	# Enhanced system prompt for Agentic RAG with Pre-loaded Context and Persona
	persona_info = ''
	if workflow_config and workflow_config.persona_enabled:
		persona_info = f"""
🎭 PERSONA ACTIVE: {workflow_config.get_persona_name()}
Persona Type: {workflow_config.persona_type.value if workflow_config.persona_type else 'none'}
"""

	agentic_system = f"""{system}

🤖 BẠN LÀ AGENTIC RAG AI với KNOWLEDGE CONTEXT - Context đã được load sẵn:{persona_info}

Basic Tools Available:
- add(a, b): Cộng hai số
- subtract(a, b): Trừ hai số  
- multiply(a, b): Nhân hai số
- divide(a, b): Chia hai số

Conversation Context: {thread_id}
RAG Status: {state.get('retrieval_quality', 'unknown')}
Context Pre-loaded: {state.get('mandatory_rag_complete', False)}
Agentic RAG: {state.get('agentic_rag_used', True)}

Hướng dẫn đặc biệt:
1. 📚 CONTEXT ĐÃ CÓ SẴN: Sử dụng knowledge context được cung cấp bên dưới làm nguồn chính
2. 🧮 TÍNH TOÁN: Sử dụng math tools khi cần thực hiện phép tính
3. 💡 Kết hợp context có sẵn với kiến thức của bạn để trả lời toàn diện
4. 🎯 TRẢ LỜI TỰ NHIÊN: KHÔNG ghi "(Theo thông tin từ context)" hay trích nguồn máy móc
5. 🗣️ Nói như thể thông tin đó là kiến thức của bạn, trả lời trực tiếp và tự nhiên
6. ⚡ Context đã được retrieve tự động, không cần gọi thêm RAG tools
7. 🎭 Giữ đúng personality và phong cách giao tiếp theo persona được định nghĩa
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

		enhanced_system = f'{agentic_system}\n\n🔗 KIẾN THỨC TỪ KNOWLEDGE BASE (Quality: {context_quality}):\n' + '\n'.join(rag_context)
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


def create_agentic_rag_workflow(db_session, config=None):
	"""Create Agentic RAG Workflow with KBRepository and RAG Tools - Always uses RAG with intelligent routing and Persona support"""
	color_logger.workflow_start(
		'Agentic RAG Workflow Creation with KBRepository + RAG Tools + Persona',
		always_rag=True,
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

	# Define Agentic RAG workflow with tools
	workflow = StateGraph(AgentState)

	# Add Agentic RAG nodes với mandatory RAG flow
	workflow.add_node('rag_query', rag_query_node)  # Mandatory RAG node
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

	available_tools = get_tools(config)
	tool_names = [tool.name for tool in available_tools]

	color_logger.info(
		f'📊 {Colors.BOLD}MANDATORY RAG WORKFLOW NODES:{Colors.RESET}{Colors.MAGENTA} Workflow nodes configured',
		Colors.MAGENTA,
		node_count=3,
		nodes=['rag_query', 'agent', 'tools'],
		available_tools=tool_names,
		math_tools_count=len([t for t in tool_names if t in ['add', 'subtract', 'multiply', 'divide']]),
		mandatory_rag=True,
	)

	# Mandatory RAG flow: rag_query → agent → tools (if needed) → agent → END
	workflow.set_entry_point('rag_query')  # Bắt đầu với RAG query

	# RAG query → agent (luôn luôn)
	workflow.add_edge('rag_query', 'agent')

	# Agent → tools (if needed) or END
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	color_logger.info(
		f'🔗 {Colors.BOLD}MANDATORY RAG FLOW:{Colors.RESET}{Colors.CYAN} RAG Query (Mandatory) → Agent → Math Tools (if needed) → Agent → END',
		Colors.CYAN,
		entry_point='rag_query',
		mandatory_rag=True,
		always_rag=True,
		agentic_rag=True,
		math_tools_enabled=True,
	)

	# Compile with memory
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	color_logger.workflow_complete(
		'Agentic RAG Workflow Creation with KBRepository + RAG Tools + Persona',
		time.time(),
		agentic_rag_enabled=True,
		always_rag=True,
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
