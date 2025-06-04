# File Indexing Implementation for Conversation RAG

## Tổng quan

Implementation này tự động index các file của mỗi conversation vào Qdrant khi agent start, phục vụ RAG (Retrieval-Augmented Generation) để agent có thể truy vấn nội dung file trong conversation.

## Kiến trúc

### 1. Luồng hoạt động chính

```
User upload file → File lưu vào MinIO + metadata vào DB → Agent start conversation 
→ Check collection exists → Index files vào Qdrant → RAG search files + knowledge base
```

### 2. Các thành phần chính

#### A. FileExtractionService (`app/modules/chat/services/file_extraction_service.py`)
- **Chức năng**: Extract text từ các loại file khác nhau
- **Hỗ trợ**: PDF, DOCX, TXT, Markdown
- **Output**: Extracted text với metadata

#### B. ConversationFileIndexingService (`app/modules/agent/services/file_indexing_service.py`)
- **Chức năng**: Index files của conversation vào Qdrant
- **Tính năng**:
  - Tạo collection riêng cho mỗi conversation
  - Batch processing với error handling
  - Deduplication theo file_id

#### C. Enhanced LangGraphService (`app/modules/agent/services/langgraph_service.py`)
- **Tính năng mới**:
  - Auto-index files khi conversation start
  - Check collection existence để tránh index lại
  - Integration với workflow cho RAG

#### D. Enhanced Workflow (`app/modules/agent/workflows/chat_workflow/basic_workflow.py`)
- **RAG Enhancement**:
  - Search cả knowledge base và conversation files
  - Combine results với priority scoring
  - Context formatting cho model

## Chi tiết Implementation

### 1. File Text Extraction

```python
# FileExtractionService
file_extraction_service.extract_text_from_file(
    file_content=bytes,
    file_type="application/pdf",
    file_name="document.pdf"
)
# Returns: {content, file_name, file_type, char_count, extraction_success, extraction_error}
```

**Supported File Types:**
- `application/pdf` → PyPDF2
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` → python-docx
- `text/plain` → Direct decode
- `text/markdown` → Direct decode
- `application/msword` → Placeholder (chưa implement)

### 2. Conversation File Indexing

```python
# ConversationFileIndexingService
await service.index_conversation_files(
    conversation_id="uuid",
    files_data=[{
        'file_id': 'uuid',
        'file_name': 'document.pdf', 
        'file_type': 'application/pdf',
        'file_content': bytes
    }]
)
```

**Collection Naming:**
- Pattern: `conversation_{conversation_id}`
- Ví dụ: `conversation_123e4567-e89b-12d3-a456-426614174000`

### 3. Auto-Indexing in LangGraphService

```python
# Trong execute_conversation()
await self._ensure_conversation_files_indexed(conversation_id)

# Logic:
1. Check collection exists
2. Get files cần index
3. Extract text và index vào Qdrant
4. Mark files as indexed trong DB
```

### 4. Enhanced RAG in Workflow

```python
# Trong retrieve_knowledge()
# Search knowledge base
documents = await knowledge_retriever.retrieve_documents(queries)

# Search conversation files  
conversation_documents = file_indexing_service.search_conversation_context(
    conversation_id, query, top_k=3, score_threshold=0.6
)

# Combine results
all_documents = documents + conversation_documents
```

## Database Schema Updates

### File Model Fields
```sql
-- Existing fields
is_indexed BOOLEAN DEFAULT FALSE
indexed_at DATETIME NULL
indexing_error VARCHAR(1000) NULL
```

### File Status Tracking
- `is_indexed = False`: Chưa index
- `is_indexed = True`: Đã index thành công  
- `indexing_error != NULL`: Index failed với error message

## Configuration

### Required Dependencies
```txt
PyPDF2>=3.0.1
python-docx>=0.8.11
```

### Environment Variables
```env
# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_PATH=./qdrant_storage

# MinIO Configuration (existing)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=chat-files
MINIO_SECURE=false
```

## API Endpoints

### File Upload (Enhanced)
```
POST /files/upload
- Upload files với conversation_id
- Files tự động được index khi agent start conversation
```

### File Management
```
GET /files/conversation/{conversation_id}
- Lấy tất cả files của conversation
- Kiểm tra indexing status
```

## Error Handling

### 1. File Extraction Errors
- Unsupported file types → Log warning, skip file
- Extraction failures → Mark file với error message
- Empty content → Skip file

### 2. Indexing Errors  
- Qdrant connection failures → Log error, continue conversation
- Document creation errors → Mark specific files as failed
- Collection creation errors → Retry với exponential backoff

### 3. RAG Search Errors
- Collection not found → Return empty results
- Search failures → Fall back to knowledge base only
- No relevant documents → Continue với base prompt

## Performance Considerations

### 1. Indexing Optimization
- **Batch processing**: Index multiple files cùng lúc
- **Deduplication**: Skip files đã index
- **Async processing**: Non-blocking cho conversation flow

### 2. Search Optimization
- **Top-K limiting**: Max 3 conversation files + 5 knowledge docs
- **Score thresholds**: 0.6 for files, 0.7 for knowledge
- **Caching**: Collection existence check

### 3. Memory Management
- **Streaming extraction**: Process large files theo chunks
- **Cleanup**: Remove file content từ memory sau indexing
- **Connection pooling**: Reuse Qdrant connections

## Monitoring & Logging

### 1. Indexing Metrics
```python
logger.info(f'[FileIndexingService] Indexed {successful_files}/{total_files} files')
logger.info(f'[FileIndexingService] Collection: {collection_name}')
logger.info(f'[FileIndexingService] Processing time: {processing_time}ms')
```

### 2. RAG Performance
```python
logger.info(f'[RAG] Knowledge docs: {len(knowledge_docs)}')
logger.info(f'[RAG] Conversation docs: {len(conversation_docs)}')
logger.info(f'[RAG] Average relevance: {avg_score:.3f}')
```

### 3. Error Tracking
```python
logger.error(f'[FileExtraction] Failed: {file_name}, Error: {error}')
logger.warning(f'[Indexing] Skipped unsupported file: {file_type}')
```

## Testing Strategy

### 1. Unit Tests
- File extraction cho từng file type
- Document creation và indexing
- Search accuracy với different queries

### 2. Integration Tests  
- End-to-end file upload → index → search
- Multi-conversation isolation
- Error recovery scenarios

### 3. Performance Tests
- Large file handling (50MB PDFs)
- Multiple concurrent conversations
- Memory usage monitoring

## Future Enhancements

### 1. Additional File Types
- PowerPoint (.pptx) → python-pptx
- Excel (.xlsx) → openpyxl + pandas
- Images với OCR → pytesseract

### 2. Advanced Features
- Incremental indexing cho file updates
- Semantic chunking instead của fixed-size
- File versioning và change detection

### 3. Scalability
- Distributed indexing với Celery
- Sharded collections cho large conversations
- Caching layer với Redis

## Troubleshooting

### Common Issues

#### 1. "Collection not found"
```python
# Solution: Check Qdrant connection
service.check_collection_exists(conversation_id)
```

#### 2. "Extraction failed" 
```python
# Check file type support
if file_extraction_service.is_supported_file_type(file_type):
    # Process file
```

#### 3. "No relevant documents"
```python
# Lower score threshold hoặc expand search query
documents = service.search_conversation_context(
    conversation_id, query, score_threshold=0.5
)
```

#### 4. Memory issues với large files
```python
# Process files in smaller batches
batch_size = 10  # Reduce từ 50
```

## Deployment Notes

### 1. Resource Requirements
- **RAM**: +2GB cho embedding models
- **Storage**: Qdrant data directory
- **CPU**: Text extraction có thể intensive

### 2. Scaling Considerations
- **Horizontal**: Multiple worker instances
- **Vertical**: Tăng RAM cho large file processing
- **Storage**: Monitor Qdrant disk usage

### 3. Backup Strategy
- **Qdrant collections**: Export/import functionality
- **File metadata**: Database backups
- **MinIO files**: Backup policies 