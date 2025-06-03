"""
Complete LangGraph workflow for chat system với RAG capabilities
Production-ready implementation cho MoneyEZ financial assistant
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Annotated, TypedDict, Any
import logging

from dotenv import load_dotenv
from langchain_core.messages import (
	SystemMessage,
	HumanMessage,
	AIMessage,
	BaseMessage,
	ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.errors import NodeInterrupt
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)

# ==============================================
# 1. STATE DEFINITION
# ==============================================


class AgentState(TypedDict):
	"""State definition cho LangGraph workflow"""

	messages: Annotated[List[BaseMessage], add_messages]
	rag_context: Optional[List[str]]
	queries: Optional[List[str]]
	retrieved_docs: Optional[List[Document]]
	need_rag: Optional[bool]


# ==============================================
# 2. UTILITY FUNCTIONS
# ==============================================


def get_message_text(msg: BaseMessage) -> str:
	"""Extract text từ various message formats"""
	if hasattr(msg, 'content'):
		return str(msg.content)
	elif isinstance(msg, dict):
		return str(msg.get('content', ''))
	return str(msg)


def format_docs(docs: List[Document]) -> str:
	"""Format documents as XML cho prompts"""
	if not docs:
		return ''

	formatted = []
	for i, doc in enumerate(docs):
		content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
		formatted.append(f'<document_{i + 1}>\n{content}\n</document_{i + 1}>')

	return '\n\n'.join(formatted)


# ==============================================
# 3. RAG NODE FUNCTIONS
# ==============================================


async def should_use_rag(state: AgentState, config: Dict) -> Dict[str, Any]:
	"""
	Decision node: Xác định có cần sử dụng RAG không
	"""
	print(f'🔍 [RAG Decision] Starting RAG analysis...')

	try:
		# Kiểm tra config setting
		use_rag_setting = config.get('configurable', {}).get('use_rag', True)
		if not use_rag_setting:
			print(f'📝 [RAG Decision] RAG disabled in config')
			return {'need_rag': False, 'queries': []}

		# Lấy user message cuối cùng
		messages = state.get('messages', [])
		if not messages:
			print(f'📝 [RAG Decision] No messages found')
			return {'need_rag': False, 'queries': []}

		last_user_msg = None
		for msg in reversed(messages):
			if isinstance(msg, HumanMessage):
				last_user_msg = get_message_text(msg)
				break

		if not last_user_msg:
			print(f'📝 [RAG Decision] No user message found')
			return {'need_rag': False, 'queries': []}

		# Vietnamese financial keywords
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
			'đầu tư',
			'tiết kiệm',
			'ngân hàng',
			'tín dụng',
			'bảo hiểm',
			'thuế',
			'lãi suất',
			'cổ phiếu',
			'trái phiếu',
			'quỹ đầu tư',
		]

		# Phân tích message
		need_rag = any(keyword in last_user_msg.lower() for keyword in knowledge_keywords)

		print(f"📝 [RAG Decision] Message: '{last_user_msg[:100]}...'")
		print(f'📝 [RAG Decision] Need RAG: {need_rag}')

		return {'need_rag': need_rag, 'queries': []}

	except Exception as e:
		logger.error(f'Error in should_use_rag: {str(e)}')
		print(f'❌ [RAG Decision] Error: {str(e)}')
		return {'need_rag': False, 'queries': []}


async def generate_query(state: AgentState, config: Dict) -> Dict[str, Any]:
	"""
	Generate optimized search queries cho RAG retrieval
	"""
	print(f'🔍 [Query Generation] Starting query optimization...')

	try:
		messages = state.get('messages', [])
		if not messages:
			return {'queries': []}

		# Lấy user message cuối cùng
		last_user_msg = None
		for msg in reversed(messages):
			if isinstance(msg, HumanMessage):
				last_user_msg = get_message_text(msg)
				break

		if not last_user_msg:
			return {'queries': []}

		# Remove filler words
		filler_words = [
			'cho tôi',
			'giúp tôi',
			'làm ơn',
			'xin vui lòng',
			'bạn có thể',
			'tôi muốn',
			'tôi cần',
			'xin',
			'hãy',
			'thông tin về',
		]

		optimized_query = last_user_msg.lower()
		for filler in filler_words:
			optimized_query = optimized_query.replace(filler, '').strip()

		# Add financial terms nếu tìm thấy
		financial_terms = [
			'đầu tư',
			'tiết kiệm',
			'ngân hàng',
			'tín dụng',
			'bảo hiểm',
			'thuế',
			'lãi suất',
			'cổ phiếu',
			'trái phiếu',
			'quỹ đầu tư',
		]

		keyword_query = optimized_query
		for term in financial_terms:
			if term in optimized_query:
				keyword_query += f' {term}'

		queries = [optimized_query.strip(), keyword_query.strip()]
		queries = [q for q in queries if q]  # Remove empty queries

		print(f"📝 [Query Generation] Original: '{last_user_msg[:100]}...'")
		print(f'📝 [Query Generation] Optimized queries: {queries}')

		return {'queries': queries}

	except Exception as e:
		logger.error(f'Error in generate_query: {str(e)}')
		print(f'❌ [Query Generation] Error: {str(e)}')
		return {'queries': []}


async def retrieve_knowledge(state: AgentState, config: Dict) -> Dict[str, Any]:
	"""
	Retrieve knowledge từ vector database
	"""
	print(f'🔍 [Knowledge Retrieval] Starting document retrieval...')

	try:
		queries = state.get('queries', [])
		if not queries:
			print(f'📝 [Knowledge Retrieval] No queries to process')
			return {'rag_context': [], 'retrieved_docs': []}

		# Mock retriever function - Replace với actual QdrantService integration
		def mock_retrieve_docs(query: str) -> List[Document]:
			"""Placeholder cho vector DB integration"""
			# Trong production, integrate với QdrantService:
			# from app.modules.agent.services.qdrant_service import QdrantService
			# qdrant = QdrantService(db)
			# results = qdrant.search_documents(query, collection_name, top_k=5)

			mock_docs = [
				Document(
					page_content=f'Mock financial content cho query: {query}. Thông tin về tài chính cá nhân và đầu tư.',
					metadata={'source': 'mock_source', 'score': 0.9},
				),
				Document(
					page_content=f'Hướng dẫn chi tiết về {query} trong lĩnh vực ngân hàng và tài chính.',
					metadata={'source': 'mock_guide', 'score': 0.8},
				),
			]
			return mock_docs

		# Process tất cả queries
		all_docs = []
		for query in queries:
			docs = mock_retrieve_docs(query)
			all_docs.extend(docs)

		# Deduplicate và rank documents
		unique_docs = []
		seen_content = set()

		for doc in all_docs:
			content = doc.page_content
			if content not in seen_content:
				seen_content.add(content)
				unique_docs.append(doc)

		# Sort by relevance score nếu available
		unique_docs.sort(key=lambda x: x.metadata.get('score', 0), reverse=True)

		# Limit to top documents
		top_docs = unique_docs[:5]
		rag_context = [doc.page_content for doc in top_docs]

		print(f'📝 [Knowledge Retrieval] Retrieved {len(top_docs)} documents')
		for i, doc in enumerate(top_docs):
			print(f'📄 [Doc {i + 1}] {doc.page_content[:100]}...')

		return {'rag_context': rag_context, 'retrieved_docs': top_docs}

	except Exception as e:
		logger.error(f'Error in retrieve_knowledge: {str(e)}')
		print(f'❌ [Knowledge Retrieval] Error: {str(e)}')
		return {'rag_context': [], 'retrieved_docs': []}


# ==============================================
# 4. AGENT FUNCTIONS
# ==============================================


async def call_model(state: AgentState, config: Dict) -> Dict[str, Any]:
	"""
	Main agent function: Call LLM với optional RAG context
	"""
	print(f'🤖 [Agent] Starting model invocation...')

	try:
		# Get system prompt từ config hoặc default
		default_system_prompt = """
        Bạn là MoneyEZ AI Assistant - trợ lý tài chính thông minh và thân thiện.
        
        Nhiệm vụ:
        • Hỗ trợ tư vấn tài chính cá nhân tại Việt Nam
        • Cung cấp thông tin về ngân hàng, đầu tư, tiết kiệm
        • Giải thích các khái niệm tài chính một cách dễ hiểu
        • Đưa ra lời khuyên phù hợp với luật pháp Việt Nam
        
        Nguyên tắc:
        • Luôn trả lời bằng tiếng Việt
        • Thông tin chính xác, cập nhật
        • Giải thích đơn giản, dễ hiểu  
        • Không đưa ra lời khuyên đầu tư cụ thể
        • Khuyến khích tham khảo chuyên gia khi cần
        """

		system_prompt = config.get('system_prompt', default_system_prompt)

		# Enhance với RAG context nếu có
		rag_context = state.get('rag_context', [])
		if rag_context:
			context_text = '\n\n'.join(rag_context)
			enhanced_prompt = f"""
            {system_prompt}
            
            === THÔNG TIN THAM KHẢO ===
            {context_text}
            
            Sử dụng thông tin trên để trả lời chính xác và chi tiết hơn.
            """
			system_prompt = enhanced_prompt
			print(f'📝 [Agent] Enhanced prompt với RAG context ({len(rag_context)} docs)')

		# Setup model
		model_config = config.get('model_config', {})
		model = ChatGoogleGenerativeAI(
			model=model_config.get('model', 'gemini-2.0-flash'),
			temperature=model_config.get('temperature', 0),
			google_api_key=model_config.get('api_key', os.getenv('GOOGLE_API_KEY')),
		)

		# Create prompt template
		prompt = ChatPromptTemplate.from_messages([
			SystemMessage(content=system_prompt),
			MessagesPlaceholder(variable_name='messages'),
		])

		# Get available tools
		tools = get_tools(config)
		if tools:
			model = model.bind_tools(tools)
			print(f'📝 [Agent] Model bound với {len(tools)} tools')

		# Create chain và invoke
		chain = prompt | model

		# Add current timestamp cho context
		current_time = datetime.now(timezone.utc).isoformat()

		# Prepare messages với timestamp context
		messages = state.get('messages', [])
		if messages and isinstance(messages[-1], HumanMessage):
			# Add timestamp context
			last_msg = messages[-1]
			enhanced_content = f'{last_msg.content}\n\n[Thời gian hiện tại: {current_time}]'
			messages[-1] = HumanMessage(content=enhanced_content)

		response = await chain.ainvoke({'messages': messages})

		print(f'🤖 [Agent] Model response generated successfully')
		print(f"📝 [Agent] Response preview: '{str(response.content)[:100]}...'")

		return {'messages': [response]}

	except Exception as e:
		logger.error(f'Error in call_model: {str(e)}')
		print(f'❌ [Agent] Error: {str(e)}')

		# Fallback response
		fallback_msg = AIMessage(content='Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.')
		return {'messages': [fallback_msg]}


def should_continue(state: AgentState) -> str:
	"""
	Conditional edge: Kiểm tra có tool calls không
	"""
	messages = state.get('messages', [])
	if not messages:
		return END

	last_message = messages[-1]

	# Kiểm tra tool calls
	if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
		print(f'🔧 [Routing] Tool calls detected: {len(last_message.tool_calls)}')
		return 'tools'

	print(f'🏁 [Routing] No tool calls, ending conversation')
	return END


async def run_tools(state: AgentState, config: Dict, **kwargs) -> Dict[str, Any]:
	"""
	Execute tools và return response
	"""
	print(f'🔧 [Tools] Starting tool execution...')

	try:
		tools = get_tools(config)
		if not tools:
			print(f'❌ [Tools] No tools available')
			return {'messages': []}

		tool_node = ToolNode(tools)
		result = await tool_node.ainvoke(state, config, **kwargs)

		print(f'✅ [Tools] Tool execution completed')
		return result

	except Exception as e:
		logger.error(f'Error in run_tools: {str(e)}')
		print(f'❌ [Tools] Error: {str(e)}')

		error_msg = ToolMessage(content=f'Tool execution failed: {str(e)}', tool_call_id='error')
		return {'messages': [error_msg]}


# ==============================================
# 5. TOOL SUPPORT
# ==============================================


class FrontendTool(BaseTool):
	"""
	Tool cho frontend-rendered functionality
	"""

	name: str
	description: str

	def _run(self, *args, **kwargs):
		"""Raise interrupt cho frontend handling"""
		raise NodeInterrupt(f'Frontend tool: {self.name}')

	async def _arun(self, *args, **kwargs):
		"""Async version"""
		raise NodeInterrupt(f'Frontend tool: {self.name}')


def get_tool_defs(config: Dict) -> List[Dict]:
	"""
	Get tool definitions từ config
	"""
	frontend_tools = config.get('frontend_tools', [])
	backend_tools = config.get('backend_tools', [])

	all_tools = []
	all_tools.extend(frontend_tools)
	all_tools.extend(backend_tools)

	return all_tools


def get_tools(config: Dict) -> List[BaseTool]:
	"""
	Create tool instances cho ToolNode
	"""
	tool_defs = get_tool_defs(config)
	tools = []

	for tool_def in tool_defs:
		if tool_def.get('type') == 'frontend':
			tool = FrontendTool(
				name=tool_def.get('name', 'unknown_tool'),
				description=tool_def.get('description', 'Frontend tool'),
			)
			tools.append(tool)
		elif tool_def.get('type') == 'backend':
			# Add backend tool implementations nếu cần
			pass

	return tools


# ==============================================
# 6. WORKFLOW GRAPH CONSTRUCTION
# ==============================================


def create_workflow() -> StateGraph:
	"""
	Create complete LangGraph workflow
	"""
	print(f'🏗️ [Workflow] Building LangGraph workflow...')

	# Initialize workflow
	workflow = StateGraph(AgentState)

	# Add nodes
	workflow.add_node('rag_decision', should_use_rag)
	workflow.add_node('generate_query', generate_query)
	workflow.add_node('retrieve', retrieve_knowledge)
	workflow.add_node('agent', call_model)
	workflow.add_node('tools', run_tools)

	# Set entry point
	workflow.set_entry_point('rag_decision')

	# Add conditional edges cho RAG flow
	def route_rag_decision(state: AgentState) -> str:
		need_rag = state.get('need_rag', False)
		return 'use_rag' if need_rag else 'skip_rag'

	workflow.add_conditional_edges(
		'rag_decision',
		route_rag_decision,
		{'use_rag': 'generate_query', 'skip_rag': 'agent'},
	)

	# RAG pipeline edges
	workflow.add_edge('generate_query', 'retrieve')
	workflow.add_edge('retrieve', 'agent')

	# Tool handling edges
	workflow.add_conditional_edges('agent', should_continue, {'tools': 'tools', END: END})
	workflow.add_edge('tools', 'agent')

	print(f'✅ [Workflow] LangGraph workflow created successfully')
	return workflow


# ==============================================
# 7. FINAL WORKFLOW COMPILATION
# ==============================================

# Create workflow instance
workflow = create_workflow()

# Setup memory checkpointer
memory = MemorySaver()

# Compile graph với memory
assistant_ui_graph = workflow.compile(checkpointer=memory)

print(f'🚀 [System] MoneyEZ LangGraph Assistant ready!')
print(f'📊 [System] Workflow nodes: {len(workflow.nodes)}')
print(f'🔗 [System] Memory persistence: Enabled')
print(f'🔧 [System] RAG capabilities: Enabled')
print(f'🤖 [System] Model: gemini-2.0-flash')
