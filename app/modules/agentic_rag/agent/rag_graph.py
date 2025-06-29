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

		self.collection_id = collection_id or DEFAULT_COLLECTION
		self.kb_repo = kb_repo or KBRepository(collection_name=self.collection_id)

		try:
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash-lite',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
		except Exception as e:
			logger.error(f'[RAGAgentGraph] Failed to initialize LLM: {str(e)}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		self.memory = MemorySaver()  # In-memory checkpointer for state

		self.workflow = self._build_graph()

	async def _planning_node(self, state: AgentState) -> Dict[str, Any]:
		"""Plan a list of sub-queries to maximize information retrieval."""
		query = state.get('query', '')

		if not query:
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
		plans = result.sub_queries if isinstance(result, PlanningOutput) else []
		return {
			'plans': plans,
			'current_plan_index': 0,
			'all_contexts': [],
			'messages': state.get('messages', []) + [AIMessage(content=f'Planned sub-queries: {plans}')],
		}

	async def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
		"""Retrieve relevant documents based on the current plan sub-query."""
		plans = state.get('plans', [])
		current_plan_index = state.get('current_plan_index', 0)
		collection_id = state.get('collection_id', self.collection_id)
		# Use the current plan sub-query if available, else fallback to main query
		if plans and 0 <= current_plan_index < len(plans):
			query = plans[current_plan_index]
		else:
			query = state.get('query', '')

		if not query:
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}
		# Log the query being processed

		try:
			# Retrieve documents using the KB repository
			from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

			# Use collection-specific query
			query_response = await self.kb_repo.query(QueryRequest(query=query, top_k=5), collection_id=collection_id)

			# Convert to Document objects
			retrieved_docs = []
			for i, item in enumerate(query_response.results):
				doc = Document(
					page_content=item.content,
					metadata={**item.metadata, 'collection_id': collection_id},
				)
				retrieved_docs.append(doc)

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
				'messages': state.get('messages', []) + [AIMessage(content=f'Retrieved {len(retrieved_docs)} documents for plan: "{query}"')],
			}
		except Exception as e:
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error retrieving documents from collection {collection_id}: {e}')],
			}

	async def _generation_node(self, state: AgentState) -> Dict[str, Any]:
		"""Generate an answer based on all aggregated contexts."""

		if state.get('error'):
			return state

		all_contexts = state.get('all_contexts', [])
		collection_id = state.get('collection_id', self.collection_id)

		if not all_contexts:
			return {
				'answer': f"I don't have enough information to answer this question based on the available knowledge in collection '{collection_id}'.",
				'sources': [],
				'messages': state.get('messages', []) + [AIMessage(content=f'No relevant information found for this query in collection {collection_id}.')],
			}

		# Concatenate all contexts
		context = '\n\n'.join(all_contexts)

		# Define the generation prompt
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
			return {
				'answer': answer,
				'sources': sources,
				'messages': state.get('messages', []) + [AIMessage(content=answer)],
			}
		except Exception as e:
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

		return should_end

	def _build_graph(self) -> StateGraph:
		"""Construct the LangGraph StateGraph for the RAG workflow."""

		# Define the graph
		graph = StateGraph(AgentState)

		# Add nodes
		graph.add_node('planning', self._planning_node)

		graph.add_node('retrieval', self._retrieval_node)

		graph.add_node('generation', self._generation_node)

		# Define the edges
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
		graph.set_entry_point('planning')

		# Compile the graph
		compiled_graph = graph.compile()

		return compiled_graph

	async def answer_query(self, query: str, collection_id: str = None) -> Dict[str, Any]:
		"""Process a query and return the answer with sources."""
		collection_id = collection_id or self.collection_id

		try:
			# Initialize the state
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

			# Create a new session for this execution
			session_id = str(uuid.uuid4())

			# Execute the workflow
			result = await self.workflow.ainvoke(state, config={'configurable': {'session_id': session_id}})

			# Check if we got an error
			if result.get('error'):
				raise Exception(result['error'])

			# Return the results
			answer = result.get('answer', '')
			sources = result.get('sources', [])
			messages = result.get('messages', [])

			return {
				'answer': answer,
				'sources': sources,
				'conversation': [msg.content for msg in messages],
				'collection_id': collection_id,
			}
		except Exception as e:
			logger.error(f'[RAGAgentGraph] Error processing query "{query}" in collection "{collection_id}": {str(e)}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
