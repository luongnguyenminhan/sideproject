"""
LangChain Qdrant Service for Agentic RAG
Using KB Repository for all document operations
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
import uuid

logger = logging.getLogger(__name__)


class LangChainQdrantService:
    """Simplified service using KB Repository for all document operations"""

    def __init__(self, db: Session):
        logger.info(
            "LangChainQdrantService - Initializing with KB Repository integration"
        )
        self.db = db

    async def index_documents(
        self, documents: List[Document], collection_name: str, batch_size: int = 50
    ) -> Dict[str, Any]:
        """Index documents using KB Repository"""
        logger.info(
            f"LangChainQdrantService - Indexing {len(documents)} documents to collection '{collection_name}'"
        )

        try:
            from app.modules.agentic_rag.repositories.kb_repo import KBRepository
            from app.modules.agentic_rag.schemas.kb_schema import (
                AddDocumentsRequest,
                DocumentModel,
            )

            # Text splitter for large documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200, length_function=len
            )

            # Split documents into chunks
            doc_chunks = []
            for doc in documents:
                chunks = text_splitter.split_documents([doc])
                doc_chunks.extend(chunks)

            # Initialize KB Repository
            kb_repo = KBRepository(collection_name=collection_name)

            # Convert chunks to DocumentInput format and process in batches
            total_indexed = 0
            for i in range(0, len(doc_chunks), batch_size):
                batch = doc_chunks[i : i + batch_size]

                document_inputs = []
                for chunk in batch:
                    doc_input = DocumentModel(
                        id=str(uuid.uuid4()),
                        content=chunk.page_content,
                        metadata=chunk.metadata or {},
                    )
                    document_inputs.append(doc_input)

                # Add documents via KB Repository
                add_request = AddDocumentsRequest(documents=document_inputs)
                ids = await kb_repo.add_documents(
                    add_request, collection_id=collection_name
                )
                total_indexed += len(ids)

            result = {
                "total_documents": len(documents),
                "total_chunks": len(doc_chunks),
                "total_indexed": total_indexed,
                "collection": collection_name,
                "indexing_method": "kb_repository",
            }

            logger.info(f"LangChainQdrantService - Indexing completed: {result}")
            return result

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Failed to index documents: {str(e)}",
                exc_info=True,
            )
            raise ValidationException(_("document_indexing_failed"))

    async def similarity_search(
        self,
        query: str,
        collection_name: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> List[Document]:
        """Perform similarity search using KB Repository"""
        logger.info(
            f"LangChainQdrantService - Searching in collection '{collection_name}': '{query[:50]}...'"
        )

        try:
            from app.modules.agentic_rag.repositories.kb_repo import KBRepository
            from app.modules.agentic_rag.schemas.kb_schema import QueryRequest

            # Initialize KB Repository and perform search
            kb_repo = KBRepository(collection_name=collection_name)
            query_request = QueryRequest(query=query, top_k=top_k)
            query_response = await kb_repo.query(
                query_request, collection_id=collection_name
            )

            # Convert results to Document format and filter by score
            documents = []
            for result in query_response.results:
                if result.score >= score_threshold:
                    doc = Document(
                        page_content=result.content,
                        metadata={
                            **result.metadata,
                            "similarity_score": result.score,
                            "document_id": result.id,
                        },
                    )
                    documents.append(doc)

            logger.info(
                f"LangChainQdrantService - Found {len(documents)} documents above threshold"
            )
            return documents

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Search failed: {str(e)}", exc_info=True
            )
            raise ValidationException(_("similarity_search_failed"))

    def list_collections(self) -> List[str]:
        """List all collections via KB Repository"""
        try:
            from app.modules.agentic_rag.repositories.kb_repo import KBRepository

            kb_repo = KBRepository()
            collections = kb_repo.list_collections()
            logger.info(
                f"LangChainQdrantService - Found {len(collections)} collections"
            )
            return collections

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Failed to list collections: {str(e)}",
                exc_info=True,
            )
            return []

    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists via KB Repository"""
        try:
            from app.modules.agentic_rag.repositories.kb_repo import KBRepository

            kb_repo = KBRepository()
            return kb_repo.collection_exists(collection_name)

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Error checking collection: {str(e)}",
                exc_info=True,
            )
            return False

    def create_collection(self, collection_name: str) -> bool:
        """Create collection via KB Repository"""
        try:
            from app.modules.agentic_rag.repositories.kb_repo import KBRepository

            kb_repo = KBRepository()
            result = kb_repo.create_collection(collection_name)
            logger.info(
                f"LangChainQdrantService - Collection '{collection_name}' creation: {result}"
            )
            return result

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Failed to create collection: {str(e)}",
                exc_info=True,
            )
            return False

    def get_conversation_collection_name(self, conversation_id: str) -> str:
        """Generate collection name for conversation"""
        return f"conversation_{conversation_id}"

    async def index_conversation_files(
        self, conversation_id: str, files_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Index files for conversation using KB Repository"""
        logger.info(
            f"LangChainQdrantService - Indexing {len(files_data)} files for conversation '{conversation_id}'"
        )

        try:
            collection_name = self.get_conversation_collection_name(conversation_id)

            # Convert files to Document objects
            documents = []
            for file_data in files_data:
                doc = Document(
                    page_content=file_data["content"],
                    metadata={
                        "file_id": file_data["file_id"],
                        "file_name": file_data["file_name"],
                        "file_type": file_data["file_type"],
                        "conversation_id": conversation_id,
                        "indexed_at": file_data.get("indexed_at"),
                    },
                )
                documents.append(doc)

            # Index via KB Repository
            result = await self.index_documents(documents, collection_name)
            logger.info(
                f"LangChainQdrantService - Conversation files indexed successfully"
            )
            return result

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Failed to index conversation files: {str(e)}",
                exc_info=True,
            )
            raise ValidationException(_("conversation_files_indexing_failed"))

    async def search_conversation_files(
        self,
        conversation_id: str,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.7,
    ) -> List[Document]:
        """Search files in conversation using KB Repository"""
        logger.info(
            f"LangChainQdrantService - Searching files in conversation '{conversation_id}'"
        )

        try:
            collection_name = self.get_conversation_collection_name(conversation_id)

            # Check if collection exists
            if not self.collection_exists(collection_name):
                logger.info(
                    f"LangChainQdrantService - No files indexed for conversation '{conversation_id}'"
                )
                return []

            # Perform search
            documents = await self.similarity_search(
                query, collection_name, top_k, score_threshold
            )
            logger.info(
                f"LangChainQdrantService - Found {len(documents)} relevant files"
            )
            return documents

        except Exception as e:
            logger.error(
                f"LangChainQdrantService - Failed to search conversation files: {str(e)}",
                exc_info=True,
            )
            return []
