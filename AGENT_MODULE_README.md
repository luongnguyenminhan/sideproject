# Agent Module Documentation

## 📋 Tổng quan

Module Agent cung cấp hệ thống AI Agent sử dụng LangGraph để tích hợp liền mạch với hệ thống chat WebSocket hiện tại. Module tuân thủ nghiêm ngặt kiến trúc 3-layer và hỗ trợ nhiều loại agent với khả năng cấu hình linh hoạt.

## 🏗 Kiến trúc

### Cấu trúc Module
```
app/modules/chat/agent/
├── dal/                    # Data Access Layer
│   ├── agent_dal.py
│   ├── agent_config_dal.py
│   └── agent_memory_dal.py
├── models/                 # Database Models
│   ├── agent.py
│   ├── agent_config.py
│   └── agent_memory.py
├── repository/            # Business Logic Layer
│   ├── agent_repo.py
│   └── agent_workflow_repo.py
├── services/              # Service Layer
│   ├── langgraph_service.py
│   ├── agent_factory.py
│   ├── workflow_manager.py
│   └── agent_integration_service.py
├── schemas/               # Request/Response Schemas
│   ├── agent_request.py
│   └── agent_response.py
├── routes/                # API Routes
│   └── v1/
│       └── agent_routes.py
└── workflows/             # Workflow Implementations
    ├── base_workflow.py
    ├── chat_workflow.py
    └── analysis_workflow.py
```

### Luồng dữ liệu
```
WebSocket Request → Chat Route → Chat Repo → Agent Integration Service → Agent Workflow Repo → LangGraph Service → AI Response
```

## 🚀 Tính năng chính

### 1. Loại Agent
- **Chat Agent**: Đối thoại tự nhiên, ghi nhớ ngữ cảnh
- **Analysis Agent**: Phân tích dữ liệu, tạo insight
- **Task Agent**: Quản lý công việc, lập kế hoạch
- **Custom Agent**: Cấu hình tùy chỉnh

### 2. Model Provider hỗ trợ
- **OpenAI**: GPT-3.5, GPT-4, GPT-4o
- **Anthropic**: Claude-3 series
- **Google**: Gemini models
- **Groq**: Llama models với tốc độ cao
- **Ollama**: Models local

### 3. Tính năng nâng cao
- **Streaming Response**: Real-time response qua WebSocket
- **Memory Management**: Lưu trữ ngữ cảnh và trạng thái
- **Tool Integration**: Web search, memory retrieval
- **Workflow Customization**: Tùy chỉnh workflow theo nhu cầu

## 📊 Database Schema

### Tables
1. **agent_configs**: Cấu hình agent (model, prompt, tools)
2. **agents**: Thông tin agent của user
3. **agent_memories**: Bộ nhớ và ngữ cảnh agent

### Relationships
- Agent → AgentConfig (many-to-one)
- Agent → AgentMemory (one-to-many)
- Agent → User (many-to-one)

## 🔧 Installation

### 1. Cài đặt dependencies
```bash
pip install -r requirements_agent.txt
```

### 2. Chạy migration
```bash
alembic upgrade head
```

### 3. Cấu hình environment variables
```env
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Google
GOOGLE_API_KEY=your_google_key

# Groq
GROQ_API_KEY=your_groq_key

# Tavily (for web search)
TAVILY_API_KEY=your_tavily_key
```

## 📝 API Endpoints

### Agent Management
- `POST /api/v1/agents` - Tạo agent mới
- `GET /api/v1/agents` - Liệt kê agents của user
- `GET /api/v1/agents/{id}` - Lấy thông tin agent
- `PUT /api/v1/agents/{id}` - Cập nhật agent
- `DELETE /api/v1/agents/{id}` - Xóa agent

### Agent Operations
- `POST /api/v1/agents/{id}/chat` - Chat với agent (non-streaming)
- `POST /api/v1/agents/{id}/test` - Test agent response
- `GET /api/v1/agents/{id}/memory` - Lấy memory của agent
- `POST /api/v1/agents/{id}/memory/clear` - Xóa memory

### Utility Endpoints
- `GET /api/v1/agents/models/available` - Danh sách models
- `GET /api/v1/agents/templates/{type}` - Template cấu hình
- `POST /api/v1/agents/create-default` - Tạo agent mặc định
- `POST /api/v1/agents/create-custom` - Tạo agent tùy chỉnh

## 🌐 WebSocket Integration

Agent system tích hợp hoàn toàn với WebSocket chat hiện tại:

### Client Message Format
```json
{
  "type": "chat_message",
  "content": "Hello, how are you?",
  "api_key": "optional_api_key"
}
```

### Server Response Format
```json
{
  "type": "assistant_message_chunk",
  "content": "Hello! I'm doing well...",
  "full_content": "Complete response so far",
  "agent_id": "agent_uuid"
}
```

## 💾 Memory System

### Memory Types
- **SHORT_TERM**: Tạm thời, xóa sau session
- **LONG_TERM**: Dài hạn, quan trọng
- **CONTEXT**: Ngữ cảnh cuộc hội thoại
- **WORKFLOW_STATE**: Trạng thái workflow

### Memory Management
```python
# Lấy memory context
context = agent_integration.get_agent_conversation_context(
    agent_id, user_id, conversation_id
)

# Xóa memory
cleared = agent_integration.clear_agent_conversation_memory(
    agent_id, user_id, conversation_id
)
```

## 🔄 Workflow System

### Base Workflow
Tất cả workflows kế thừa từ `BaseWorkflow`:
```python
class CustomWorkflow(BaseWorkflow):
    async def execute(self, context, api_key=None):
        # Implementation
        pass
    
    async def execute_streaming(self, context, api_key=None):
        # Streaming implementation
        pass
```

### Workflow Types
- **ConversationalWorkflow**: Chat tự nhiên
- **AnalyticalWorkflow**: Phân tích có cấu trúc
- **TaskOrientedWorkflow**: Hướng công việc

## 🛠 Configuration Examples

### Chat Agent
```json
{
  "name": "My Chat Assistant",
  "agent_type": "chat",
  "model_provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "temperature": 0.7,
  "system_prompt": "You are a helpful assistant...",
  "tools_config": {
    "web_search": false,
    "memory_retrieval": true
  }
}
```

### Analysis Agent
```json
{
  "name": "Data Analyst",
  "agent_type": "analysis",
  "model_provider": "openai", 
  "model_name": "gpt-4",
  "temperature": 0.3,
  "tools_config": {
    "web_search": true,
    "memory_retrieval": true,
    "custom_tools": ["data_visualization"]
  }
}
```

## 🔍 Testing

### Test Agent Response
```bash
curl -X POST "/api/v1/agents/{agent_id}/test" \
  -H "Content-Type: application/json" \
  -d '{
    "test_message": "Hello, how are you?",
    "api_key": "optional_key"
  }'
```

### WebSocket Testing
```javascript
const ws = new WebSocket('ws://localhost:8000/chat/ws/{conversation_id}?token={ws_token}');

ws.send(JSON.stringify({
  type: 'chat_message',
  content: 'Hello from agent system!'
}));
```

## 🚨 Error Handling

### Fallback System
Khi agent system lỗi, hệ thống tự động fallback về simulation:
```python
try:
    result = await agent_integration.get_ai_response(...)
except Exception:
    # Automatic fallback to simulation
    result = await fallback_simulation(...)
```

### Error Types
- **Agent Not Found**: Agent không tồn tại
- **Invalid Configuration**: Cấu hình không hợp lệ
- **Model Provider Error**: Lỗi từ model provider
- **Workflow Execution Error**: Lỗi thực thi workflow

## 📈 Performance

### Optimization
- Database indexing cho queries nhanh
- Memory caching cho agent configs
- Async processing cho streaming
- Connection pooling cho LLM providers

### Monitoring
- Response time tracking
- Token usage monitoring
- Error rate tracking
- Memory usage statistics

## 🔐 Security

### API Key Management
- Keys được encrypt trong database
- Per-user key isolation
- Automatic key rotation support

### User Isolation
- Agents isolated per user
- Memory separation
- Access control validation

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] API keys secured
- [ ] Monitoring enabled
- [ ] Fallback system tested

### Docker Support
Agent module hoàn toàn tương thích với Docker deployment hiện tại.

## 🔮 Future Enhancements

### Planned Features
- Custom tool development framework
- Multi-agent conversations
- Agent performance analytics
- Visual workflow builder
- Integration with external APIs

### Scalability
- Horizontal scaling support
- Load balancing for LLM calls
- Distributed memory storage
- Caching optimization

## 🤝 Contributing

### Development Guidelines
1. Follow 3-layer architecture strictly
2. Add comprehensive tests
3. Document all new features
4. Follow existing code patterns
5. Update migration scripts

### Code Review Checklist
- [ ] Architecture compliance
- [ ] Error handling
- [ ] Performance considerations
- [ ] Security validation
- [ ] Documentation updated

---

## 📞 Support

Để hỗ trợ và báo lỗi, vui lòng tạo issue trên repository hoặc liên hệ team development.