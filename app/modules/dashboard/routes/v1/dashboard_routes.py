"""Dashboard API Routes"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.base_model import APIResponse
from app.modules.dashboard.services.dashboard_service import DashboardService
from app.modules.dashboard.schemas.dashboard_schemas import (
    OverviewStatsResponse,
    UserAnalyticsResponse,
    UserGrowthStatsResponse,
    RevenueAnalyticsResponse,
    ChatAnalyticsResponse,
    ChatUsageStatsResponse,
    FileAnalyticsResponse,
    SessionAnalyticsResponse,
    AgentAnalyticsResponse,
    ActivityLogsResponse,
    RecentActivityResponse,
    SystemHealthResponse,
    DashboardDateRangeRequest,
    ActivityLogRequest
)
from app.middleware.auth_middleware import require_auth
from app.enums.user_enums import UserRoleEnum

route = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@route.get("/overview", response_model=APIResponse[OverviewStatsResponse])
async def get_overview_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/overview**
    
    Lấy thống kê tổng quan của hệ thống dashboard.
    
    **Tham số đầu vào:**
    - `start_date` (optional): Ngày bắt đầu để lọc dữ liệu
    - `end_date` (optional): Ngày kết thúc để lọc dữ liệu
    
    **Logic xử lý:**
    - Tổng hợp số liệu từ tất cả các module: Users, Conversations, Messages, Payments, Files, Question Sessions
    - Tính toán số liệu hoạt động theo ngày/tuần/tháng
    - Thống kê doanh thu và giao dịch
    
    **Dữ liệu trả về:**
    - Tổng số người dùng và người dùng hoạt động
    - Thống kê cuộc trò chuyện và tin nhắn
    - Doanh thu và thống kê thanh toán
    - Thông tin file và storage
    - Số liệu question sessions
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        
        request = None
        if start_date or end_date:
            request = DashboardDateRangeRequest(start_date=start_date, end_date=end_date)
        
        stats = await service.get_overview_stats(request)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê tổng quan thành công",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê tổng quan: {str(e)}")


@route.get("/users", response_model=APIResponse[UserAnalyticsResponse])
async def get_user_analytics(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    order_by: str = Query("create_date", description="Trường sắp xếp"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Hướng sắp xếp"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/users**
    
    Lấy thống kê chi tiết về người dùng với phân trang.
    
    **Tham số đầu vào:**
    - `page`: Số trang (mặc định: 1)
    - `page_size`: Số item trên trang (mặc định: 20, tối đa: 100)
    - `order_by`: Trường để sắp xếp (mặc định: create_date)
    - `order_direction`: Hướng sắp xếp asc/desc (mặc định: desc)
    
    **Logic xử lý:**
    - Join User với Conversation, Message, File để lấy số liệu hoạt động
    - Áp dụng phân trang và sắp xếp
    - Tính toán số conversations, messages, files cho mỗi user
    
    **Dữ liệu trả về:**
    - Danh sách user với thống kê hoạt động
    - Thông tin phân trang
    - Role và rank distribution
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        analytics = await service.get_user_analytics(page, page_size, order_by, order_direction)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê người dùng thành công",
            data=analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê người dùng: {str(e)}")


@route.get("/users/growth", response_model=APIResponse[UserGrowthStatsResponse])
async def get_user_growth_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/users/growth**
    
    Lấy thống kê tăng trưởng người dùng theo thời gian.
    
    **Logic xử lý:**
    - Thống kê đăng ký mới theo ngày (30 ngày gần nhất)
    - Thống kê tăng trưởng theo tháng (12 tháng gần nhất)
    - Phân bố theo role và subscription rank
    
    **Dữ liệu trả về:**
    - Biểu đồ tăng trưởng hàng ngày và hàng tháng
    - Phân bố người dùng theo role
    - Phân bố theo subscription rank
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        growth_stats = await service.get_user_growth_stats()
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê tăng trưởng người dùng thành công",
            data=growth_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê tăng trưởng: {str(e)}")


@route.get("/revenue", response_model=APIResponse[RevenueAnalyticsResponse])
async def get_revenue_analytics(
    start_date: Optional[datetime] = Query(None, description="Ngày bắt đầu"),
    end_date: Optional[datetime] = Query(None, description="Ngày kết thúc"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/revenue**
    
    Lấy thống kê doanh thu và thanh toán.
    
    **Tham số đầu vào:**
    - `start_date` (optional): Ngày bắt đầu lọc
    - `end_date` (optional): Ngày kết thúc lọc
    
    **Logic xử lý:**
    - Tổng hợp doanh thu từ Payment table (chỉ status COMPLETED)
    - Thống kê theo ngày, tháng trong khoảng thời gian
    - Phân tích doanh thu theo subscription rank
    - Tính giá trị giao dịch trung bình
    
    **Dữ liệu trả về:**
    - Doanh thu theo ngày và tháng
    - Phân bố doanh thu theo subscription rank
    - Tổng doanh thu và giá trị giao dịch trung bình
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        
        request = None
        if start_date or end_date:
            request = DashboardDateRangeRequest(start_date=start_date, end_date=end_date)
        
        revenue_stats = await service.get_revenue_analytics(request)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê doanh thu thành công",
            data=revenue_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê doanh thu: {str(e)}")


@route.get("/chat", response_model=APIResponse[ChatAnalyticsResponse])
async def get_chat_analytics(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/chat**
    
    Lấy thống kê về hệ thống chat và conversations.
    
    **Tham số đầu vào:**
    - `page`: Số trang
    - `page_size`: Số item trên trang
    
    **Logic xử lý:**
    - Join Conversation với User để lấy thông tin chủ sở hữu
    - Join với File để đếm số file trong conversation
    - Tính toán conversation hoạt động nhất
    - Sắp xếp theo hoạt động gần nhất
    
    **Dữ liệu trả về:**
    - Danh sách conversations với thống kê
    - Conversations hoạt động nhất
    - Conversations gần đây nhất
    - Tổng số conversations và messages
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        chat_analytics = await service.get_chat_analytics(page, page_size)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê chat thành công",
            data=chat_analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê chat: {str(e)}")


@route.get("/chat/usage", response_model=APIResponse[ChatUsageStatsResponse])
async def get_chat_usage_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/chat/usage**
    
    Lấy thống kê sử dụng chat theo thời gian và patterns.
    
    **Logic xử lý:**
    - Thống kê conversations và messages theo ngày (30 ngày gần nhất)
    - Phân bố hoạt động theo giờ trong ngày
    - Tính toán user engagement metrics
    
    **Dữ liệu trả về:**
    - Biểu đồ hoạt động hàng ngày
    - Phân bố theo giờ (0-23h)
    - Metrics về user engagement
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        usage_stats = await service.get_chat_usage_stats()
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê sử dụng chat thành công",
            data=usage_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê sử dụng chat: {str(e)}")


@route.get("/files", response_model=APIResponse[FileAnalyticsResponse])
async def get_file_analytics(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/files**
    
    Lấy thống kê về file uploads và storage.
    
    **Tham số đầu vào:**
    - `page`: Số trang
    - `page_size`: Số item trên trang
    
    **Logic xử lý:**
    - Join File với User để lấy thông tin uploader
    - Thống kê theo file type
    - Sắp xếp theo upload date
    - Tính toán storage metrics
    
    **Dữ liệu trả về:**
    - Danh sách files với thông tin chi tiết
    - Phân bố theo file type
    - Files upload gần đây nhất
    - Files được download nhiều nhất
    - Tổng storage size
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        file_analytics = await service.get_file_analytics(page, page_size)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê file thành công",
            data=file_analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê file: {str(e)}")


@route.get("/sessions", response_model=APIResponse[SessionAnalyticsResponse])
async def get_session_analytics(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/sessions**
    
    Lấy thống kê về Question Sessions và Surveys.
    
    **Tham số đầu vào:**
    - `page`: Số trang
    - `page_size`: Số item trên trang
    
    **Logic xử lý:**
    - Join QuestionSession với User và QuestionAnswer
    - Tính completion rate cho mỗi session
    - Thống kê theo session type và status
    - Sắp xếp theo ngày tạo
    
    **Dữ liệu trả về:**
    - Danh sách sessions với completion rate
    - Phân bố theo session type
    - Phân bố theo status
    - Sessions gần đây nhất
    - Tổng completion rate
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        session_analytics = await service.get_session_analytics(page, page_size)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê session thành công",
            data=session_analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê session: {str(e)}")


@route.get("/agents", response_model=APIResponse[AgentAnalyticsResponse])
async def get_agent_analytics(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/agents**
    
    Lấy thống kê về AI Agents và model usage.
    
    **Tham số đầu vào:**
    - `page`: Số trang
    - `page_size`: Số item trên trang
    
    **Logic xử lý:**
    - Join Agent với User để lấy thông tin owner
    - Thống kê theo model provider và model name
    - Đếm agents active/inactive
    - Tính usage metrics (cần implement)
    
    **Dữ liệu trả về:**
    - Danh sách agents với thông tin chi tiết
    - Phân bố theo model provider
    - Phân bố theo model name
    - Số agents active/inactive
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        agent_analytics = await service.get_agent_analytics(page, page_size)
        
        return APIResponse(
            error_code=0,
            message="Lấy thống kê agent thành công",
            data=agent_analytics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thống kê agent: {str(e)}")


@route.get("/activity", response_model=APIResponse[ActivityLogsResponse])
async def get_activity_logs(
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số item trên trang"),
    user_id: Optional[str] = Query(None, description="Lọc theo user ID"),
    action: Optional[str] = Query(None, description="Lọc theo action type"),
    start_date: Optional[datetime] = Query(None, description="Ngày bắt đầu"),
    end_date: Optional[datetime] = Query(None, description="Ngày kết thúc"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/activity**
    
    Lấy logs hoạt động của người dùng trong hệ thống.
    
    **Tham số đầu vào:**
    - `page`: Số trang
    - `page_size`: Số item trên trang  
    - `user_id` (optional): Lọc theo user cụ thể
    - `action` (optional): Lọc theo loại action
    - `start_date` (optional): Ngày bắt đầu
    - `end_date` (optional): Ngày kết thúc
    
    **Logic xử lý:**
    - Join UserLog với User để lấy thông tin user
    - Áp dụng các filter được yêu cầu
    - Sắp xếp theo thời gian mới nhất
    - Phân trang kết quả
    
    **Dữ liệu trả về:**
    - Danh sách activity logs với thông tin chi tiết
    - Thông tin user thực hiện action
    - Chi tiết action và metadata
    - Thông tin phân trang
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        
        request = ActivityLogRequest(
            page=page,
            page_size=page_size,
            user_id=user_id,
            action=action,
            start_date=start_date,
            end_date=end_date
        )
        
        activity_logs = await service.get_activity_logs(request)
        
        return APIResponse(
            error_code=0,
            message="Lấy activity logs thành công",
            data=activity_logs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy activity logs: {str(e)}")


@route.get("/recent", response_model=APIResponse[RecentActivityResponse])
async def get_recent_activity(
    limit: int = Query(5, ge=1, le=20, description="Số item cho mỗi category"),
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]))
):
    """
    **GET /api/v1/dashboard/recent**
    
    Lấy hoạt động gần đây nhất từ tất cả các module.
    
    **Tham số đầu vào:**
    - `limit`: Số lượng item cho mỗi category (mặc định: 5, tối đa: 20)
    
    **Logic xử lý:**
    - Lấy users đăng ký gần đây nhất
    - Lấy conversations được tạo gần đây
    - Lấy files upload gần đây
    - Lấy payments gần đây
    - Lấy question sessions gần đây
    
    **Dữ liệu trả về:**
    - Recent users với thông tin cơ bản
    - Recent conversations với activity
    - Recent files với metadata
    - Recent payments với status
    - Recent question sessions với progress
    
    **Yêu cầu:** Admin hoặc Manager role
    """
    try:
        service = DashboardService(db)
        recent_activity = await service.get_recent_activity(limit)
        
        return APIResponse(
            error_code=0,
            message="Lấy hoạt động gần đây thành công",
            data=recent_activity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy hoạt động gần đây: {str(e)}")


@route.get("/health", response_model=APIResponse[SystemHealthResponse])
async def get_system_health(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN]))
):
    """
    **GET /api/v1/dashboard/health**
    
    Lấy thông tin sức khỏe và hiệu suất hệ thống.
    
    **Logic xử lý:**
    - Kiểm tra kết nối database
    - Đếm tổng số records trong các table chính
    - Tính toán storage usage
    - Đánh giá performance metrics
    
    **Dữ liệu trả về:**
    - Database connection status
    - Record counts cho tất cả tables
    - Storage information và indexing rate
    - Performance metrics
    - Timestamp của lần update cuối
    
    **Yêu cầu:** Admin role only
    """
    try:
        service = DashboardService(db)
        health_stats = await service.get_system_health()
        
        return APIResponse(
            error_code=0,
            message="Lấy thông tin sức khỏe hệ thống thành công",
            data=health_stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông tin sức khỏe hệ thống: {str(e)}")


# Additional utility endpoints
@route.post("/cache/refresh")
async def refresh_dashboard_cache(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN]))
):
    """
    **POST /api/v1/dashboard/cache/refresh**
    
    Refresh dashboard cache để cập nhật dữ liệu mới nhất.
    
    **Yêu cầu:** Admin role only
    """
    try:
        service = DashboardService(db)
        result = await service.refresh_dashboard_cache()
        
        return APIResponse(
            error_code=0,
            message="Refresh cache thành công" if result else "Refresh cache thất bại",
            data={"success": result}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi refresh cache: {str(e)}")


@route.get("/performance")
async def get_dashboard_performance(
    db: Session = Depends(get_db),
    current_user = Depends(require_auth([UserRoleEnum.ADMIN]))
):
    """
    **GET /api/v1/dashboard/performance**
    
    Lấy performance metrics của dashboard.
    
    **Yêu cầu:** Admin role only
    """
    try:
        service = DashboardService(db)
        performance = await service.get_dashboard_performance_metrics()
        
        return APIResponse(
            error_code=0,
            message="Lấy performance metrics thành công",
            data=performance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy performance metrics: {str(e)}")
