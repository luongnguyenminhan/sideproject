# Migration từ MongoDB sang MySQL - Chat Module

## 📋 Tổng quan
Project đã được chuyển từ hybrid storage (MySQL + MongoDB) sang hoàn toàn MySQL cho chat module.

## 🔄 Những thay đổi đã thực hiện

### 1. **Repository Layer**
- ✅ **ChatRepo** (`app/modules/chat/repository/chat_repo.py`)
  - Xóa import `mongodb_service`
  - Chuyển `create_message()` để chỉ lưu vào MySQL
  - Cập nhật `get_ai_response()` và `get_ai_response_streaming()` để lấy history từ MySQL
  
- ✅ **ConversationRepo** (`app/modules/chat/repository/conversation_repo.py`)
  - Xóa import `mongodb_service`
  - Cập nhật `delete_conversation()` để chỉ xóa trong MySQL
  - Thêm logic soft delete messages khi xóa conversation

### 2. **DAL Layer**
- ✅ **MessageDAL** (`app/modules/chat/dal/message_dal.py`)
  - Thêm method `soft_delete_by_conversation()` để xóa messages theo conversation
  - Đã có sẵn các methods: `get_conversation_history()`, `get_conversation_messages()`

### 3. **Models**
- ✅ **Message Model** (`app/modules/chat/models/message.py`)
  - Cập nhật comment để phản ánh việc lưu trữ hoàn toàn trong MySQL

## 📊 Dữ liệu hiện tại

### Messages được lưu trong MySQL
```sql
-- Table: messages
- id (UUID, PK)
- conversation_id (FK)
- user_id (FK) 
- role (enum: user/assistant)
- content (Text) -- Toàn bộ nội dung message
- timestamp
- model_used
- tokens_used (JSON string)
- response_time_ms
- create_date, update_date, is_deleted (từ BaseEntity)
```

## 🚀 Migration dữ liệu cũ

Nếu bạn có dữ liệu cũ trong MongoDB:

1. **Chạy migration script**:
```bash
python scripts/migrate_mongodb_to_mysql.py
```

2. **Cập nhật script** với logic MongoDB thực tế của bạn
3. **Kiểm tra dữ liệu** sau khi migrate
4. **Backup MongoDB** trước khi xóa

## 🔍 Kiểm tra sau migration

### 1. **API Endpoints hoạt động bình thường**
- ✅ Tạo conversation 
- ✅ Gửi message
- ✅ Lấy conversation history
- ✅ Xóa conversation (soft delete messages)

### 2. **Database queries**
```sql
-- Kiểm tra messages được lưu đầy đủ
SELECT COUNT(*) FROM messages WHERE is_deleted = false;

-- Kiểm tra content được lưu
SELECT id, role, SUBSTRING(content, 1, 50) as content_preview 
FROM messages 
WHERE conversation_id = 'your-conversation-id'
ORDER BY timestamp;
```

## 📈 Performance Benefits

### Trước (MySQL + MongoDB)
- ❌ 2 database systems cần maintain
- ❌ Data consistency issues 
- ❌ Complex error handling
- ❌ Network latency giữa databases

### Sau (MySQL only)
- ✅ Single source of truth
- ✅ ACID transactions 
- ✅ Simpler architecture
- ✅ Better performance với proper indexing

## 🛠️ Recommended Indexes

```sql
-- Indexes cho optimal performance
CREATE INDEX idx_messages_conversation_timestamp 
ON messages(conversation_id, timestamp DESC) 
WHERE is_deleted = false;

CREATE INDEX idx_messages_user_timestamp 
ON messages(user_id, timestamp DESC) 
WHERE is_deleted = false;

CREATE INDEX idx_messages_role 
ON messages(role) 
WHERE is_deleted = false;
```

## 🔧 Cleanup sau migration

1. **Xóa MongoDB service** (nếu không dùng cho module khác)
2. **Remove MongoDB Docker container**
3. **Update environment variables**
4. **Clean up old MongoDB config files**

## ⚠️ Lưu ý quan trọng

- **Backup dữ liệu** trước khi migration
- **Test thoroughly** tất cả chat functionality
- **Monitor performance** sau khi chuyển
- **Update documentation** và API docs nếu cần
- **Inform team** về thay đổi architecture 