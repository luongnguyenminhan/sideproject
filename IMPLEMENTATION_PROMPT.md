# 🚀 AI Implementation Prompt: Modular LangGraph với QdrantService Integration

## 🎯 Objective
Refactor `chat_workflow.py` (18KB, 568 lines) thành modular structure và implement production-ready QdrantService integration cho knowledge retrieval trong LangGraph workflow.

## 📊 Current State Analysis

### ✅ **Assets Available:**
- ✅ Working `chat_workflow.py` với complete LangGraph implementation
- ✅ Production `QdrantService` class với full vector search capabilities  
- ✅ Reference implementation trong `moneyez-ai-service/app/langgraph/`
- ✅ Working `LangGraphService` với global caching
- ✅ Vietnamese language support và financial keywords

### ❌ **Current Issues:**
- ❌ Monolithic 568-line file - khó maintain
- ❌ Mock RAG functions - cần real QdrantService integration
- ❌ Hard-coded configurations - cần centralized config
- ❌ Limited error handling - cần production-ready patterns
- ❌ No separation of concerns - mixing RAG, tools, và agent logic

## 🏗️ Target Architecture

### **Folder Structure:**
```
app/modules/agent/workflows/chat_workflow/
├── __init__.py                    # Main workflow export
├── config/
│   ├── __init__.py
│   ├── workflow_config.py         # Centralized configuration
│   └── prompts.py                 # System prompts & templates
├── nodes/
│   ├── __init__.py
│   ├── rag_nodes.py              # RAG decision, query gen, retrieval
│   ├── agent_nodes.py            # LLM calling, routing logic
│   └── tool_nodes.py             # Tool execution & management
├── state/
│   ├── __init__.py
│   └── workflow_state.py         # AgentState definition
├── tools/
│   ├── __init__.py
│   ├── frontend_tools.py         # Frontend tool interrupts
│   └── backend_tools.py          # Backend tool implementations
├── knowledge/
│   ├── __init__.py
│   ├── retriever.py              # QdrantService integration
│   └── query_optimizer.py       # Query processing & enhancement
└── utils/
    ├── __init__.py
    ├── message_utils.py          # Message processing utilities
    └── error_handlers.py         # Error handling & fallbacks
```

## 🔧 Implementation Strategy

### **Phase 1: Core Modularization**
1. **Extract State Definition**
   ```python
   # state/workflow_state.py
   from typing import Dict, List, Optional, Annotated, TypedDict
   from langchain_core.messages import BaseMessage
   from langchain_core.documents import Document
   from langgraph.graph.message import add_messages

   class AgentState(TypedDict):
       """Production-ready state với comprehensive typing"""
       messages: Annotated[List[BaseMessage], add_messages]
       rag_context: Optional[List[str]]
       queries: Optional[List[str]]
       retrieved_docs: Optional[List[Document]]
       need_rag: Optional[bool]
       conversation_metadata: Optional[Dict[str, Any]]
       error_context: Optional[Dict[str, Any]]
   ```

2. **Extract Configuration Management**
   ```python
   # config/workflow_config.py
   from dataclasses import dataclass
   from typing import Dict, List, Optional
   
   @dataclass
   class WorkflowConfig:
       """Centralized workflow configuration"""
       # Model settings
       model_name: str = 'gemini-2.0-flash'
       temperature: float = 0
       max_tokens: int = 2048
       
       # RAG settings
       rag_enabled: bool = True
       similarity_threshold: float = 0.7
       max_retrieved_docs: int = 5
       collection_name: str = 'moneyez_knowledge'
       
       # Vietnamese financial keywords
       knowledge_keywords: List[str] = field(default_factory=lambda: [
           'tài chính', 'thông tin', 'giải thích', 'là gì', 'định nghĩa',
           'khái niệm', 'cách', 'làm sao', 'tư vấn', 'nên', 'hướng dẫn',
           'quy định', 'luật', 'chính sách', 'so sánh', 'khác nhau',
           'đầu tư', 'tiết kiệm', 'ngân hàng', 'tín dụng', 'bảo hiểm',
           'thuế', 'lãi suất', 'cổ phiếu', 'trái phiếu', 'quỹ đầu tư'
       ])
   ```

### **Phase 2: QdrantService Integration**

1. **Replace Mock Retrieval với Real Implementation**
   ```python
   # knowledge/retriever.py
   from typing import List, Dict, Any
   from langchain_core.documents import Document
   from app.modules.agent.services.qdrant_service import QdrantService
   import logging

   class KnowledgeRetriever:
       """Production knowledge retriever với QdrantService"""
       
       def __init__(self, db_session, config: WorkflowConfig):
           self.qdrant_service = QdrantService(db_session)
           self.config = config
           self.logger = logging.getLogger(__name__)
           
       async def retrieve_documents(
           self,
           queries: List[str],
           collection_name: str = None
       ) -> List[Document]:
           """Real document retrieval từ QdrantDB"""
           try:
               collection = collection_name or self.config.collection_name
               
               # Ensure collection exists
               self.qdrant_service.initialize_collection(collection)
               
               all_docs = []
               for query in queries:
                   # Use QdrantService similarity search
                   docs = self.qdrant_service.similarity_search(
                       query=query,
                       collection_name=collection,
                       top_k=self.config.max_retrieved_docs,
                       score_threshold=self.config.similarity_threshold
                   )
                   all_docs.extend(docs)
               
               # Deduplicate và rank documents
               unique_docs = self._deduplicate_documents(all_docs)
               ranked_docs = self._rank_documents(unique_docs, queries)
               
               self.logger.info(f"Retrieved {len(ranked_docs)} documents")
               return ranked_docs[:self.config.max_retrieved_docs]
               
           except Exception as e:
               self.logger.error(f"Knowledge retrieval failed: {str(e)}")
               return []  # Graceful degradation
   ```

2. **Implement Query Optimization**
   ```python
   # knowledge/query_optimizer.py
   class QueryOptimizer:
       """Advanced query processing cho better retrieval"""
       
       def __init__(self, config: WorkflowConfig):
           self.config = config
           
       def optimize_queries(self, user_message: str) -> List[str]:
           """Generate multiple optimized search queries"""
           
           # Base query cleanup
           cleaned_query = self._remove_filler_words(user_message)
           
           # Generate variants
           queries = [
               cleaned_query,  # Clean version
               self._add_financial_context(cleaned_query),  # Enhanced với financial terms
               self._extract_key_concepts(cleaned_query),   # Key concept extraction
           ]
           
           return [q for q in queries if q and len(q.strip()) > 2]
   ```

### **Phase 3: RAG Node Implementation**

1. **Production RAG Nodes**
   ```python
   # nodes/rag_nodes.py
   from typing import Dict, Any
   from ..state.workflow_state import AgentState
   from ..knowledge.retriever import KnowledgeRetriever
   from ..knowledge.query_optimizer import QueryOptimizer
   from ..config.workflow_config import WorkflowConfig

   class RAGNodes:
       """Production RAG node implementations"""
       
       def __init__(self, db_session, config: WorkflowConfig):
           self.retriever = KnowledgeRetriever(db_session, config)
           self.optimizer = QueryOptimizer(config)
           self.config = config
           
       async def should_use_rag(
           self, 
           state: AgentState, 
           config: Dict
       ) -> Dict[str, Any]:
           """Smart RAG decision với advanced logic"""
           try:
               # Extract last user message
               user_message = self._extract_last_user_message(state)
               if not user_message:
                   return {'need_rag': False}
               
               # Multiple decision factors
               keyword_match = self._check_knowledge_keywords(user_message)
               question_type = self._classify_question_type(user_message)
               context_dependency = self._check_context_dependency(state)
               
               # Smart decision logic
               need_rag = (
                   keyword_match or 
                   question_type in ['information', 'explanation', 'comparison'] or
                   context_dependency
               )
               
               return {
                   'need_rag': need_rag,
                   'decision_factors': {
                       'keyword_match': keyword_match,
                       'question_type': question_type,
                       'context_dependency': context_dependency
                   }
               }
               
           except Exception as e:
               # Graceful fallback
               return {'need_rag': False, 'error': str(e)}
       
       async def retrieve_knowledge(
           self,
           state: AgentState,
           config: Dict
       ) -> Dict[str, Any]:
           """Real knowledge retrieval implementation"""
           try:
               queries = state.get('queries', [])
               if not queries:
                   return {'rag_context': [], 'retrieved_docs': []}
               
               # Use real retriever
               docs = await self.retriever.retrieve_documents(
                   queries=queries,
                   collection_name=config.get('collection_name')
               )
               
               # Extract content cho context
               rag_context = [doc.page_content for doc in docs]
               
               return {
                   'rag_context': rag_context,
                   'retrieved_docs': docs,
                   'retrieval_metadata': {
                       'query_count': len(queries),
                       'doc_count': len(docs),
                       'avg_score': self._calculate_avg_score(docs)
                   }
               }
               
           except Exception as e:
               return {
                   'rag_context': [],
                   'retrieved_docs': [],
                   'error': str(e)
               }
   ```

### **Phase 4: Agent & Tool Integration**

1. **Enhanced Agent Nodes**
   ```python
   # nodes/agent_nodes.py
   class AgentNodes:
       """Production agent implementations với advanced features"""
       
       async def call_model(
           self,
           state: AgentState,
           config: Dict
       ) -> Dict[str, Any]:
           """Enhanced model calling với RAG context integration"""
           
           # Build enhanced system prompt
           system_prompt = self._build_system_prompt(state, config)
           
           # Setup model với proper configuration
           model = self._setup_model(config)
           
           # Create prompt với RAG context
           prompt = self._create_enhanced_prompt(system_prompt, state)
           
           # Execute với error handling
           try:
               response = await self._execute_model_call(model, prompt, state)
               return {'messages': [response]}
           except Exception as e:
               return {'messages': [self._create_fallback_response(e)]}
   ```

2. **Tool System Enhancement**
   ```python
   # tools/frontend_tools.py
   class ProductionFrontendTools:
       """Enhanced frontend tool system"""
       
       def create_tool_definitions(self, config: Dict) -> List[Dict]:
           """Create comprehensive tool definitions"""
           
       def handle_tool_interrupts(self, state: AgentState) -> Dict[str, Any]:
           """Advanced tool interrupt handling"""
   ```

## 🎯 Key Implementation Requirements

### **1. QdrantService Integration Points:**
- ✅ Replace `mock_retrieve_docs()` với `QdrantService.similarity_search()`
- ✅ Implement collection initialization trong workflow startup
- ✅ Add document indexing capabilities cho knowledge base updates
- ✅ Use real embeddings từ `GoogleGenerativeAIEmbeddings`
- ✅ Implement proper error handling cho DB connection issues

### **2. Configuration Management:**
- ✅ Centralize tất cả constants trong `WorkflowConfig`
- ✅ Environment-based configuration loading
- ✅ Runtime configuration updates support
- ✅ Validation cho configuration parameters

### **3. Error Handling & Resilience:**
- ✅ Graceful degradation khi RAG fails
- ✅ Fallback responses cho LLM errors
- ✅ Retry logic cho transient failures
- ✅ Comprehensive logging với structured data

### **4. Performance Optimization:**
- ✅ Async/await throughout pipeline
- ✅ Batch processing cho multiple queries
- ✅ Caching strategies cho retrieved documents
- ✅ Connection pooling cho QdrantDB

## 📋 Reference Implementation Mapping

### **Study These Files:**
1. **`moneyez-ai-service/app/langgraph/rag_node.py`** - RAG implementation patterns
2. **`moneyez-ai-service/app/knowledge/vectordb.py`** - Vector DB integration
3. **`moneyez-ai-service/app/langgraph/state.py`** - State management
4. **`moneyez-ai-service/app/langgraph/agent.py`** - Agent coordination

### **Key Patterns to Follow:**
- ✅ Error boundary patterns from rag_node.py
- ✅ Database integration patterns from vectordb.py  
- ✅ State management from state.py
- ✅ Workflow orchestration from agent.py

## 🚀 Implementation Checklist

### **Phase 1: Structure Setup**
- [ ] Create folder structure
- [ ] Move AgentState to state/workflow_state.py
- [ ] Extract configuration to config/workflow_config.py
- [ ] Create utils modules

### **Phase 2: QdrantService Integration**
- [ ] Implement KnowledgeRetriever class
- [ ] Replace mock functions với real QdrantService calls
- [ ] Add query optimization logic
- [ ] Implement document ranking algorithms

### **Phase 3: Node Refactoring**
- [ ] Extract RAG nodes to nodes/rag_nodes.py
- [ ] Extract agent nodes to nodes/agent_nodes.py
- [ ] Extract tool nodes to nodes/tool_nodes.py
- [ ] Implement error handling trong all nodes

### **Phase 4: Integration & Testing**
- [ ] Update main workflow assembly
- [ ] Test RAG pipeline end-to-end
- [ ] Validate QdrantService integration
- [ ] Performance testing & optimization

### **Phase 5: Production Readiness**
- [ ] Add comprehensive logging
- [ ] Implement monitoring hooks
- [ ] Add configuration validation
- [ ] Documentation & examples

## 💡 Success Criteria

### **Functional Requirements:**
- ✅ Modular, maintainable code structure
- ✅ Real QdrantService integration working
- ✅ Vietnamese financial knowledge retrieval
- ✅ Production-ready error handling
- ✅ Configurable workflow parameters

### **Technical Requirements:**
- ✅ <2s response time cho RAG queries
- ✅ >95% uptime với graceful degradation
- ✅ Memory efficient document processing
- ✅ Scalable architecture patterns
- ✅ Comprehensive test coverage

### **Documentation Requirements:**
- ✅ Clear module documentation
- ✅ Configuration guide
- ✅ Deployment instructions
- ✅ Troubleshooting guide
- ✅ Performance tuning tips

## 🎯 Next Steps

1. **Start with Phase 1**: Create folder structure và move AgentState
2. **Implement QdrantService integration**: Replace mock functions
3. **Test thoroughly**: Ensure RAG pipeline works end-to-end  
4. **Optimize performance**: Tune query processing và retrieval
5. **Add monitoring**: Implement logging và metrics collection

This implementation will transform your monolithic workflow into a production-ready, modular LangGraph system với real knowledge base capabilities! 🚀
