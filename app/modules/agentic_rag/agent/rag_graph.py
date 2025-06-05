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
from app.modules.agentic_rag.core.config import DEFAULT_COLLECTION

logger = logging.getLogger(__name__)



class AgentState(TypedDict):
	"""State for the Agentic RAG workflow."""

	query: str
	collection_id: str
	retrieved_documents: List[Document]
	answer: Optional[str]
	sources: List[Dict[str, Any]]
	messages: List[Any]
	error: Optional[str]


class RAGAgentGraph:
	"""LangGraph-based agent for RAG operations."""

	def __init__(self, kb_repo: Optional[KBRepository] = None, collection_id: str = None) -> None:
		"""Initialize the RAG agent graph."""

		self.collection_id = collection_id or DEFAULT_COLLECTION
		self.kb_repo = kb_repo or KBRepository(collection_name=self.collection_id)

		try:
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
		except Exception as e:
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		self.memory = MemorySaver()  # In-memory checkpointer for state

		self.workflow = self._build_graph()

	async def _retrieval_node(self, state: AgentState) -> Dict[str, Any]:
		"""Retrieve relevant documents based on the query."""

		# Get the user query and collection_id
		query = state.get('query', '')
		collection_id = state.get('collection_id', self.collection_id)

		if not query:
			return {
				'error': 'No query provided',
				'messages': state.get('messages', []) + [AIMessage(content='Error: No query provided')],
			}


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

			return {
				'retrieved_documents': retrieved_docs,
				'messages': state.get('messages', []) + [AIMessage(content=f'Retrieved {len(retrieved_docs)} documents from collection {collection_id}')],
			}
		except Exception as e:
			return {
				'error': str(e),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error retrieving documents from collection {collection_id}: {e}')],
			}

	async def _generation_node(self, state: AgentState) -> Dict[str, Any]:
		"""Generate an answer based on retrieved documents."""

		# Check if we have an error or documents
		if state.get('error'):
			return state

		docs = state.get('retrieved_documents', [])
		collection_id = state.get('collection_id', self.collection_id)

		if not docs:
			return {
				'answer': f"I don't have enough information to answer this question based on the available knowledge in collection '{collection_id}'.",
				'sources': [],
				'messages': state.get('messages', []) + [AIMessage(content=f'No relevant information found for this query in collection {collection_id}.')],
			}


		# Prepare context from retrieved documents
		context_parts = []
		for i, doc in enumerate(docs):
			doc_id = getattr(doc, 'id', f'doc_{i}')
			context_part = f'Document {i + 1} (ID: {doc_id}, Collection: {collection_id}):\n{doc.page_content}'
			context_parts.append(context_part)

		context = '\n\n'.join(context_parts)

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
			# Prepare the prompt inputs
			query = state.get('query', '')
			prompt_inputs = {'context': context, 'question': query}

			# Invoke the LLM
			from langchain.chains import LLMChain

			chain = LLMChain(llm=self.llm, prompt=prompt)
			result = chain.invoke(prompt_inputs)

			# Extract the answer
			answer = result.get('text', '')

			# Prepare source information for each document
			sources = []
			for i, doc in enumerate(docs):
				doc_id = getattr(doc, 'id', 'unknown')
				doc_score = getattr(doc, 'score', 0.0)
				source = {
					'id': doc_id,
					'content': (doc.page_content[:200] + '...' if len(doc.page_content) > 200 else doc.page_content),
					'score': doc_score,
					'metadata': {**doc.metadata, 'collection_id': collection_id},
				}
				sources.append(source)

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
		graph.add_node('retrieval', self._retrieval_node)

		graph.add_node('generation', self._generation_node)

		# Define the edges
		graph.add_edge('retrieval', 'generation')

		graph.add_conditional_edges(
			'generation',
			self._should_end,
			{
				True: END,
				False: 'retrieval',  # We could loop back for refinement, but for now we'll end
			},
		)

		# Set the entry point
		graph.set_entry_point('retrieval')

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
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
