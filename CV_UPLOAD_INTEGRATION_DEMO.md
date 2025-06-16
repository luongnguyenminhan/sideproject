# 🚀 **CV Upload Integration - Complete Implementation**

## **📋 Tổng quan Implementation**

• **File Upload**: `/api/v1/chat/upload-cv` endpoint để upload CV files  
• **CV Extraction**: Tích hợp với `cv_extraction` module để phân tích toàn bộ CV  
• **Storage**: Lưu trữ file trong MinIO và full JSON analysis trong conversation metadata  
• **Agent Integration**: CV context được load như tool trong ChatWorkflow  
• **RAG Enhancement**: CV info được dùng để enhance RAG queries  

---

## **🔧 API Endpoints**

### **1. Upload CV**
```http
POST /api/v1/chat/upload-cv
Content-Type: multipart/form-data
Authorization: Bearer <token>

Parameters:
- file: [CV file - PDF/DOC/DOCX] (required)
- conversation_id: [UUID] (optional)
```

**Response Success:**
```json
{
  "error_code": 0,
  "message": "Tải CV lên thành công",
  "data": {
    "file_path": "cv_files/user123/uuid.pdf",
    "cv_summary": "Senior Developer với 5 năm kinh nghiệm React, Node.js...",
    "personal_info": {
      "full_name": "Nguyễn Văn A",
      "email": "nguyenvana@email.com",
      "phone": "0123456789",
      "location": "Hà Nội"
    },
    "skills_count": 15,
    "experience_count": 3
  }
}
```

---

## **🏗️ Architecture Implementation**

### **1. File Upload Flow**
```
User Upload CV → chat_route.py → MinIO Storage → CV Extraction → Store Context
```

### **2. Chat Integration Flow** 
```
User Message → ChatWorkflow → CV Context Tool → Enhanced Response
```

### **3. RAG Enhancement Flow**
```
User Query → CV RAG Enhancement Tool → Enhanced Query → Better Results
```

---

## **📁 Files Created/Modified**

### **✅ New Files Created:**

**1. CV Integration Service**
- `app/modules/chat/services/cv_integration_service.py`
- Extract CV từ MinIO files
- Store full JSON context trong conversation metadata
- Provide CV context cho chat prompts

**2. CV Context Tool** 
- `app/modules/agent/tools/cv_context_tool.py`
- LangChain tool để access CV information
- Format comprehensive CV context cho agent
- Include personal info, skills, experience, education, projects

**3. CV RAG Enhancement Tool**
- `app/modules/agent/tools/cv_rag_enhancement_tool.py` 
- Enhance RAG queries với CV context
- Add skills, experience level, industry context
- Improve search relevance based on user background

### **✅ Files Modified:**

**1. Chat Route**
- `app/modules/chat/routes/v1/chat_route.py`
- Added `/upload-cv` endpoint
- Integrate với CV extraction service
- File validation và MinIO upload

**2. Workflow Tools**
- `app/modules/agent/workflows/chat_workflow/tools/basic_tools.py`
- Added CV tools to workflow
- Dynamic tool loading based on db_session availability

**3. Workflow Config**
- `app/modules/agent/workflows/chat_workflow/config/workflow_config.py`
- Added `db_session` field for CV tools

**4. ChatWorkflow**
- `app/modules/agent/workflows/chat_workflow/__init__.py`
- Pass db_session to config for CV tools

**5. Translation**
- `app/locales/vi.json`
- Added CV-related translation keys

---

## **🎯 Usage Examples**

### **1. Upload CV via API**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/upload-cv" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mycv.pdf" \
  -F "conversation_id=123e4567-e89b-12d3-a456-426614174000"
```

### **2. Chat với CV Context**
```json
{
  "type": "chat_message", 
  "content": "Tư vấn cho tôi về cơ hội việc làm phù hợp"
}
```

**Agent Response:**
```
Dựa trên CV của bạn, tôi thấy bạn có:
- 5 năm kinh nghiệm làm Senior Developer
- Kỹ năng mạnh về React, Node.js, Python
- Kinh nghiệm trong lĩnh vực Fintech

Tôi khuyên bạn nên tìm hiểu các vị trí:
1. Tech Lead tại các startup Fintech
2. Senior Full-stack Developer tại các công ty công nghệ
3. Solution Architect cho các dự án digital transformation

Bạn có muốn tôi tìm các khóa học để nâng cao kỹ năng leadership không?
```

### **3. RAG Query Enhancement**
```
Original Query: "Khóa học lập trình nào phù hợp?"
Enhanced Query: "Khóa học lập trình nào phù hợp? [User Context: Skills: React, Node.js, Python | Senior level professional | Industry experience: Technology]"
```

---

## **⚙️ Technical Details**

### **1. CV Context Storage**
```json
{
  "cv_context": {
    "cv_uploaded": true,
    "full_cv_analysis": {
      // Complete CV extraction JSON from cv_extraction module
      "cv_summary": "...",
      "personal_information": {...},
      "skills_summary": {...},
      "work_experience_history": {...},
      "education_history": {...},
      "projects_showcase": {...},
      "certificates_and_courses": {...}
    },
    "cv_summary": "Senior Developer...",
    "personal_info": {...},
    "skills": ["React", "Node.js", "Python"],
    "experience_count": 3,
    "education_count": 2
  }
}
```

### **2. Agent Tools Available**
- **cv_context**: Lấy full CV information
- **cv_rag_enhancement**: Enhance queries với CV context  
- **add/subtract/multiply/divide**: Basic math tools
- **Built-in RAG**: Knowledge base search

### **3. RAG Enhancement Logic**
- Skills matching với query keywords
- Experience level context (Junior/Mid/Senior)
- Industry/domain context extraction
- Role background analysis
- Education relevance detection

---

## **🔒 Security & Privacy**

• **File Validation**: Chỉ accept .pdf, .doc, .docx files  
• **User Authorization**: Require valid JWT token  
• **Data Privacy**: CV data chỉ accessible bởi user owner  
• **Storage**: Files stored trong MinIO với user-specific paths  
• **Metadata**: Full JSON stored in conversation metadata  

---

## **🚀 Production Ready Features**

• **Error Handling**: Comprehensive exception handling  
• **Logging**: Detailed logging cho debugging  
• **Circular Import Fix**: Resolved import dependencies  
• **Translation Support**: Vietnamese UI messages  
• **Scalable Architecture**: Tool-based modular design  
• **MinIO Integration**: Production file storage  
• **Database Storage**: Persistent CV context  

---

## **📈 Benefits**

### **For Users:**
• Upload CV một lần, chat với context mãi mãi  
• Personalized career advice based on real CV  
• Better job matching và skill recommendations  
• Relevant course/certification suggestions  

### **For System:**
• Enhanced RAG search với user context  
• Better conversation relevance  
• Structured CV data storage  
• Extensible tool architecture  

---

## **🔄 Workflow Integration**

### **ChatWorkflow Process:**
1. User sends message
2. ChatWorkflow checks for CV context via `cv_context` tool
3. If CV exists, load comprehensive user information
4. Use `cv_rag_enhancement` tool to enhance RAG queries
5. Generate personalized response based on user background
6. Return contextually relevant advice

### **Tool Execution Example:**
```python
# ChatWorkflow automatically calls:
cv_info = cv_context_tool.run(conversation_id, user_id)
enhanced_query = cv_rag_enhancement_tool.run(conversation_id, user_id, user_message)
rag_results = knowledge_base.search(enhanced_query)
response = generate_response(cv_info, rag_results, user_message)
```

---

## **⚡ Next Steps**

• **Frontend Integration**: UI components để upload CV  
• **Advanced Matching**: ML-based job/course matching  
• **CV Analytics**: Skills gap analysis  
• **Multi-language**: Support English CVs  
• **Resume Builder**: Generate updated CV suggestions  
• **Career Tracking**: Monitor career progression over time  

---

**🎉 Implementation Complete! Ready for production use with full CV integration into chat system.** 