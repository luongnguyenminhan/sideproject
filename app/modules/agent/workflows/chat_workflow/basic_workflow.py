"""
Basic Chat Workflow with integrated Agentic RAG functionality
Advanced workflow with query analysis, routing, and self-correction using LangChain Qdrant
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
from app.modules.agentic_rag.services.langchain_qdrant_service import (
	LangChainQdrantService,
)
from .utils.color_logger import get_color_logger, Colors

load_dotenv()

# Initialize colorful logger
color_logger = get_color_logger(__name__)

# Default system prompt for the financial assistant
DEFAULT_SYSTEM_PROMPT = """
Bạn là trợ lý tài chính thông minh MoneyEZ, một trợ lý AI được tạo ra để giúp người dùng quản lý tài chính cá nhân.
Nhiệm vụ của bạn:
1. Giúp người dùng theo dõi chi tiêu hàng ngày
2. Phân loại các khoản chi tiêu vào các danh mục phù hợp
3. Cung cấp thông tin và tư vấn tài chính
4. Trả lời mọi câu hỏi liên quan đến tài chính cá nhân một cách chính xác và hữu ích
5. Thực hiện các phép tính cơ bản khi cần thiết
6. Sử dụng kiến thức tài chính để tư vấn chuyên nghiệp

Bạn có thể sử dụng các công cụ tính toán đơn giản: cộng, trừ, nhân, chia để hỗ trợ người dùng.
Bạn luôn phân tích query và sử dụng kiến thức phù hợp nhất để trả lời.
"""

# Initialize the default model
model = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)

# Global services - will be initialized when workflow is created
langchain_qdrant_service = None
query_optimizer = None
knowledge_retriever = None
workflow_config = None


def initialize_services(db_session, config=None):
	"""Initialize Agentic RAG services with LangChain Qdrant"""
	global langchain_qdrant_service, query_optimizer, knowledge_retriever, workflow_config

	color_logger.workflow_start(
		'Agentic RAG Services Initialization',
		db_session_id=id(db_session),
		config_provided=config is not None,
	)

	try:
		workflow_config = config or WorkflowConfig.from_env()
		color_logger.info(
			f'📋 {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} Agentic RAG with LangChain Qdrant enabled',
			Colors.CYAN,
			model_name=workflow_config.model_name,
			collection_name=workflow_config.collection_name,
		)

		langchain_qdrant_service = LangChainQdrantService(db_session)
		color_logger.success(
			'LangChainQdrantService initialized',
			service_type='LangChainQdrantService',
			status='ready',
		)

		color_logger.workflow_complete(
			'Agentic RAG Services Initialization',
			time.time(),
			services_count=3,
			status='success',
		)
		return True
	except Exception as e:
		color_logger.error(
			f'Failed to initialize Agentic RAG services: {str(e)}',
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
	return tools


def get_tools(config):
	"""Get tool instances for the tool node."""
	return tools


async def call_model(state, config):
	"""Agentic RAG - Enhanced Model Call with LangChain Qdrant Context"""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
	color_logger.workflow_start(
		'Agentic RAG - Model Invocation',
		thread_id=thread_id,
		has_context=bool(state.get('rag_context')),
		langchain_qdrant=state.get('langchain_qdrant_used', False),
	)

	# Get system prompt
	system = config.get('configurable', {}).get('system_prompt', DEFAULT_SYSTEM_PROMPT)

	# Enhanced system prompt for Agentic RAG with LangChain Qdrant
	agentic_system = f"""{system}

BẠN LÀ AGENTIC RAG AI với LangChain Qdrant - Sử dụng thông tin được cung cấp một cách thông minh:

Retrieval Strategy: {state.get('retrieval_strategy_used', 'comprehensive')}
Document Quality: {state.get('retrieval_quality', 'unknown')}
Grading Score: {state.get('grading_score', 0):.2f}
LangChain Qdrant: {state.get('langchain_qdrant_used', False)}

Hướng dẫn đặc biệt:
1. Ưu tiên thông tin từ nguồn có độ tin cậy cao từ LangChain Qdrant
2. Kết hợp kiến thức từ nhiều nguồn khi phù hợp
3. Nếu thông tin không đủ, hãy nói rõ và đưa ra câu trả lời tốt nhất có thể
4. Luôn kiểm tra tính nhất quán của thông tin
5. Cung cấp lý do và nguồn gốc thông tin khi có thể
"""

	# Add RAG context
	rag_context = state.get('rag_context')
	if rag_context:
		context_quality = state.get('retrieval_quality', 'unknown')
		context_length = sum(len(ctx) for ctx in rag_context)

		color_logger.info(
			f'🧠 {Colors.BOLD}LANGCHAIN CONTEXT:{Colors.RESET}{Colors.BRIGHT_YELLOW} Quality={context_quality}',
			Colors.BRIGHT_YELLOW,
			sources_count=len(rag_context),
			total_context_length=context_length,
			quality=context_quality,
		)

		enhanced_system = f'{agentic_system}\n\nKIẾN THỨC TỪ LANGCHAIN QDRANT (Quality: {context_quality}):\n' + '\n'.join(rag_context)
	else:
		color_logger.info(
			f'📝 {Colors.BOLD}NO CONTEXT:{Colors.RESET}{Colors.DIM} Using base knowledge',
			Colors.DIM,
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
		f'🤖 {Colors.BOLD}AGENTIC LANGCHAIN MODEL:{Colors.RESET}{Colors.BRIGHT_BLUE} Processing with enhanced context',
		Colors.BRIGHT_BLUE,
		model_name=getattr(model, 'model', 'unknown'),
		total_messages=len(formatted_prompt),
	)

	# Invoke model
	model_with_tools = model.bind_tools(get_tool_defs(config))
	response = await model_with_tools.ainvoke(
		formatted_prompt,
		{
			'system_time': datetime.now(tz=timezone.utc).isoformat(),
			'agentic_mode': True,
			'langchain_qdrant': True,
		},
	)

	processing_time = time.time() - start_time
	color_logger.model_invocation(
		getattr(model, 'model', 'unknown'),
		len(str(response.content)) // 4,  # Token estimate
		processing_time=processing_time,
		response_length=len(str(response.content)),
		agentic_mode=True,
		langchain_qdrant=True,
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
	"""Create Agentic RAG Workflow with LangChain Qdrant - Always uses RAG with intelligent routing"""
	color_logger.workflow_start(
		'Agentic RAG Workflow Creation with LangChain Qdrant',
		always_rag=True,
		db_session_provided=db_session is not None,
	)

	# Initialize services
	services_ready = initialize_services(db_session, config)

	color_logger.info(
		f'🚀 {Colors.BOLD}LANGCHAIN AGENTIC RAG:{Colors.RESET}{Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED} {"READY" if services_ready else "FAILED"}',
		Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED,
		services_initialized=services_ready,
		langchain_qdrant=True,
	)

	# Define Agentic RAG workflow
	workflow = StateGraph(AgentState)

	# Add Agentic RAG nodes
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

	color_logger.info(
		f'📊 {Colors.BOLD}LANGCHAIN AGENTIC NODES:{Colors.RESET}{Colors.MAGENTA} Workflow nodes configured',
		Colors.MAGENTA,
		node_count=2,
		nodes=[
			'agent',
			'tools',
		],
	)

	# Agentic RAG flow - ALWAYS goes through RAG
	workflow.set_entry_point('agent')

	# Tool handling
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	color_logger.info(
		f'🔗 {Colors.BOLD}LANGCHAIN AGENTIC FLOW:{Colors.RESET}{Colors.CYAN} Always RAG → Analysis → LangChain Retrieve → Grade → Generate',
		Colors.CYAN,
		entry_point='agent',
		always_rag=True,
		langchain_qdrant=True,
	)

	# Compile with memory
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	color_logger.workflow_complete(
		'Agentic RAG Workflow Creation with LangChain Qdrant',
		time.time(),
		agentic_rag_enabled=True,
		always_rag=True,
		langchain_qdrant=True,
		compilation_successful=True,
	)

	return compiled_workflow


# Create default Agentic RAG workflow
def create_workflow_with_rag(db_session, config=None):
	"""Backward compatibility - now creates Agentic RAG workflow with LangChain Qdrant"""
	return create_agentic_rag_workflow(db_session, config)
