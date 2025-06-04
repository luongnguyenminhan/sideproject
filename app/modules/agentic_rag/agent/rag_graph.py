"""
LangGraph implementation for Agentic RAG workflows.
"""

import uuid
import logging
from typing import Dict, List, Any, TypedDict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException
from app.core.config import GOOGLE_API_KEY
from app.modules.agentic_rag.repositories.kb_repo import KBRepository

logger = logging.getLogger(__name__)


# Color codes for logging
class LogColors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'


class AgentState(TypedDict):
	"""State for the Agentic RAG workflow."""

	query: str
	retrieved_documents: List[Document]
	answer: Optional[str]
	sources: List[Dict[str, Any]]
	messages: List[Any]
	error: Optional[str]


class RAGAgentGraph:
	"""LangGraph-based agent for RAG operations."""

	def __init__(self, kb_repo: Optional[KBRepository] = None) -> None:
		"""Initialize the RAG agent graph."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph] Initializing LangGraph-based RAG agent{LogColors.ENDC}')

		self.kb_repo = kb_repo or KBRepository()
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] KB repository established{LogColors.ENDC}')

		try:
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Initializing ChatGoogleGenerativeAI for agent workflow{LogColors.ENDC}')
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] ChatGoogleGenerativeAI initialized successfully{LogColors.ENDC}')
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph] Error initializing LLM: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Setting up memory saver for state management{LogColors.ENDC}')
		self.memory = MemorySaver()  # In-memory checkpointer for state

		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Building workflow graph{LogColors.ENDC}')
		self.workflow = self._build_graph()
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] RAG agent graph initialized successfully{LogColors.ENDC}')

	async def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
		"""Retrieve relevant documents based on the query."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-RetrievalNode] Starting document retrieval process{LogColors.ENDC}')

		# Get the user query
		query = state.get('query', '')
		if not query:
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-RetrievalNode] No query provided in state{LogColors.ENDC}')
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}

		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-RetrievalNode] Processing query: "{query[:100]}..."{LogColors.ENDC}')

		try:
			# Retrieve documents using the KB repository
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-RetrievalNode] Executing document retrieval via KB repository{LogColors.ENDC}')
			from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

			# Use simpler approach for LangGraph integration
			query_response = await self.kb_repo.query(QueryRequest(query=query, top_k=5))
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-RetrievalNode] KB query completed - Found {len(query_response.results)} results{LogColors.ENDC}')

			# Convert to Document objects
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-RetrievalNode] Converting query results to Document objects{LogColors.ENDC}')
			retrieved_docs = []
			for i, item in enumerate(query_response.results):
				doc = Document(
					page_content=item.content,
					metadata=item.metadata,
				)
				retrieved_docs.append(doc)
				logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-RetrievalNode] Document {i + 1} converted - ID: {item.id}, Content length: {len(item.content)}, Score: {item.score}{LogColors.ENDC}')

			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-RetrievalNode] Document retrieval completed successfully - Retrieved {len(retrieved_docs)} documents{LogColors.ENDC}')
			return {
				'retrieved_documents': retrieved_docs,
				'messages': state.get('messages', []) + [AIMessage(content=f'Retrieved {len(retrieved_docs)} documents')],
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph-RetrievalNode] Error during document retrieval: {e}{LogColors.ENDC}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error retrieving documents: {e}')],
			}

	async def _generation_node(self, state: AgentState) -> Dict[str, Any]:
		"""Generate an answer based on retrieved documents."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-GenerationNode] Starting answer generation process{LogColors.ENDC}')

		# Check if we have an error or documents
		if state.get('error'):
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-GenerationNode] Error detected in state, skipping generation{LogColors.ENDC}')
			return state

		docs = state.get('retrieved_documents', [])
		if not docs:
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-GenerationNode] No documents found for generation{LogColors.ENDC}')
			return {
				'answer': "I don't have enough information to answer this question based on the available knowledge.",
				'sources': [],
				'messages': state.get('messages', []) + [AIMessage(content='No relevant information found for this query.')],
			}

		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-GenerationNode] Processing {len(docs)} documents for context preparation{LogColors.ENDC}')

		# Prepare context from retrieved documents
		context_parts = []
		for i, doc in enumerate(docs):
			doc_id = getattr(doc, 'id', f'doc_{i}')
			context_part = f'Document {i + 1} (ID: {doc_id}):\n{doc.page_content}'
			context_parts.append(context_part)
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-GenerationNode] Document {i + 1} added to context - ID: {doc_id}, Length: {len(doc.page_content)}{LogColors.ENDC}')

		context = '\n\n'.join(context_parts)
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] Context prepared - Total length: {len(context)} characters{LogColors.ENDC}')

		# Define the generation prompt
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-GenerationNode] Setting up generation prompt template{LogColors.ENDC}')
		template = """You are a helpful and precise assistant. Use the following context to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Always provide a detailed and comprehensive answer based only on the context provided.
        Include citations in your answer when you use information from specific documents.
        
        Context:
        {context}
        
        Question: {question}
        
        Helpful Answer:"""

		prompt = PromptTemplate(input_variables=['context', 'question'], template=template)
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-GenerationNode] Prompt template configured{LogColors.ENDC}')

		try:
			# Prepare the prompt inputs
			query = state.get('query', '')
			prompt_inputs = {'context': context, 'question': query}
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-GenerationNode] Prompt inputs prepared for query: "{query[:50]}..."{LogColors.ENDC}')

			# Invoke the LLM
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-GenerationNode] Creating and invoking LLM chain{LogColors.ENDC}')
			from langchain.chains import LLMChain

			chain = LLMChain(llm=self.llm, prompt=prompt)
			result = chain.invoke(prompt_inputs)
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] LLM chain invocation completed{LogColors.ENDC}')

			# Extract the answer
			answer = result.get('text', '')
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] Answer generated - Length: {len(answer)} characters{LogColors.ENDC}')

			# Prepare source information for each document
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-GenerationNode] Preparing source information for {len(docs)} documents{LogColors.ENDC}')
			sources = []
			for i, doc in enumerate(docs):
				doc_id = getattr(doc, 'id', 'unknown')
				doc_score = getattr(doc, 'score', 0.0)
				source = {
					'id': doc_id,
					'content': (doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content),
					'score': doc_score,
					'metadata': doc.metadata or {},
				}
				sources.append(source)
				logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-GenerationNode] Source {i + 1} prepared - ID: {doc_id}, Score: {doc_score:.4f}{LogColors.ENDC}')

			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] Answer generation completed successfully with {len(sources)} sources{LogColors.ENDC}')
			return {
				'answer': answer,
				'sources': sources,
				'messages': state.get('messages', []) + [AIMessage(content=answer)],
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph-GenerationNode] Error during answer generation: {e}{LogColors.ENDC}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error generating answer: {e}')],
			}

	def _should_end(self, state: AgentState) -> bool:
		"""Determine if the workflow should end."""
		has_answer = bool(state.get('answer'))
		has_error = bool(state.get('error'))
		should_end = has_answer or has_error

		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-ShouldEnd] Workflow end condition check - Answer: {has_answer}, Error: {has_error}, Should End: {should_end}{LogColors.ENDC}')
		return should_end

	def _build_graph(self) -> StateGraph:
		"""Construct the LangGraph StateGraph for the RAG workflow."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-BuildGraph] Constructing workflow graph{LogColors.ENDC}')

		# Define the graph
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-BuildGraph] Creating StateGraph with AgentState{LogColors.ENDC}')
		graph = StateGraph(AgentState)

		# Add nodes
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding retrieval node to graph{LogColors.ENDC}')
		graph.add_node('retrieval', self._retrieval_node)

		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding generation node to graph{LogColors.ENDC}')
		graph.add_node('generation', self._generation_node)

		# Define the edges
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-BuildGraph] Setting up graph edges{LogColors.ENDC}')
		graph.add_edge('retrieval', 'generation')

		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding conditional edges for workflow termination{LogColors.ENDC}')
		graph.add_conditional_edges(
			'generation',
			self._should_end,
			{
				True: END,
				False: 'retrieval',  # We could loop back for refinement, but for now we'll end
			},
		)

		# Set the entry point
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-BuildGraph] Setting retrieval as entry point{LogColors.ENDC}')
		graph.set_entry_point('retrieval')

		# Compile the graph
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Compiling workflow graph{LogColors.ENDC}')
		compiled_graph = graph.compile()
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-BuildGraph] Workflow graph construction completed{LogColors.ENDC}')

		return compiled_graph

	async def answer_query(self, query: str) -> Dict[str, Any]:
		"""Process a query and return the answer with sources."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph] Processing query through workflow: "{query[:100]}..."{LogColors.ENDC}')

		try:
			# Initialize the state
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Initializing workflow state{LogColors.ENDC}')
			state = {
				'query': query,
				'retrieved_documents': [],
				'answer': None,
				'sources': [],
				'messages': [
					SystemMessage(content='RAG Agent'),
					HumanMessage(content=query),
				],
				'error': None,
			}
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Workflow state initialized with query and system messages{LogColors.ENDC}')

			# Create a new session for this execution
			session_id = str(uuid.uuid4())
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Created workflow session: {session_id}{LogColors.ENDC}')

			# Execute the workflow
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Executing workflow with session: {session_id}{LogColors.ENDC}')
			result = await self.workflow.ainvoke(state, config={'configurable': {'session_id': session_id}})
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] Workflow execution completed for session: {session_id}{LogColors.ENDC}')

			# Check if we got an error
			if result.get('error'):
				logger.info(f'{LogColors.WARNING}[RAGAgentGraph] Workflow completed with error: {result["error"]}{LogColors.ENDC}')
				raise Exception(result['error'])

			# Return the results
			answer = result.get('answer', '')
			sources = result.get('sources', [])
			messages = result.get('messages', [])

			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] Query processing completed successfully - Answer length: {len(answer)}, Sources: {len(sources)}, Messages: {len(messages)}{LogColors.ENDC}')

			return {
				'answer': answer,
				'sources': sources,
				'conversation': [msg.content for msg in messages],
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph] Critical error during query processing: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
