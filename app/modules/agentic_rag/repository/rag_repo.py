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

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.database import get_db

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_repo import BaseRepo

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.exception import CustomHTTPException, ValidationException
from ..schemas.rag_schema import (
    RAGRequest,
    RAGResponse,
    CitedSource,
)
from ..dal.rag_dal import RAGVectorDAL
from ..schemas.kb_schema import QueryRequest

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)


class RAGRepo(BaseRepo):
    """Repository for generating responses using RAG techniques - tuân thủ naming convention."""

    def __init__(self, db: Session = Depends(get_db)) -> None:
        """Initialize RAG repository với dependency injection."""

        self.db = db

        self.rag_dal = RAGVectorDAL(db)

        # Initialize the LLM
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=0.7,
                convert_system_message_to_human=True,
            )
        except Exception as e:
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))

        # Define the default RAG prompt
        self.rag_prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are a helpful and precise assistant. Use the following context to answer the question at the end. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Always provide a detailed and comprehensive answer based only on the context provided.
            
            Context:
            {context}
            
            Question: {question}
            
            Helpful Answer:""",
        )

    async def generate(
        self, request: RAGRequest, collection_id: str = "global"
    ) -> RAGResponse:
        """Generate a response using RAG based on the query for specific collection."""

        try:
            # Validate collection exists
            if not self.rag_dal.collection_exists(collection_id):
                raise ValidationException(_("collection_not_found"))

            # Retrieve documents from the knowledge base via DAL
            query_response = await self.rag_dal.search_in_collection(
                collection_name=collection_id, query=request.query, top_k=request.top_k
            )

            if not query_response.results:
                return RAGResponse(
                    answer=f"I don't have enough information to answer this question based on the available knowledge in collection '{collection_id}'.",
                    sources=[],
                    usage={
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                )

            # Prepare the context by combining the contents of retrieved documents
            context = "\n\n".join(
                [
                    f"Document {i + 1} (Collection: {collection_id}):\n{doc.content}"
                    for i, doc in enumerate(query_response.results)
                ]
            )
            context_length = len(context)

            # Create a RetrievelQA chain with the prepared context
            qa_chain = self.create_qa_chain(request.temperature)

            # Generate the response
            result = qa_chain.invoke({"context": context, "question": request.query})

            # Create the sources information for each document
            sources = []
            for i, doc in enumerate(query_response.results):
                source = CitedSource(
                    id=doc.id,
                    content=(
                        doc.content[:200] + "..."
                        if len(doc.content) > 200
                        else doc.content
                    ),
                    score=doc.score,
                    metadata={**doc.metadata, "collection_id": collection_id},
                )
                sources.append(source)

            # Create token usage estimation
            answer_text = result["text"]
            usage = {
                "prompt_tokens": len(context) // 4 + len(request.query) // 4,
                "completion_tokens": len(answer_text) // 4,
                "total_tokens": (len(context) + len(request.query) + len(answer_text))
                // 4,
            }

            return RAGResponse(answer=answer_text, sources=sources, usage=usage)

        except ValidationException:
            raise
        except Exception as e:
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))

    def create_qa_chain(self, temperature: float) -> Any:
        """Create a QA chain for answering questions with context."""

        try:
            # Create a new LLM instance with the requested temperature
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=GOOGLE_API_KEY,
                temperature=temperature,
                convert_system_message_to_human=True,
            )

            # Create chain directly with prompt and llm
            from langchain.chains import LLMChain

            chain = LLMChain(
                llm=llm,
                prompt=self.rag_prompt_template,
            )

            return chain
        except Exception as e:
            raise CustomHTTPException(status_code=500, message=_("error_occurred"))
