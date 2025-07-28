"""Dashboard Service Layer"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from app.modules.dashboard.dal.dashboard_dal import DashboardDAL
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


class DashboardService:
    """Service layer for dashboard operations"""

    def __init__(self, db: Session):
        self.db = db
        self.dal = DashboardDAL(db)

    async def get_overview_stats(self, request: Optional[DashboardDateRangeRequest] = None) -> OverviewStatsResponse:
        """Get general overview statistics"""
        
        start_date = request.start_date if request else None
        end_date = request.end_date if request else None
        
        stats = self.dal.get_overview_stats(start_date, end_date)
        return OverviewStatsResponse(**stats)

    async def get_user_analytics(self, page: int = 1, page_size: int = 20,
                               order_by: str = "create_date", order_direction: str = "desc") -> UserAnalyticsResponse:
        """Get detailed user analytics"""
        
        user_stats, total_count = self.dal.get_user_analytics(page, page_size, order_by, order_direction)
        
        return UserAnalyticsResponse(
            user_stats=user_stats,
            total_count=total_count,
            page=page,
            page_size=page_size
        )

    async def get_user_growth_stats(self) -> UserGrowthStatsResponse:
        """Get user growth statistics"""
        
        growth_stats = self.dal.get_user_growth_stats()
        return UserGrowthStatsResponse(**growth_stats)

    async def get_revenue_analytics(self, request: Optional[DashboardDateRangeRequest] = None) -> RevenueAnalyticsResponse:
        """Get revenue analytics"""
        
        start_date = request.start_date if request else None
        end_date = request.end_date if request else None
        
        revenue_stats = self.dal.get_revenue_analytics(start_date, end_date)
        return RevenueAnalyticsResponse(**revenue_stats)

    async def get_chat_analytics(self, page: int = 1, page_size: int = 20) -> ChatAnalyticsResponse:
        """Get chat analytics"""
        
        conversation_stats, analytics = self.dal.get_chat_analytics(page, page_size)
        
        return ChatAnalyticsResponse(
            conversations=conversation_stats,
            **analytics
        )

    async def get_chat_usage_stats(self) -> ChatUsageStatsResponse:
        """Get chat usage statistics"""
        
        usage_stats = self.dal.get_chat_usage_stats()
        return ChatUsageStatsResponse(**usage_stats)

    async def get_file_analytics(self, page: int = 1, page_size: int = 20) -> FileAnalyticsResponse:
        """Get file analytics"""
        
        file_stats, analytics = self.dal.get_file_analytics(page, page_size)
        
        return FileAnalyticsResponse(
            files=file_stats,
            **analytics
        )

    async def get_session_analytics(self, page: int = 1, page_size: int = 20) -> SessionAnalyticsResponse:
        """Get question session analytics"""
        
        session_stats, analytics = self.dal.get_session_analytics(page, page_size)
        
        return SessionAnalyticsResponse(
            sessions=session_stats,
            **analytics
        )

    async def get_agent_analytics(self, page: int = 1, page_size: int = 20) -> AgentAnalyticsResponse:
        """Get agent analytics"""
        
        agent_stats, analytics = self.dal.get_agent_analytics(page, page_size)
        
        return AgentAnalyticsResponse(
            agents=agent_stats,
            **analytics
        )

    async def get_activity_logs(self, request: ActivityLogRequest) -> ActivityLogsResponse:
        """Get activity logs"""
        
        activity_logs, total_count = self.dal.get_activity_logs(
            page=request.page or 1,
            page_size=request.page_size or 20,
            user_id=request.user_id,
            action=request.action,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return ActivityLogsResponse(
            logs=activity_logs,
            total_count=total_count,
            page=request.page or 1,
            page_size=request.page_size or 20
        )

    async def get_recent_activity(self, limit: int = 5) -> RecentActivityResponse:
        """Get recent activity across all modules"""
        
        recent_activity = self.dal.get_recent_activity(limit)
        return RecentActivityResponse(**recent_activity)

    async def get_system_health(self) -> SystemHealthResponse:
        """Get system health metrics"""
        
        health_stats = self.dal.get_system_health()
        return SystemHealthResponse(**health_stats)

    # Additional utility methods
    async def export_user_analytics(self, format: str = "csv") -> bytes:
        """Export user analytics data"""
        # This would implement CSV/Excel export functionality
        # For now, just return placeholder
        raise NotImplementedError("Export functionality not yet implemented")

    async def get_custom_analytics(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get custom analytics based on query parameters"""
        # This would allow for custom dashboard widgets and analytics
        # For now, just return placeholder
        raise NotImplementedError("Custom analytics not yet implemented")

    # Cache management methods
    async def refresh_dashboard_cache(self) -> bool:
        """Refresh dashboard cache"""
        # This would implement cache refresh logic
        # For now, just return success
        return True

    async def get_dashboard_performance_metrics(self) -> Dict[str, Any]:
        """Get dashboard performance metrics"""
        # This would track dashboard query performance
        return {
            "avg_query_time": 0.0,
            "cache_hit_rate": 0.0,
            "active_sessions": 0
        }
