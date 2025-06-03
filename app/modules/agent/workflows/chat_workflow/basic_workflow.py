"""
Basic Chat Workflow with integrated RAG functionality
Simple workflow with basic calculation tools + knowledge retrieval
"""

from datetime import datetime, timezone
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

load_dotenv()

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
model = ChatGoogleGenerativeAI(model='gemini-2.0-flash', temperature=0)

# Global services - will be initialized when workflow is created
qdrant_service = None
query_optimizer = None
knowledge_retriever = None
workflow_config = None


def initialize_services(db_session, config=None):
	"""Initialize RAG services"""
	global qdrant_service, query_optimizer, knowledge_retriever, workflow_config

	try:
		workflow_config = config or WorkflowConfig.from_env()
		qdrant_service = QdrantService(db_session)
		query_optimizer = QueryOptimizer(workflow_config)
		knowledge_retriever = KnowledgeRetriever(db_session, workflow_config)
		print('[RAG] Services initialized successfully')
		return True
	except Exception as e:
		print(f'[RAG] Failed to initialize services: {str(e)}')
		return False


def should_use_rag(state):
	"""Determine if RAG should be used based on query"""
	messages = state.get('messages', [])
	if not messages:
		return 'skip_rag'

	# Get last user message
	last_message = None
	for msg in reversed(messages):
		if hasattr(msg, 'content') and msg.content:
			last_message = msg.content
			break

	if not last_message:
		return 'skip_rag'

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

	need_rag = any(keyword in last_message.lower() for keyword in knowledge_keywords)

	print(f"[RAG] RAG decision: {'use_rag' if need_rag else 'skip_rag'} for query: '{last_message[:50]}...'")
	return 'use_rag' if need_rag else 'skip_rag'


async def retrieve_knowledge(state, config):
	"""Retrieve relevant knowledge from QdrantDB"""
	try:
		messages = state.get('messages', [])
		if not messages:
			return {'rag_context': None}

		# Get last user message
		user_message = None
		for msg in reversed(messages):
			if hasattr(msg, 'content') and msg.content:
				user_message = msg.content
				break

		if not user_message:
			return {'rag_context': None}

		print(f"[RAG] Retrieving knowledge for: '{user_message[:50]}...'")

		# Check if services are available
		if not knowledge_retriever or not query_optimizer:
			print('[RAG] Services not available, skipping RAG')
			return {'rag_context': None}

		# Optimize queries
		optimized_queries = query_optimizer.optimize_queries(user_message)
		print(f'[RAG] Generated {len(optimized_queries)} optimized queries')

		# Retrieve documents
		documents = await knowledge_retriever.retrieve_documents(queries=optimized_queries, top_k=5, score_threshold=0.7)

		# Format context
		if documents:
			rag_context = []
			for doc in documents:
				context_text = f'Nguồn: {doc.page_content}'
				rag_context.append(context_text)

			print(f'[RAG] Retrieved {len(documents)} relevant documents')
			return {'rag_context': rag_context}
		else:
			print('[RAG] No relevant documents found')
			return {'rag_context': None}

	except Exception as e:
		print(f'[RAG] Error retrieving knowledge: {str(e)}')
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
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
	print(f'\n[AGENT] Calling model for thread: {thread_id}')

	# Get the system prompt from config
	system = config.get('configurable', {}).get('system_prompt', DEFAULT_SYSTEM_PROMPT)
	print(f'[AGENT] Using system prompt: {system}...')
	# Add RAG context to system prompt if available
	rag_context = state.get('rag_context')
	if rag_context:
		print(f'[AGENT] Using RAG context with {len(rag_context)} sources')
		enhanced_system = f'{system}\n\nThông tin tham khảo từ cơ sở dữ liệu:\n' + '\n'.join(rag_context)
	else:
		print('[AGENT] No RAG context available')
		enhanced_system = system

	print(f'[AGENT] System prompt enhanced: {len(enhanced_system)} characters')

	# Prepare messages with enhanced system prompt and ChatPromptTemplate
	messages = state.get('messages', [])
	if not messages:
		# Handle the case when messages is empty
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
		agent_scratchpad=[],  # This can be used for agent's intermediate reasoning if needed
	)

	print(f'[AGENT] Total messages in context: {len(formatted_prompt)}')

	# Invoke model with tools
	print(f'[AGENT] Invoking model')
	model_with_tools = model.bind_tools(get_tool_defs(config))
	response = await model_with_tools.ainvoke(
		formatted_prompt,
		{
			'system_time': datetime.now(tz=timezone.utc).isoformat(),
		},
	)

	# Return the response to be added to the messages
	return {'messages': response}


async def run_tools(input, config, **kwargs):
	"""Execute tools based on the model's response."""
	thread_id = config.get('configurable', {}).get('thread_id', 'unknown')
	print(f'\n[TOOLS] Running tools for thread: {thread_id}')

	tool_node = ToolNode(get_tools(config))
	response = await tool_node.ainvoke(input, config, **kwargs)

	print(f'[TOOLS] Tool response received')
	return response


def create_workflow_with_rag(db_session, config=None):
	"""Create workflow with RAG functionality"""

	# Initialize services
	services_ready = initialize_services(db_session, config)

	# Define the workflow with RAG
	workflow = StateGraph(AgentState)

	# Add nodes
	workflow.add_node('rag_decision', lambda state: {'need_rag': should_use_rag(state) == 'use_rag'})
	workflow.add_node('retrieve', retrieve_knowledge)
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

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

	# Compile graph with memory checkpointer
	memory = MemorySaver()
	compiled_workflow = workflow.compile(checkpointer=memory)

	print(f'[WORKFLOW] Compiled workflow with RAG {"enabled" if services_ready else "disabled"}')
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
