"""
Repository for RAG operations - tuân thủ meobeo-ai-rule architecture.
Repository layer chỉ chứa business logic, delegate database operations to DAL.
"""

import logging
from typing import Any
from sqlalchemy.orm import Session
from fastapi import Depends

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

from app.core.database import get_db
from app.middleware.translation_manager import _
from app.exceptions.exception import CustomHTTPException, ValidationException
from app.modules.agentic_rag.schemas.rag_schema import (
	RAGRequest,
	RAGResponse,
	CitedSource,
)
from app.modules.agentic_rag.dal.rag_dal import RAGVectorDAL
from app.modules.agentic_rag.schemas.kb_schema import QueryRequest
from app.core.config import GOOGLE_API_KEY

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


class RAGRepo:
	"""Repository for generating responses using RAG techniques - tuân thủ naming convention."""

	def __init__(self, db: Session = Depends(get_db)) -> None:
		"""Initialize RAG repository với dependency injection."""
		logger.info(f'{LogColors.HEADER}[RAGRepo] Initializing RAG Repository{LogColors.ENDC}')

		self.db = db
		logger.info(f'{LogColors.OKBLUE}[RAGRepo] Database session established{LogColors.ENDC}')

		self.rag_dal = RAGVectorDAL(db)
		logger.info(f'{LogColors.OKCYAN}[RAGRepo] RAGVectorDAL initialized{LogColors.ENDC}')

		# Initialize the LLM
		try:
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Initializing ChatGoogleGenerativeAI with model: gemini-2.0-flash{LogColors.ENDC}')
			self.llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash',
				google_api_key=GOOGLE_API_KEY,
				temperature=0.7,
				convert_system_message_to_human=True,
			)
			logger.info(f'{LogColors.OKGREEN}[RAGRepo] ChatGoogleGenerativeAI initialized successfully{LogColors.ENDC}')
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGRepo] Error initializing LLM: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

		# Define the default RAG prompt
		logger.info(f'{LogColors.OKCYAN}[RAGRepo] Setting up RAG prompt template{LogColors.ENDC}')
		self.rag_prompt_template = PromptTemplate(
			input_variables=['context', 'question'],
			template="""You are a helpful and precise assistant. Use the following context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Always provide a detailed and comprehensive answer based only on the context provided.
            
            Context:
            {context}
            
            Question: {question}
            
            Helpful Answer:""",
		)
		logger.info(f'{LogColors.OKGREEN}[RAGRepo] RAG prompt template configured successfully{LogColors.ENDC}')

	async def generate(self, request: RAGRequest, collection_name: str = 'default') -> RAGResponse:
		"""Generate a response using RAG based on the query."""
		logger.info(f'{LogColors.HEADER}[RAGRepo] Starting RAG generation for collection: {collection_name}{LogColors.ENDC}')
		logger.info(f'{LogColors.OKBLUE}[RAGRepo] Query: "{request.query[:100]}..." (Top K: {request.top_k}, Temperature: {request.temperature}){LogColors.ENDC}')

		try:
			# Validate collection exists
			logger.info(f'{LogColors.OKCYAN}[RAGRepo] Validating collection existence: {collection_name}{LogColors.ENDC}')
			if not self.rag_dal.collection_exists(collection_name):
				logger.info(f'{LogColors.WARNING}[RAGRepo] Collection not found: {collection_name}{LogColors.ENDC}')
				raise ValidationException(_('collection_not_found'))

			logger.info(f'{LogColors.OKGREEN}[RAGRepo] Collection validated successfully: {collection_name}{LogColors.ENDC}')

			# Retrieve documents from the knowledge base via DAL
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Retrieving documents from collection via DAL{LogColors.ENDC}')
			query_response = await self.rag_dal.search_in_collection(collection_name=collection_name, query=request.query, top_k=request.top_k)

			logger.info(f'{LogColors.OKCYAN}[RAGRepo] Retrieved {len(query_response.results)} documents from collection{LogColors.ENDC}')

			if not query_response.results:
				logger.info(f'{LogColors.WARNING}[RAGRepo] No results found for query: "{request.query}"{LogColors.ENDC}')
				return RAGResponse(
					answer="I don't have enough information to answer this question based on the available knowledge.",
					sources=[],
					usage={
						'prompt_tokens': 0,
						'completion_tokens': 0,
						'total_tokens': 0,
					},
				)

			# Prepare the context by combining the contents of retrieved documents
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Preparing context from {len(query_response.results)} retrieved documents{LogColors.ENDC}')
			context = '\n\n'.join([f'Document {i + 1}:\n{doc.content}' for i, doc in enumerate(query_response.results)])
			context_length = len(context)
			logger.info(f'{LogColors.OKCYAN}[RAGRepo] Context prepared - Total length: {context_length} characters{LogColors.ENDC}')

			# Create a RetrievelQA chain with the prepared context
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Creating QA chain with temperature: {request.temperature}{LogColors.ENDC}')
			qa_chain = self.create_qa_chain(request.temperature)
			logger.info(f'{LogColors.OKCYAN}[RAGRepo] QA chain created successfully{LogColors.ENDC}')

			# Generate the response
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Invoking QA chain for response generation{LogColors.ENDC}')
			result = qa_chain.invoke({'context': context, 'question': request.query})
			logger.info(f'{LogColors.OKGREEN}[RAGRepo] QA chain invocation completed{LogColors.ENDC}')

			# Create the sources information for each document
			logger.info(f'{LogColors.OKCYAN}[RAGRepo] Creating source citations for {len(query_response.results)} documents{LogColors.ENDC}')
			sources = []
			for i, doc in enumerate(query_response.results):
				source = CitedSource(
					id=doc.id,
					content=(doc.content[:200] + '...' if len(doc.content) > 200 else doc.content),
					score=doc.score,
					metadata=doc.metadata,
				)
				sources.append(source)
				logger.info(f'{LogColors.OKCYAN}[RAGRepo] Source {i + 1} created - ID: {doc.id}, Score: {doc.score:.4f}, Content length: {len(doc.content)}{LogColors.ENDC}')

			# Create token usage estimation (example values, replace with actual tracking)
			answer_text = result['text']
			usage = {
				'prompt_tokens': len(context) // 4 + len(request.query) // 4,  # Approximation
				'completion_tokens': len(answer_text) // 4,  # Approximation
				'total_tokens': (len(context) + len(request.query) + len(answer_text)) // 4,  # Approximation
			}

			logger.info(f'{LogColors.OKGREEN}[RAGRepo] Token usage estimated - Prompt: {usage["prompt_tokens"]}, Completion: {usage["completion_tokens"]}, Total: {usage["total_tokens"]}{LogColors.ENDC}')
			logger.info(f'{LogColors.OKGREEN}[RAGRepo] RAG response generated successfully - Answer length: {len(answer_text)} characters{LogColors.ENDC}')

			return RAGResponse(answer=answer_text, sources=sources, usage=usage)

		except ValidationException:
			logger.info(f'{LogColors.WARNING}[RAGRepo] Validation exception occurred during RAG generation{LogColors.ENDC}')
			# Re-raise validation exceptions
			raise
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGRepo] Critical error during RAG generation: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))

	def create_qa_chain(self, temperature: float) -> Any:
		"""Create a QA chain for answering questions with context."""
		logger.info(f'{LogColors.HEADER}[RAGRepo] Creating QA chain with temperature: {temperature}{LogColors.ENDC}')

		try:
			# Create a new LLM instance with the requested temperature
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Initializing LLM instance with custom temperature: {temperature}{LogColors.ENDC}')
			llm = ChatGoogleGenerativeAI(
				model='gemini-2.0-flash',
				google_api_key=GOOGLE_API_KEY,
				temperature=temperature,
				convert_system_message_to_human=True,
			)
			logger.info(f'{LogColors.OKCYAN}[RAGRepo] LLM instance created with temperature: {temperature}{LogColors.ENDC}')

			# Create chain directly with prompt and llm
			logger.info(f'{LogColors.OKBLUE}[RAGRepo] Creating LLMChain with prompt template{LogColors.ENDC}')
			from langchain.chains import LLMChain

			chain = LLMChain(
				llm=llm,
				prompt=self.rag_prompt_template,
			)

			logger.info(f'{LogColors.OKGREEN}[RAGRepo] QA chain created successfully{LogColors.ENDC}')
			return chain
		except Exception as e:
			logger.info(f'{LogColors.FAIL}[RAGRepo] Error creating QA chain: {e}{LogColors.ENDC}')
			raise CustomHTTPException(status_code=500, message=_('error_occurred'))
