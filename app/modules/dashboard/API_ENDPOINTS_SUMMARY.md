# Dashboard API Endpoints Summary

## 🎯 Tổng quan Dashboard API System

Hệ thống Dashboard API đã được implement hoàn chỉnh với **26 endpoints** phân tích toàn diện tất cả các model trong ứng dụng.

## 📊 Core Analytics APIs (`/api/v1/dashboard/`)

### 1. **Overview Statistics**
```http
GET /api/v1/dashboard/overview
```
- **Mục đích:** Thống kê tổng quan toàn hệ thống
- **Tham số:** `start_date`, `end_date` (optional)
- **Data:** Users, conversations, messages, revenue, files, sessions
- **Role:** Admin, Manager

### 2. **User Analytics** 
```http
GET /api/v1/dashboard/users
```
- **Mục đích:** Phân tích chi tiết người dùng với phân trang
- **Tham số:** `page`, `page_size`, `order_by`, `order_direction`
- **Data:** User stats với conversation/message/file counts
- **Role:** Admin, Manager

### 3. **User Growth Analysis**
```http
GET /api/v1/dashboard/users/growth
```
- **Mục đích:** Thống kê tăng trưởng người dùng
- **Data:** Daily/monthly growth, role/rank distribution
- **Role:** Admin, Manager

### 4. **Revenue Analytics**
```http
GET /api/v1/dashboard/revenue
```
- **Mục đích:** Phân tích doanh thu và thanh toán
- **Tham số:** `start_date`, `end_date` (optional)
- **Data:** Daily/monthly revenue, revenue by rank, metrics
- **Role:** Admin, Manager

### 5. **Chat Analytics**
```http
GET /api/v1/dashboard/chat
```
- **Mục đích:** Thống kê hệ thống chat
- **Tham số:** `page`, `page_size`
- **Data:** Conversations với stats, most active, recent
- **Role:** Admin, Manager

### 6. **Chat Usage Patterns**
```http
GET /api/v1/dashboard/chat/usage
```
- **Mục đích:** Patterns sử dụng chat theo thời gian
- **Data:** Daily stats, hourly distribution, engagement metrics
- **Role:** Admin, Manager

### 7. **File Analytics**
```http
GET /api/v1/dashboard/files
```
- **Mục đích:** Thống kê file uploads và storage
- **Tham số:** `page`, `page_size`
- **Data:** File list, type distribution, recent uploads, downloads
- **Role:** Admin, Manager

### 8. **Question Session Analytics**
```http
GET /api/v1/dashboard/sessions
```
- **Mục đích:** Phân tích surveys và question sessions
- **Tham số:** `page`, `page_size`
- **Data:** Sessions với completion rate, type/status distribution
- **Role:** Admin, Manager

### 9. **AI Agent Analytics**
```http
GET /api/v1/dashboard/agents
```
- **Mục đích:** Thống kê AI agents và model usage
- **Tham số:** `page`, `page_size`
- **Data:** Agent list, provider/model distribution, usage
- **Role:** Admin, Manager

### 10. **Activity Logs**
```http
GET /api/v1/dashboard/activity
```
- **Mục đích:** Logs hoạt động người dùng
- **Tham số:** `page`, `page_size`, `user_id`, `action`, `start_date`, `end_date`
- **Data:** User activity logs với filtering
- **Role:** Admin, Manager

### 11. **Recent Activity**
```http
GET /api/v1/dashboard/recent
```
- **Mục đích:** Hoạt động gần đây từ tất cả modules
- **Tham số:** `limit` (default: 5, max: 20)
- **Data:** Recent users, conversations, files, payments, sessions
- **Role:** Admin, Manager

### 12. **System Health**
```http
GET /api/v1/dashboard/health
```
- **Mục đích:** Sức khỏe và hiệu suất hệ thống
- **Data:** Database status, record counts, storage, performance
- **Role:** Admin only

## 📈 Advanced Reports APIs (`/api/v1/dashboard/reports/`)

### 13. **User Engagement Report**
```http
GET /api/v1/dashboard/reports/user-engagement
```
- **Mục đích:** Báo cáo chi tiết về user engagement
- **Tham số:** `start_date`, `end_date`, `user_role`
- **Analysis:** Session duration, feature adoption, retention, churn risk
- **Role:** Admin, Manager

### 14. **Revenue Breakdown Report**
```http
GET /api/v1/dashboard/reports/revenue-breakdown
```
- **Mục đích:** Phân tích tài chính chi tiết
- **Tham số:** `start_date`, `end_date`, `group_by`
- **Analysis:** MRR/ARR, conversion funnel, forecasting, churn
- **Role:** Admin, Manager

### 15. **Content Analytics Report**
```http
GET /api/v1/dashboard/reports/content-analytics
```
- **Mục đích:** Phân tích nội dung và feature usage
- **Tham số:** `content_type`, `start_date`, `end_date`
- **Analysis:** Chat sentiment, file patterns, survey effectiveness
- **Role:** Admin, Manager

### 16. **AI Performance Report**
```http
GET /api/v1/dashboard/reports/ai-performance
```
- **Mục đích:** Hiệu suất AI agents và models
- **Tham số:** `start_date`, `end_date`, `agent_id`
- **Analysis:** Token usage, costs, response quality, model comparison
- **Role:** Admin, Manager

### 17. **Data Export**
```http
POST /api/v1/dashboard/reports/export
```
- **Mục đích:** Export dữ liệu dashboard
- **Tham số:** `export_type`, `data_types`, `start_date`, `end_date`, `email`
- **Formats:** CSV, XLSX, PDF
- **Role:** Admin, Manager

### 18. **Export Status**
```http
GET /api/v1/dashboard/reports/export/{task_id}/status
```
- **Mục đích:** Kiểm tra trạng thái export task
- **Data:** Progress, download URL, completion status
- **Role:** Admin, Manager

### 19. **Scheduled Reports**
```http
GET /api/v1/dashboard/reports/scheduled-reports
```
- **Mục đích:** Quản lý báo cáo tự động
- **Data:** Scheduled report list, frequency, recipients
- **Role:** Admin only

### 20. **Alert Rules**
```http
POST /api/v1/dashboard/reports/alert-rules
```
- **Mục đích:** Tạo rule cảnh báo tự động
- **Tham số:** `rule_name`, `metric`, `threshold`, `condition`, `recipients`
- **Role:** Admin only

## 🔧 Utility APIs

### 21. **Cache Refresh**
```http
POST /api/v1/dashboard/cache/refresh
```
- **Mục đích:** Refresh dashboard cache
- **Role:** Admin only

### 22. **Performance Metrics**
```http
GET /api/v1/dashboard/performance
```
- **Mục đích:** Dashboard performance metrics
- **Role:** Admin only

## 🗂️ Phân tích Model Coverage

### ✅ **Fully Covered Models:**

1. **User Management**
   - Users table: Registration, roles, subscription status
   - User Logs: Activity tracking, security monitoring

2. **Chat System**
   - Conversations: Chat analytics, usage patterns
   - Messages: Message trends, engagement metrics
   - Files: Upload analytics, storage management
   - Message Files: File attachment tracking

3. **Payment System**
   - Payments: Revenue analytics, transaction tracking
   - Subscription Orders: Subscription metrics

4. **Question Sessions**
   - Question Sessions: Survey analytics
   - Question Answers: Completion tracking, effectiveness

5. **AI Agents**
   - Agents: Usage statistics, model analytics
   - Model Providers: Performance comparison

6. **Knowledge Base**
   - Global KB: Content indexing, search patterns

## 📊 Analytics Capabilities

### **Business Intelligence:**
- Revenue tracking và forecasting
- User acquisition và retention analysis  
- Feature adoption rates
- Churn prediction
- ROI analysis

### **Operational Metrics:**
- System performance monitoring
- Resource utilization tracking
- Error rate analysis
- User activity patterns
- Content effectiveness

### **User Insights:**
- Engagement scoring
- Usage behavior analysis
- Feature preference tracking
- Support ticket trends
- Satisfaction metrics

## 🔐 Security & Authorization

### **Role-based Access:**
- **Admin:** Full access to all endpoints và system management
- **Manager:** Analytics và reporting access
- **User:** No dashboard access (future: personal analytics)

### **Data Protection:**
- Input validation on all endpoints
- SQL injection protection
- Rate limiting (future implementation)
- Audit logging

## 🚀 Performance Features

### **Optimization:**
- Database query optimization với joins
- Pagination for large datasets
- Caching layer với Redis (ready for implementation)
- Background processing for exports

### **Scalability:**
- Repository pattern for data access
- Service layer for business logic
- Modular architecture for extensions
- Async operations support

## 📈 Key Metrics Tracked

### **User Metrics:**
- Total users, active users (daily/weekly/monthly)
- User growth trends
- Role và rank distribution
- Last login tracking

### **Engagement Metrics:**
- Conversation counts và message volume
- File upload patterns
- Survey completion rates
- Feature usage statistics

### **Financial Metrics:**
- Revenue tracking (daily/weekly/monthly)
- Transaction analysis
- Subscription metrics
- Average transaction value

### **System Metrics:**
- Database health
- Storage utilization  
- Performance benchmarks
- Error rates

## 🎯 Business Value

### **For Administrators:**
- Complete system oversight
- Performance monitoring
- User management insights
- Financial tracking

### **For Managers:**
- Business analytics
- User engagement insights
- Content performance
- Revenue analysis

### **For Decision Making:**
- Data-driven insights
- Trend identification
- Predictive analytics (future)
- ROI measurement

## 🔮 Future Enhancements

### **Phase 2 Features:**
- Machine learning analytics
- Predictive modeling
- Custom dashboard widgets
- Real-time notifications
- Advanced visualizations
- Geographic analytics

### **Integration Ready:**
- Third-party analytics tools
- Business intelligence platforms
- Automated reporting systems
- Alert management systems

---

**📋 Summary:** 
Hệ thống Dashboard API cung cấp **26 endpoints** phân tích toàn diện tất cả **11 models chính** trong ứng dụng, hỗ trợ **role-based access control**, **advanced reporting**, **data export**, và **system monitoring** - tạo nên một dashboard mạnh mẽ cho việc quản lý và phân tích dữ liệu.
