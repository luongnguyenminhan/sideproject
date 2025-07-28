# Dashboard Module - Complete API Documentation

## Tổng quan

Module Dashboard cung cấp hệ thống API toàn diện để quản lý và phân tích dữ liệu từ tất cả các module trong ứng dụng. Hệ thống được thiết kế để hỗ trợ cả Admin và Manager trong việc theo dõi, phân tích và ra quyết định dựa trên dữ liệu.

## Kiến trúc Module

```
dashboard/
├── dal/                    # Data Access Layer
│   └── dashboard_dal.py   # Database operations
├── repository/            # Repository Pattern
│   └── dashboard_repository.py
├── services/              # Business Logic Layer
│   └── dashboard_service.py
├── schemas/               # Pydantic Models
│   └── dashboard_schemas.py
└── routes/                # API Routes
    └── v1/
        ├── dashboard_routes.py      # Main dashboard APIs
        └── dashboard_reports.py     # Reports & Analytics APIs
```

## Các Model được phân tích

Dashboard tích hợp dữ liệu từ tất cả các model chính:

### 1. **Users Management**
- User registrations, roles, subscription status
- Activity tracking, login patterns
- User engagement metrics

### 2. **Chat System**
- Conversations và Messages analytics
- Usage patterns, peak hours
- User interaction trends

### 3. **File Management**
- File uploads, storage analytics
- File type distribution
- Download patterns

### 4. **Payment & Revenue**
- Payment transactions, revenue tracking
- Subscription analytics
- Financial KPIs

### 5. **Question Sessions**
- Survey completion rates
- Question effectiveness
- User response analysis

### 6. **AI Agents**
- Agent usage statistics
- Model performance metrics
- Cost analysis

### 7. **Knowledge Base**
- Content indexing status
- Search patterns
- Content effectiveness

### 8. **User Activity Logs**
- Action tracking
- Security monitoring
- Audit trails

## API Endpoints

### Core Dashboard APIs (`/api/v1/dashboard/`)

#### 1. Overview Statistics
```http
GET /api/v1/dashboard/overview
```
**Mô tả:** Lấy thống kê tổng quan toàn hệ thống  
**Parameters:**
- `start_date` (optional): Ngày bắt đầu
- `end_date` (optional): Ngày kết thúc  
**Response:** Tổng hợp số liệu từ tất cả modules

#### 2. User Analytics
```http
GET /api/v1/dashboard/users
```
**Mô tả:** Phân tích chi tiết người dùng với phân trang  
**Parameters:**
- `page`: Số trang (default: 1)
- `page_size`: Kích thước trang (default: 20)
- `order_by`: Trường sắp xếp (default: create_date)
- `order_direction`: Hướng sắp xếp (asc/desc)

#### 3. User Growth Analysis
```http
GET /api/v1/dashboard/users/growth
```
**Mô tả:** Thống kê tăng trưởng người dùng theo thời gian  
**Response:** Biểu đồ tăng trưởng, phân bố role/rank

#### 4. Revenue Analytics
```http
GET /api/v1/dashboard/revenue
```
**Mô tả:** Phân tích doanh thu và thanh toán  
**Parameters:**
- `start_date` (optional): Ngày bắt đầu
- `end_date` (optional): Ngày kết thúc  
**Response:** Revenue breakdown, MRR, conversion rates

#### 5. Chat Analytics
```http
GET /api/v1/dashboard/chat
```
**Mô tả:** Thống kê hệ thống chat và conversations  
**Response:** Conversation metrics, active users, message trends

#### 6. Chat Usage Patterns
```http
GET /api/v1/dashboard/chat/usage
```
**Mô tả:** Patterns sử dụng chat theo thời gian  
**Response:** Hourly distribution, daily trends, engagement

#### 7. File Analytics
```http
GET /api/v1/dashboard/files
```
**Mô tả:** Thống kê file uploads và storage  
**Response:** File distribution, storage usage, popular types

#### 8. Question Session Analytics
```http
GET /api/v1/dashboard/sessions
```
**Mô tả:** Phân tích surveys và question sessions  
**Response:** Completion rates, session types, effectiveness

#### 9. AI Agent Analytics
```http
GET /api/v1/dashboard/agents
```
**Mô tả:** Thống kê AI agents và model usage  
**Response:** Usage metrics, model distribution, performance

#### 10. Activity Logs
```http
GET /api/v1/dashboard/activity
```
**Mô tả:** Logs hoạt động người dùng  
**Parameters:**
- `user_id` (optional): Lọc theo user
- `action` (optional): Lọc theo action type
- `start_date`, `end_date` (optional): Khoảng thời gian

#### 11. Recent Activity
```http
GET /api/v1/dashboard/recent
```
**Mô tả:** Hoạt động gần đây từ tất cả modules  
**Parameters:**
- `limit`: Số lượng items (default: 5, max: 20)

#### 12. System Health
```http
GET /api/v1/dashboard/health
```
**Mô tả:** Sức khỏe và hiệu suất hệ thống  
**Response:** Database status, record counts, performance metrics

### Advanced Reports APIs (`/api/v1/dashboard/reports/`)

#### 1. User Engagement Report
```http
GET /api/v1/dashboard/reports/user-engagement
```
**Mô tả:** Báo cáo chi tiết về mức độ tương tác người dùng  
**Analysis:** Session duration, feature adoption, retention, churn risk

#### 2. Revenue Breakdown Report
```http
GET /api/v1/dashboard/reports/revenue-breakdown
```
**Mô tả:** Phân tích tài chính chi tiết  
**Analysis:** MRR/ARR, conversion funnel, forecasting, churn analysis

#### 3. Content Analytics Report
```http
GET /api/v1/dashboard/reports/content-analytics
```
**Mô tả:** Phân tích nội dung và feature usage  
**Analysis:** Chat sentiment, file patterns, survey effectiveness

#### 4. AI Performance Report
```http
GET /api/v1/dashboard/reports/ai-performance
```
**Mô tả:** Hiệu suất AI agents và models  
**Analysis:** Token usage, costs, response quality, model comparison

#### 5. Data Export
```http
POST /api/v1/dashboard/reports/export
```
**Mô tả:** Export dữ liệu dashboard  
**Parameters:**
- `export_type`: Format (csv, xlsx, pdf)
- `data_types`: Loại dữ liệu cần export
- `email` (optional): Email nhận file

#### 6. Export Status
```http
GET /api/v1/dashboard/reports/export/{task_id}/status
```
**Mô tả:** Kiểm tra trạng thái export task

### Utility APIs

#### 1. Cache Management
```http
POST /api/v1/dashboard/cache/refresh
```
**Mô tả:** Refresh dashboard cache  
**Yêu cầu:** Admin role

#### 2. Performance Metrics
```http
GET /api/v1/dashboard/performance
```
**Mô tả:** Dashboard performance metrics  
**Yêu cầu:** Admin role

## Phân quyền (Authorization)

### Admin Role
- Toàn quyền truy cập tất cả APIs
- System health monitoring
- Cache management
- Alert rules configuration
- Scheduled reports setup

### Manager Role  
- Truy cập hầu hết analytics APIs
- User và revenue analytics
- Content và engagement reports
- Export functionality (limited)

### User Role
- Không có quyền truy cập dashboard APIs
- Chỉ có thể xem thống kê cá nhân (nếu implement)

## Tính năng nổi bật

### 1. **Real-time Analytics**
- Cập nhật số liệu theo thời gian thực
- Live dashboard updates
- Real-time alerting

### 2. **Advanced Filtering**
- Date range filtering
- Multi-dimensional filtering
- Dynamic query building

### 3. **Performance Optimization**
- Caching layer với Redis
- Database query optimization
- Pagination cho large datasets

### 4. **Data Export**
- Multiple format support (CSV, Excel, PDF)
- Background processing for large exports
- Email delivery for completed exports

### 5. **Comprehensive Coverage**
- Tích hợp tất cả modules hiện có
- Cross-module analytics
- Business intelligence insights

## Cách sử dụng

### 1. Dashboard Tổng quan
```python
# Lấy overview stats
response = await client.get("/api/v1/dashboard/overview")
stats = response.json()["data"]

print(f"Total Users: {stats['total_users']}")
print(f"Revenue This Month: ${stats['revenue_this_month']}")
```

### 2. User Analytics với Phân trang
```python
# Lấy user analytics trang 1
response = await client.get("/api/v1/dashboard/users?page=1&page_size=20")
analytics = response.json()["data"]

for user in analytics["user_stats"]:
    print(f"{user['email']}: {user['total_conversations']} conversations")
```

### 3. Revenue Analysis
```python
# Phân tích doanh thu tháng này
from datetime import datetime, timedelta

start_date = datetime.now().replace(day=1)
response = await client.get(f"/api/v1/dashboard/revenue?start_date={start_date}")
revenue_data = response.json()["data"]
```

### 4. Export Data
```python
# Export user data
export_response = await client.post("/api/v1/dashboard/reports/export", params={
    "export_type": "xlsx",
    "data_types": ["users", "revenue"],
    "email": "admin@example.com"
})

task_id = export_response.json()["data"]["task_id"]

# Check status
status_response = await client.get(f"/api/v1/dashboard/reports/export/{task_id}/status")
```

## Monitoring và Alerting

### 1. System Health Monitoring
- Database connection status
- Performance metrics tracking
- Storage usage monitoring

### 2. Business Metrics Alerts
- Revenue threshold alerts
- User activity anomalies
- System performance warnings

### 3. Scheduled Reports
- Daily/Weekly/Monthly reports
- Automated email delivery
- Custom report templates

## Roadmap và Tính năng tương lai

### Phase 2 Features
1. **Machine Learning Analytics**
   - Predictive analytics
   - Anomaly detection
   - Trend forecasting

2. **Custom Dashboards**
   - User-configurable widgets
   - Drag-and-drop dashboard builder
   - Personal dashboard for regular users

3. **Advanced Visualizations**
   - Interactive charts and graphs
   - Geographic analytics
   - Time-series analysis

4. **API Analytics**
   - Endpoint usage tracking
   - Performance monitoring
   - Rate limiting analytics

## Kết luận

Hệ thống Dashboard này cung cấp một giải pháp toàn diện cho việc quản lý và phân tích dữ liệu trong ứng dụng. Với thiết kế modular và extensible, nó có thể dễ dàng được mở rộng để thêm các tính năng mới và tích hợp với các module khác trong tương lai.

Hệ thống tuân thủ các best practices của FastAPI, có performance tốt với caching và pagination, và cung cấp authorization phù hợp cho các role khác nhau trong tổ chức.
