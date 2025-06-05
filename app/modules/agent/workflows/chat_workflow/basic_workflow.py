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


async def call_model(state, config):
	"""Agentic RAG - Enhanced Model Call with RAG Tools (File Indexing Service)"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start(
		'Agentic RAG - Model Invocation with RAG Tools (File Indexing)',
		thread_id=thread_id,
		has_context=bool(state.get('rag_context')),
		agentic_rag_enabled=True,
		rag_tools_enabled=True,
	)

	# Get system prompt
	system = config.get('configurable', {}).get('system_prompt', DEFAULT_SYSTEM_PROMPT)

	# Enhanced system prompt for Agentic RAG with Tools
	agentic_system = f"""{system}

🤖 BẠN LÀ AGENTIC RAG AI với RAG TOOLS - Sử dụng công cụ một cách thông minh:

RAG Tools Available:
- answer_query_collection(query, conversation_id): Trả lời câu hỏi từ knowledge base
- search_knowledge_base(query, collection_id, top_k): Tìm kiếm trong knowledge base
- Basic math tools: add, subtract, multiply, divide

Conversation Context: {thread_id}
Retrieval Strategy: {state.get('retrieval_strategy_used', 'comprehensive')}
Document Quality: {state.get('retrieval_quality', 'unknown')}
Grading Score: {state.get('grading_score', 0):.2f}
Agentic RAG: {state.get('agentic_rag_used', True)}

Hướng dẫn đặc biệt:
1. 📚 KHI CẦN THÔNG TIN: Sử dụng answer_query_collection với conversation_id = "{thread_id}"
2. 🔍 KHI CẦN TÌM KIẾM: Sử dụng search_knowledge_base trước
3. 🧮 KHI CẦN TÍNH TOÁN: Sử dụng math tools
4. 💡 Kết hợp thông tin từ tools với kiến thức của bạn
5. 📝 Luôn cite sources khi sử dụng thông tin từ RAG tools
"""

	# Add RAG context if available (from file indexing service)
	rag_context = state.get('rag_context')
	if rag_context:
		context_quality = state.get('retrieval_quality', 'unknown')
		context_length = sum(len(ctx) for ctx in rag_context)

		color_logger.info(
			f'🧠 {Colors.BOLD}AGENTIC RAG CONTEXT + RAG TOOLS:{Colors.RESET}{Colors.BRIGHT_YELLOW} Quality={context_quality}',
			Colors.BRIGHT_YELLOW,
			sources_count=len(rag_context),
			total_context_length=context_length,
			quality=context_quality,
			rag_tools_enabled=True,
		)

		enhanced_system = f'{agentic_system}\n\n🔗 KIẾN THỨC TỪ AGENTIC RAG (Quality: {context_quality}):\n' + '\n'.join(rag_context)
	else:
		color_logger.info(
			f'📝 {Colors.BOLD}RAG TOOLS ONLY:{Colors.RESET}{Colors.DIM} Using tools for knowledge access',
			Colors.DIM,
			rag_tools_enabled=True,
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
		f'🤖 {Colors.BOLD}AGENTIC RAG MODEL + TOOLS:{Colors.RESET}{Colors.BRIGHT_BLUE} Processing with enhanced context and RAG tools',
		Colors.BRIGHT_BLUE,
		model_name=getattr(model, 'model', 'unknown'),
		total_messages=len(formatted_prompt),
		rag_tools_count=len(get_tool_defs(config)),
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
	"""Create Agentic RAG Workflow with KBRepository and RAG Tools - Always uses RAG with intelligent routing"""
	color_logger.workflow_start(
		'Agentic RAG Workflow Creation with KBRepository + RAG Tools',
		always_rag=True,
		db_session_provided=db_session is not None,
		rag_tools_enabled=True,
	)

	# Initialize workflow configuration
	services_ready = initialize_services(db_session, config)

	color_logger.info(
		f'🚀 {Colors.BOLD}AGENTIC RAG + TOOLS:{Colors.RESET}{Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED} {"READY" if services_ready else "FAILED"}',
		Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED,
		services_initialized=services_ready,
		agentic_rag=True,
		rag_tools_enabled=True,
	)

	# Define Agentic RAG workflow with tools
	workflow = StateGraph(AgentState)

	# Add Agentic RAG nodes with tool support
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

	available_tools = get_tools(config)
	tool_names = [tool.name for tool in available_tools]

	color_logger.info(
		f'📊 {Colors.BOLD}AGENTIC RAG NODES + RAG TOOLS:{Colors.RESET}{Colors.MAGENTA} Workflow nodes configured',
		Colors.MAGENTA,
		node_count=2,
		nodes=['agent', 'tools'],
		available_tools=tool_names,
		rag_tools_count=len([t for t in tool_names if 'query' in t or 'search' in t]),
	)

	# Agentic RAG flow with tool support
	workflow.set_entry_point('agent')

	# Tool handling with RAG support
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	color_logger.info(
		f'🔗 {Colors.BOLD}AGENTIC RAG FLOW + RAG TOOLS:{Colors.RESET}{Colors.CYAN} Always RAG → Analysis → Tools → KB Retrieve → Grade → Generate',
		Colors.CYAN,
		entry_point='agent',
		always_rag=True,
		agentic_rag=True,
		rag_tools_enabled=True,
	)

	# Compile with memory
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	color_logger.workflow_complete(
		'Agentic RAG Workflow Creation with KBRepository + RAG Tools',
		time.time(),
		agentic_rag_enabled=True,
		always_rag=True,
		agentic_rag=True,
		rag_tools_enabled=True,
		compilation_successful=True,
	)

	return compiled_workflow


# Create default Agentic RAG workflow
def create_workflow_with_rag(db_session, config=None):
	"""Backward compatibility - now creates Agentic RAG workflow with KBRepository"""
	return create_agentic_rag_workflow(db_session, config)
