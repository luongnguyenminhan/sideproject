"""
Basic Chat Workflow with integrated RAG functionality
Simple workflow with basic calculation tools + knowledge retrieval
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
from .knowledge.query_optimizer import QueryOptimizer
from .knowledge.retriever import KnowledgeRetriever
from .config.workflow_config import WorkflowConfig
from app.modules.agent.services.qdrant_service import QdrantService
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
Khi cần thông tin chuyên sâu, bạn sẽ tham khảo cơ sở dữ liệu kiến thức tài chính.
"""

# Initialize the default model
model = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite', temperature=0)

# Global services - will be initialized when workflow is created
qdrant_service = None
query_optimizer = None
knowledge_retriever = None
workflow_config = None


def initialize_services(db_session, config=None):
	"""Initialize RAG services"""
	global qdrant_service, query_optimizer, knowledge_retriever, workflow_config

	color_logger.workflow_start('RAG Services Initialization', db_session_id=id(db_session), config_provided=config is not None)

	try:
		workflow_config = config or WorkflowConfig.from_env()
		color_logger.info(
			f'📋 {Colors.BOLD}CONFIG:{Colors.RESET}{Colors.CYAN} WorkflowConfig loaded',
			Colors.CYAN,
			model_name=workflow_config.model_name,
			rag_enabled=workflow_config.rag_enabled,
			collection_name=workflow_config.collection_name,
		)

		qdrant_service = QdrantService(db_session)
		color_logger.success('QdrantService initialized', service_type='QdrantService', status='ready')

		query_optimizer = QueryOptimizer(workflow_config)
		color_logger.success(
			'QueryOptimizer initialized',
			service_type='QueryOptimizer',
			keywords_count=len(workflow_config.knowledge_keywords),
		)

		knowledge_retriever = KnowledgeRetriever(db_session, workflow_config)
		color_logger.success(
			'KnowledgeRetriever initialized',
			service_type='KnowledgeRetriever',
			threshold=workflow_config.similarity_threshold,
		)

		color_logger.workflow_complete(
			'RAG Services Initialization',
			time.time(),
			services_count=3,
			status='success',
		)
		return True
	except Exception as e:
		color_logger.error(
			f'Failed to initialize RAG services: {str(e)}',
			error_type=type(e).__name__,
			traceback_available=True,
		)
		return False


def should_use_rag(state):
	"""Determine if RAG should be used based on query"""
	color_logger.info(
		f'🤔 {Colors.BOLD}RAG_ANALYSIS:{Colors.RESET}{Colors.YELLOW} Starting decision process',
		Colors.YELLOW,
	)

	messages = state.get('messages', [])
	if not messages:
		color_logger.warning('No messages found in state', decision='skip_rag', reason='empty_messages')
		return 'skip_rag'

	# Get last user message
	last_message = None
	for msg in reversed(messages):
		if hasattr(msg, 'content') and msg.content:
			last_message = msg.content
			break

	if not last_message:
		color_logger.warning('No user message content found', decision='skip_rag', reason='no_content')
		return 'skip_rag'

	color_logger.info(
		f"📝 {Colors.BOLD}ANALYZING:{Colors.RESET}{Colors.BRIGHT_CYAN} '{last_message[:100]}...'",
		Colors.BRIGHT_CYAN,
		message_length=len(last_message),
	)

	# Check for knowledge-related keywords
	knowledge_keywords = [
		'tài chính',
		'thông tin',
		'giải thích',
		'là gì',
		'định nghĩa',
		'khái niệm',
		'cách',
		'làm sao',
		'tư vấn',
		'nên',
		'hướng dẫn',
		'quy định',
		'luật',
		'chính sách',
		'so sánh',
		'khác nhau',
	]

	matched_keywords = [kw for kw in knowledge_keywords if kw in last_message.lower()]
	need_rag = len(matched_keywords) > 0

	decision_factors = {
		'matched_keywords': matched_keywords,
		'keyword_count': len(matched_keywords),
		'message_length': len(last_message),
		'contains_question': any(q in last_message for q in ['?', 'gì', 'sao', 'nào']),
	}

	color_logger.rag_decision(
		need_rag,
		decision_factors,
		matched_keywords=len(matched_keywords),
		query_preview=last_message[:50],
	)

	return 'use_rag' if need_rag else 'skip_rag'


async def retrieve_knowledge(state, config):
	"""Retrieve relevant knowledge from QdrantDB"""
	start_time = time.time()
	color_logger.workflow_start(
		'Knowledge Retrieval',
		services_available=all([knowledge_retriever, query_optimizer]),
	)

	try:
		messages = state.get('messages', [])
		if not messages:
			color_logger.warning('No messages for retrieval', result='empty_context')
			return {'rag_context': None}

		# Get last user message
		user_message = None
		for msg in reversed(messages):
			if hasattr(msg, 'content') and msg.content:
				user_message = msg.content
				break

		if not user_message:
			color_logger.warning('No user message for retrieval', result='empty_context')
			return {'rag_context': None}

		color_logger.info(
			f"🔍 {Colors.BOLD}RETRIEVING:{Colors.RESET}{Colors.BRIGHT_BLUE} '{user_message[:50]}...'",
			Colors.BRIGHT_BLUE,
			query_length=len(user_message),
		)

		# Check if services are available
		if not knowledge_retriever or not query_optimizer:
			color_logger.error(
				'RAG services not available',
				knowledge_retriever_available=knowledge_retriever is not None,
				query_optimizer_available=query_optimizer is not None,
			)
			return {'rag_context': None}

		# Optimize queries
		optimized_queries = query_optimizer.optimize_queries(user_message)
		color_logger.query_optimization(
			user_message,
			len(optimized_queries),
			original_length=len(user_message),
			queries_generated=len(optimized_queries),
		)

		# Retrieve documents
		documents = await knowledge_retriever.retrieve_documents(queries=optimized_queries, top_k=5, score_threshold=0.7)

		# Calculate metrics
		avg_score = sum(doc.metadata.get('similarity_score', 0) for doc in documents) / len(documents) if documents else 0

		color_logger.knowledge_retrieval(
			len(optimized_queries),
			len(documents),
			avg_score,
			retrieval_time=time.time() - start_time,
			threshold_used=0.7,
		)

		# Format context
		if documents:
			rag_context = []
			for i, doc in enumerate(documents):
				score = doc.metadata.get('similarity_score', 0)
				context_text = f'Nguồn {i + 1} (score: {score:.3f}): {doc.page_content}'
				rag_context.append(context_text)

				color_logger.debug(
					f'Document {i + 1} retrieved',
					score=score,
					content_length=len(doc.page_content),
					preview=doc.page_content[:100],
				)

			color_logger.success(
				f'Knowledge retrieval completed',
				documents_count=len(documents),
				context_length=sum(len(ctx) for ctx in rag_context),
				avg_relevance=avg_score,
			)

			return {'rag_context': rag_context}
		else:
			color_logger.warning(
				'No relevant documents found',
				queries_tried=len(optimized_queries),
				threshold=0.7,
			)
			return {'rag_context': None}

	except Exception as e:
		color_logger.error(
			f'Knowledge retrieval failed: {str(e)}',
			error_type=type(e).__name__,
			processing_time=time.time() - start_time,
		)
		return {'rag_context': None}


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
	"""Call the language model with the current state and RAG context."""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
	print('=' * 100, config)
	color_logger.workflow_start(
		'Model Invocation',
		thread_id=thread_id,
		has_rag_context=bool(state.get('rag_context')),
	)

	# Get the system prompt from config
	system = config.get('configurable', {}).get('system_prompt', DEFAULT_SYSTEM_PROMPT)
	print(f'System prompt length: {system}')
	color_logger.info(
		f'📋 {Colors.BOLD}SYSTEM_PROMPT:{Colors.RESET}{Colors.CYAN} Loaded',
		Colors.CYAN,
		prompt_length=len(system),
		thread_id=thread_id,
	)

	# Add RAG context to system prompt if available
	rag_context = state.get('rag_context')
	if rag_context:
		context_length = sum(len(ctx) for ctx in rag_context)
		color_logger.info(
			f'🧠 {Colors.BOLD}RAG_CONTEXT:{Colors.RESET}{Colors.BRIGHT_YELLOW} Enhancing prompt',
			Colors.BRIGHT_YELLOW,
			sources_count=len(rag_context),
			total_context_length=context_length,
		)
		enhanced_system = f'{system}\n\nThông tin tham khảo từ cơ sở dữ liệu:\n' + '\n'.join(rag_context)
	else:
		color_logger.info(
			f'📝 {Colors.BOLD}NO_RAG:{Colors.RESET}{Colors.DIM} Using base prompt only',
			Colors.DIM,
		)
		enhanced_system = system

	# Prepare messages with enhanced system prompt and ChatPromptTemplate
	messages = state.get('messages', [])
	if not messages:
		color_logger.warning('No messages in state, creating system message', message_count=0)
		return {'messages': [SystemMessage(content=enhanced_system)]}

	# Create prompt template with system message and agent_scratchpad
	prompt = ChatPromptTemplate.from_messages([
		('system', enhanced_system),
		MessagesPlaceholder(variable_name='chat_history'),
		MessagesPlaceholder(variable_name='agent_scratchpad'),
	])

	# Format the prompt with the chat history
	formatted_prompt = prompt.format_messages(
		chat_history=messages,
		agent_scratchpad=[],
	)

	color_logger.info(
		f'💬 {Colors.BOLD}MESSAGES:{Colors.RESET}{Colors.BRIGHT_WHITE} Formatted for model',
		Colors.BRIGHT_WHITE,
		total_messages=len(formatted_prompt),
		chat_history_count=len(messages),
	)

	# Invoke model with tools
	color_logger.info(
		f'🤖 {Colors.BOLD}INVOKING:{Colors.RESET}{Colors.BRIGHT_BLUE} {model.__class__.__name__}',
		Colors.BRIGHT_BLUE,
		model_name=getattr(model, 'model', 'unknown'),
		tools_available=len(get_tool_defs(config)),
	)

	model_with_tools = model.bind_tools(get_tool_defs(config))
	response = await model_with_tools.ainvoke(
		formatted_prompt,
		{
			'system_time': datetime.now(tz=timezone.utc).isoformat(),
		},
	)

	# Estimate token usage
	total_chars = sum(len(str(msg.content)) for msg in formatted_prompt) + len(str(response.content))
	estimated_tokens = total_chars // 4  # Rough estimate for Vietnamese

	processing_time = time.time() - start_time
	color_logger.model_invocation(
		getattr(model, 'model', 'unknown'),
		estimated_tokens,
		processing_time=processing_time,
		response_length=len(str(response.content)),
		has_tool_calls=hasattr(response, 'tool_calls') and bool(response.tool_calls),
	)

	color_logger.workflow_complete(
		'Model Invocation',
		processing_time,
		response_generated=True,
		thread_id=thread_id,
	)

	# Return the response to be added to the messages
	return {'messages': response}


async def run_tools(input, config, **kwargs):
	"""Execute tools based on the model's response."""
	start_time = time.time()
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')

	color_logger.workflow_start('Tool Execution', thread_id=thread_id, available_tools=len(get_tools(config)))

	# Extract tool calls from messages
	messages = input.get('messages', [])
	tool_calls = []
	if messages:
		last_message = messages[-1]
		if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
			tool_calls = last_message.tool_calls
			tool_names = [tc.get('name', 'unknown') for tc in tool_calls]

			color_logger.info(
				f'🔧 {Colors.BOLD}TOOL_CALLS:{Colors.RESET}{Colors.YELLOW} Detected',
				Colors.YELLOW,
				tool_count=len(tool_calls),
				tool_names=tool_names,
			)

	tool_node = ToolNode(get_tools(config))
	response = await tool_node.ainvoke(input, config, **kwargs)

	processing_time = time.time() - start_time
	tool_names = [tc.get('name', 'unknown') for tc in tool_calls] if tool_calls else []

	color_logger.tool_execution(
		tool_names,
		processing_time,
		thread_id=thread_id,
		results_count=len(response.get('messages', [])),
	)

	color_logger.workflow_complete(
		'Tool Execution',
		processing_time,
		tools_executed=len(tool_names),
		thread_id=thread_id,
	)

	return response


def create_workflow_with_rag(db_session, config=None):
	"""Create workflow with RAG functionality"""
	color_logger.workflow_start(
		'Workflow Creation',
		rag_enabled=True,
		db_session_provided=db_session is not None,
	)

	# Initialize services
	services_ready = initialize_services(db_session, config)

	color_logger.info(
		f'🔧 {Colors.BOLD}SERVICES:{Colors.RESET}{Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED} {"Ready" if services_ready else "Failed"}',
		Colors.BRIGHT_GREEN if services_ready else Colors.BRIGHT_RED,
		qdrant_available=qdrant_service is not None,
		optimizer_available=query_optimizer is not None,
		retriever_available=knowledge_retriever is not None,
	)

	# Define the workflow with RAG
	workflow = StateGraph(AgentState)

	# Add nodes
	workflow.add_node('rag_decision', lambda state: {'need_rag': should_use_rag(state) == 'use_rag'})
	workflow.add_node('retrieve', retrieve_knowledge)
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

	color_logger.info(
		f'📊 {Colors.BOLD}NODES:{Colors.RESET}{Colors.MAGENTA} Workflow nodes added',
		Colors.MAGENTA,
		node_count=4,
		nodes=['rag_decision', 'retrieve', 'agent', 'tools'],
	)

	# Set up the graph flow
	workflow.set_entry_point('rag_decision')

	# Conditional RAG flow
	workflow.add_conditional_edges(
		'rag_decision',
		lambda state: 'use_rag' if state.get('need_rag', False) else 'skip_rag',
		{'use_rag': 'retrieve', 'skip_rag': 'agent'},
	)

	# RAG flow
	workflow.add_edge('retrieve', 'agent')

	# Tool handling
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	color_logger.info(
		f'🔗 {Colors.BOLD}EDGES:{Colors.RESET}{Colors.CYAN} Workflow connections established',
		Colors.CYAN,
		conditional_edges=2,
		regular_edges=2,
		entry_point='rag_decision',
	)

	# Compile graph with memory checkpointer
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	color_logger.workflow_complete(
		'Workflow Creation',
		time.time(),
		rag_enabled=services_ready,
		memory_checkpointer=True,
		compilation_successful=True,
	)

	return compiled_workflow


# For backward compatibility, create basic workflow without RAG
workflow = StateGraph(AgentState)

# Add nodes for the basic agent
workflow.add_node('agent', call_model)
workflow.add_node('tools', run_tools)

# Set up the graph flow
workflow.set_entry_point('agent')

# Handle tools and end conditions
workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
workflow.add_edge('tools', 'agent')

# Compile graph with memory checkpointer
memory = MemorySaver()
basic_workflow = workflow.compile(checkpointer=memory)
