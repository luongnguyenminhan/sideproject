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
from app.modules.agentic_rag.repository.kb_repo import KBRepository
from app.modules.agentic_rag.core.config import DEFAULT_COLLECTION

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
	collection_id: str
	retrieved_documents: List[Document]
	answer: Optional[str]
	sources: List[Dict[str, Any]]
	messages: List[Any]
	error: Optional[str]
	plans: Optional[List[str]]  # <-- Add plans to state
	current_plan_index: Optional[int]  # <-- Track which plan is being processed
	all_contexts: Optional[List[str]]  # <-- Store all contexts for aggregation
	plan_loop_count: Optional[int]  # <-- Add loop counter


class RAGAgentGraph:
	"""LangGraph-based agent for RAG operations."""

	def __init__(self, kb_repo: Optional[KBRepository] = None, collection_id: str = None) -> None:
		"""Initialize the RAG agent graph."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph] Initializing LangGraph-based RAG agent{LogColors.ENDC}')

		self.collection_id = collection_id or DEFAULT_COLLECTION
		self.kb_repo = kb_repo or KBRepository(collection_name=self.collection_id)
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] KB repository established for collection: {self.collection_id}{LogColors.ENDC}')

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

		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Building workflow graph for collection: {self.collection_id}{LogColors.ENDC}')
		self.workflow = self._build_graph()
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] RAG agent graph initialized successfully for collection: {self.collection_id}{LogColors.ENDC}')

	async def _planning_node(self, state: AgentState) -> Dict[str, Any]:
		"""Plan a list of sub-queries to maximize information retrieval."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-PlanningNode] Starting planning process{LogColors.ENDC}')
		query = state.get('query', '')
		collection_id = state.get('collection_id', self.collection_id)

		if not query:
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-PlanningNode] No query provided for planning{LogColors.ENDC}')
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}

		# Use LLM to generate a list of sub-queries (plans) with structured output
		from pydantic import BaseModel, Field

		class PlanningOutput(BaseModel):
			sub_queries: list[str] = Field(..., description='A list of focused sub-questions or search queries.')

		planning_prompt = PromptTemplate(
			input_variables=['question'],
			template=("You are an expert assistant. Given the following user question, break it down into a list of 2-5 focused sub-questions or search queries that, if answered, would help provide the most comprehensive and informative answer. Return only the list as a JSON array under the key 'sub_queries'.\n\nUser Question: {question}\n\n"),
		)

		# Use the new RunnableSequence pattern instead of LLMChain
		chain = planning_prompt | self.llm.with_structured_output(PlanningOutput)
		result = chain.invoke({'question': query})
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-PlanningNode] result : {result}{LogColors.ENDC}')
		plans = result.sub_queries if isinstance(result, PlanningOutput) else []
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-PlanningNode] Planning completed. Plans: {plans}{LogColors.ENDC}')
		return {
			'plans': plans,
			'current_plan_index': 0,
			'all_contexts': [],
			'messages': state.get('messages', []) + [AIMessage(content=f'Planned sub-queries: {plans}')],
		}

	async def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
		"""Retrieve relevant documents based on the current plan sub-query."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-RetrievalNode] Starting document retrieval process{LogColors.ENDC}')
		print(f'State: {state}')
		plans = state.get('plans', [])
		current_plan_index = state.get('current_plan_index', 0)
		collection_id = state.get('collection_id', self.collection_id)
		# Use the current plan sub-query if available, else fallback to main query
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-RetrievalNode] Current plan index: {current_plan_index}, Total plans: {len(plans)}{LogColors.ENDC}')
		if plans and 0 <= current_plan_index < len(plans):
			query = plans[current_plan_index]
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-RetrievalNode] Using plan sub-query: "{query}..." for collection {collection_id}{LogColors.ENDC}')
		else:
			query = state.get('query', '')

		if not query:
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-RetrievalNode] No query provided in state{LogColors.ENDC}')
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}
		# Log the query being processed
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-RetrievalNode] Processing query for collection {collection_id}: "{query[:100]}..."{LogColors.ENDC}')

		try:
			# Retrieve documents using the KB repository
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-RetrievalNode] Executing document retrieval via KB repository{LogColors.ENDC}')
			from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

			# Use collection-specific query
			query_response = await self.kb_repo.query(QueryRequest(query=query, top_k=5), collection_id=collection_id)
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-RetrievalNode] KB query completed for collection {collection_id} - Found {len(query_response.results)} results{LogColors.ENDC}')

			# Convert to Document objects
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-RetrievalNode] Converting query results to Document objects{LogColors.ENDC}')
			retrieved_docs = []
			for i, item in enumerate(query_response.results):
				doc = Document(
					page_content=item.content,
					metadata={**item.metadata, 'collection_id': collection_id},
				)
				retrieved_docs.append(doc)
				logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-RetrievalNode] Document {i + 1} converted - ID: {item.id}, Collection: {collection_id}{LogColors.ENDC}')

			# Prepare context for this plan
			context_parts = []
			for i, doc in enumerate(retrieved_docs):
				doc_id = getattr(doc, 'id', f'doc_{i}')
				context_part = f'Document {i + 1} (ID: {doc_id}, Collection: {collection_id}):\n{doc.page_content}'
				context_parts.append(context_part)
			context = '\n\n'.join(context_parts)

			# Aggregate all contexts
			all_contexts = state.get('all_contexts', [])
			all_contexts = all_contexts + [context] if context else all_contexts

			return {
				'retrieved_documents': retrieved_docs,
				'all_contexts': all_contexts,
				'current_plan_index': current_plan_index + 1,
				'all_contexts': all_contexts,
				'messages': state.get('messages', []) + [AIMessage(content=f'Retrieved {len(retrieved_docs)} documents for plan: "{query}"')],
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph-RetrievalNode] Error during document retrieval for collection {collection_id}: {e}{LogColors.ENDC}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error retrieving documents from collection {collection_id}: {e}')],
			}

	async def _generation_node(self, state: AgentState) -> Dict[str, Any]:
		"""Generate an answer based on all aggregated contexts."""
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph-GenerationNode] Starting answer generation process{LogColors.ENDC}')

		if state.get('error'):
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-GenerationNode] Error detected in state, skipping generation{LogColors.ENDC}')
			return state

		all_contexts = state.get('all_contexts', [])
		collection_id = state.get('collection_id', self.collection_id)

		if not all_contexts:
			logger.info(f'{LogColors.WARNING}[RAGAgentGraph-GenerationNode] No contexts found for generation in collection {collection_id}{LogColors.ENDC}')
			return {
				'answer': f"I don't have enough information to answer this question based on the available knowledge in collection '{collection_id}'.",
				'sources': [],
				'messages': state.get('messages', []) + [AIMessage(content=f'No relevant information found for this query in collection {collection_id}.')],
			}

		# Concatenate all contexts
		context = '\n\n'.join(all_contexts)
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] Aggregated context prepared for collection {collection_id} - Total length: {len(context)} characters{LogColors.ENDC}')

		# Define the generation prompt
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-GenerationNode] Setting up generation prompt template{LogColors.ENDC}')
		template = f"""You are a helpful and precise assistant. Use the following context from collection '{collection_id}' to answer the question at the end. 
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Always provide a detailed and comprehensive answer based only on the context provided.
        Include citations in your answer when you use information from specific documents.
        
        Context from collection '{collection_id}':
        {{context}}
        
        Question: {{question}}
        
        Helpful Answer:"""

		prompt = PromptTemplate(input_variables=['context', 'question'], template=template)
		try:
			query = state.get('query', '')
			prompt_inputs = {'context': context, 'question': query}
			from langchain.chains import LLMChain

			chain = LLMChain(llm=self.llm, prompt=prompt)
			result = chain.invoke(prompt_inputs)
			answer = result.get('text', '')

			# Prepare sources from all retrieved documents
			sources = []
			# Optionally, you can collect all docs from all retrievals if you want to show sources
			# For now, just leave empty or aggregate if you want
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-GenerationNode] Answer generation completed successfully for collection {collection_id}{LogColors.ENDC}')
			return {
				'answer': answer,
				'sources': sources,
				'messages': state.get('messages', []) + [AIMessage(content=answer)],
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph-GenerationNode] Error during answer generation for collection {collection_id}: {e}{LogColors.ENDC}')
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error generating answer for collection {collection_id}: {e}')],
			}

	def _should_continue_plans(self, state: AgentState) -> bool:
		"""Check if there are more plans to process."""
		plans = state.get('plans', [])
		current_plan_index = state.get('current_plan_index', 0)
		return bool(plans) and current_plan_index + 1 < len(plans)

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
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding planning node to graph{LogColors.ENDC}')
		graph.add_node('planning', self._planning_node)

		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding retrieval node to graph{LogColors.ENDC}')
		graph.add_node('retrieval', self._retrieval_node)

		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Adding generation node to graph{LogColors.ENDC}')
		graph.add_node('generation', self._generation_node)

		# Define the edges
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-BuildGraph] Setting up graph edges{LogColors.ENDC}')
		# Planning -> Retrieval
		graph.add_edge('planning', 'retrieval')

		# Retrieval -> Next plan or Generation
		MAX_PLAN_LOOP = 5  # Set your recursion/iteration limit here

		def plan_conditional(state: AgentState):
			plans = state.get('plans', [])
			current_plan_index = state.get('current_plan_index', 0)
			plan_loop_count = state.get('plan_loop_count', 0) or 0

			# Only increment loop count if we are actually looping
			if plans and current_plan_index + 1 < len(plans):
				plan_loop_count += 1
				state['plan_loop_count'] = plan_loop_count
				if plan_loop_count >= MAX_PLAN_LOOP:
					logger.warning(f'[RAGAgentGraph-BuildGraph] Plan loop limit reached ({plan_loop_count}), breaking recursion.')
					return 'generation'
				state['current_plan_index'] = current_plan_index + 1
				return 'retrieval'
			else:
				return 'generation'

		graph.add_conditional_edges(
			'retrieval',
			plan_conditional,
			{
				'retrieval': 'retrieval',
				'generation': 'generation',
			},
		)

		# Generation -> END
		graph.add_edge('generation', END)

		# Set the entry point
		logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph-BuildGraph] Setting planning as entry point{LogColors.ENDC}')
		graph.set_entry_point('planning')

		# Compile the graph
		logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph-BuildGraph] Compiling workflow graph{LogColors.ENDC}')
		compiled_graph = graph.compile()
		logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph-BuildGraph] Workflow graph construction completed{LogColors.ENDC}')

		return compiled_graph

	async def answer_query(self, query: str, collection_id: str = None) -> Dict[str, Any]:
		"""Process a query and return the answer with sources."""
		collection_id = collection_id or self.collection_id
		logger.info(f'{LogColors.HEADER}[RAGAgentGraph] Processing query through workflow for collection {collection_id}: "{query[:100]}..."{LogColors.ENDC}')

		try:
			# Initialize the state
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Initializing workflow state for collection {collection_id}{LogColors.ENDC}')
			state = {
				'query': query,
				'collection_id': collection_id,
				'retrieved_documents': [],
				'answer': None,
				'sources': [],
				'messages': [
					SystemMessage(content=f'RAG Agent for collection: {collection_id}'),
					HumanMessage(content=query),
				],
				'error': None,
				'plan_loop_count': 0,  # <-- Initialize loop counter
			}
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Workflow state initialized for collection {collection_id}{LogColors.ENDC}')

			# Create a new session for this execution
			session_id = str(uuid.uuid4())
			logger.info(f'{LogColors.OKBLUE}[RAGAgentGraph] Created workflow session: {session_id} for collection {collection_id}{LogColors.ENDC}')

			# Execute the workflow
			logger.info(f'{LogColors.OKCYAN}[RAGAgentGraph] Executing workflow with session: {session_id}{LogColors.ENDC}')
			result = await self.workflow.ainvoke(state, config={'configurable': {'session_id': session_id}})
			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] Workflow execution completed for session: {session_id}, collection: {collection_id}{LogColors.ENDC}')

			# Check if we got an error
			if result.get('error'):
				logger.info(f'{LogColors.WARNING}[RAGAgentGraph] Workflow completed with error for collection {collection_id}: {result["error"]}{LogColors.ENDC}')
				raise Exception(result['error'])

			# Return the results
			answer = result.get('answer', '')
			sources = result.get('sources', [])
			messages = result.get('messages', [])

			logger.info(f'{LogColors.OKGREEN}[RAGAgentGraph] Query processing completed successfully for collection {collection_id} - Answer length: {len(answer)}, Sources: {len(sources)}{LogColors.ENDC}')

			return {
				'answer': answer,
				'sources': sources,
				'conversation': [msg.content for msg in messages],
				'collection_id': collection_id,
			}
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGAgentGraph] Critical error during query processing for collection {collection_id}: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
