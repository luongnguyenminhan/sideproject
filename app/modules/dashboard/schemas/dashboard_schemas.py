"""Dashboard response schemas"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.core.base_model import ResponseSchema, RequestSchema, FilterableRequestSchema
from app.enums.subscription_enums import RankEnum, OrderStatusEnum
from app.enums.user_enums import UserRoleEnum


# Overview Stats Schemas
class OverviewStatsResponse(ResponseSchema):
    """General overview statistics for dashboard"""
    total_users: int = Field(..., description="Total number of users")
    active_users_today: int = Field(..., description="Active users today")
    active_users_this_week: int = Field(..., description="Active users this week")
    active_users_this_month: int = Field(..., description="Active users this month")
    
    total_conversations: int = Field(..., description="Total conversations")
    total_messages: int = Field(..., description="Total messages")
    conversations_today: int = Field(..., description="New conversations today")
    messages_today: int = Field(..., description="Messages sent today")
    
    total_revenue: float = Field(..., description="Total revenue from payments")
    revenue_this_month: float = Field(..., description="Revenue this month")
    revenue_this_week: float = Field(..., description="Revenue this week")
    revenue_today: float = Field(..., description="Revenue today")
    
    total_files: int = Field(..., description="Total files uploaded")
    total_file_size: int = Field(..., description="Total file size in bytes")
    files_uploaded_today: int = Field(..., description="Files uploaded today")
    
    total_question_sessions: int = Field(..., description="Total question sessions")
    completed_sessions: int = Field(..., description="Completed question sessions")
    active_sessions: int = Field(..., description="Active question sessions")


# User Analytics Schemas
class UserStatsItem(BaseModel):
    """User statistics item"""
    user_id: str
    name: Optional[str]
    email: str
    role: UserRoleEnum
    rank: RankEnum
    total_conversations: int
    total_messages: int
    total_files: int
    last_activity: Optional[datetime]
    join_date: datetime


class UserAnalyticsResponse(ResponseSchema):
    """User analytics response"""
    user_stats: List[UserStatsItem]
    total_count: int
    page: int
    page_size: int


class UserGrowthStatsResponse(ResponseSchema):
    """User growth statistics"""
    daily_growth: List[Dict[str, Any]] = Field(..., description="Daily user registration stats")
    monthly_growth: List[Dict[str, Any]] = Field(..., description="Monthly user growth stats")
    role_distribution: Dict[UserRoleEnum, int] = Field(..., description="Distribution by user roles")
    rank_distribution: Dict[RankEnum, int] = Field(..., description="Distribution by subscription ranks")


# Revenue Analytics Schemas
class RevenueStatsItem(BaseModel):
    """Revenue statistics item"""
    date: str
    amount: float
    transaction_count: int
    rank_type: Optional[RankEnum]


class RevenueAnalyticsResponse(ResponseSchema):
    """Revenue analytics response"""
    daily_revenue: List[RevenueStatsItem]
    monthly_revenue: List[RevenueStatsItem]
    revenue_by_rank: Dict[RankEnum, float]
    total_revenue: float
    average_transaction_value: float


# Chat Analytics Schemas
class ConversationStatsItem(BaseModel):
    """Conversation statistics item"""
    conversation_id: str
    name: str
    user_name: Optional[str]
    user_email: str
    message_count: int
    file_count: int
    last_activity: Optional[datetime]
    created_date: datetime


class ChatAnalyticsResponse(ResponseSchema):
    """Chat analytics response"""
    conversations: List[ConversationStatsItem]
    total_conversations: int
    total_messages: int
    average_messages_per_conversation: float
    most_active_conversations: List[ConversationStatsItem]
    recent_conversations: List[ConversationStatsItem]


class ChatUsageStatsResponse(ResponseSchema):
    """Chat usage statistics"""
    daily_stats: List[Dict[str, Any]] = Field(..., description="Daily conversation and message stats")
    hourly_distribution: List[Dict[str, Any]] = Field(..., description="Hourly usage distribution")
    user_engagement: Dict[str, Any] = Field(..., description="User engagement metrics")


# File Analytics Schemas
class FileStatsItem(BaseModel):
    """File statistics item"""
    file_id: str
    name: str
    original_name: str
    type: str
    size: int
    user_name: Optional[str]
    user_email: str
    download_count: int
    upload_date: datetime
    is_indexed: bool


class FileAnalyticsResponse(ResponseSchema):
    """File analytics response"""
    files: List[FileStatsItem]
    total_files: int
    total_size: int
    file_type_distribution: Dict[str, int]
    recent_uploads: List[FileStatsItem]
    most_downloaded: List[FileStatsItem]


# Question Session Analytics Schemas
class QuestionSessionStatsItem(BaseModel):
    """Question session statistics item"""
    session_id: str
    name: str
    user_name: Optional[str]
    user_email: str
    session_type: str
    session_status: str
    questions_count: int
    answers_count: int
    completion_rate: float
    start_date: Optional[datetime]
    completion_date: Optional[datetime]
    created_date: datetime


class SessionAnalyticsResponse(ResponseSchema):
    """Question session analytics response"""
    sessions: List[QuestionSessionStatsItem]
    total_sessions: int
    completion_rate: float
    session_type_distribution: Dict[str, int]
    status_distribution: Dict[str, int]
    recent_sessions: List[QuestionSessionStatsItem]


# Agent Analytics Schemas
class AgentStatsItem(BaseModel):
    """Agent statistics item"""
    agent_id: str
    name: str
    description: Optional[str]
    model_provider: str
    model_name: str
    is_active: bool
    usage_count: int
    owner_name: Optional[str]
    created_date: datetime


class AgentAnalyticsResponse(ResponseSchema):
    """Agent analytics response"""
    agents: List[AgentStatsItem]
    total_agents: int
    active_agents: int
    provider_distribution: Dict[str, int]
    model_distribution: Dict[str, int]


# Request Schemas
class DashboardDateRangeRequest(FilterableRequestSchema):
    """Dashboard request with date range filtering"""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    user_id: Optional[str] = Field(None, description="Filter by specific user")
    include_deleted: bool = Field(False, description="Include deleted records")


class ActivityLogRequest(FilterableRequestSchema):
    """Activity log request"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    action: Optional[str] = Field(None, description="Filter by action type")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")


# Activity Logs Schema
class ActivityLogItem(BaseModel):
    """Activity log item"""
    log_id: str
    user_name: Optional[str]
    user_email: str
    action: str
    details: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_date: datetime


class ActivityLogsResponse(ResponseSchema):
    """Activity logs response"""
    logs: List[ActivityLogItem]
    total_count: int
    page: int
    page_size: int


# Recent Activity Schema
class RecentActivityResponse(ResponseSchema):
    """Recent activity across the platform"""
    recent_users: List[UserStatsItem] = Field(..., description="Recently joined users")
    recent_conversations: List[ConversationStatsItem] = Field(..., description="Recent conversations")
    recent_files: List[FileStatsItem] = Field(..., description="Recently uploaded files")
    recent_payments: List[Dict[str, Any]] = Field(..., description="Recent payments")
    recent_sessions: List[QuestionSessionStatsItem] = Field(..., description="Recent question sessions")


# System Health Schema
class SystemHealthResponse(ResponseSchema):
    """System health and performance metrics"""
    database_status: str = Field(..., description="Database connection status")
    total_records: Dict[str, int] = Field(..., description="Total records per table")
    storage_info: Dict[str, Any] = Field(..., description="Storage usage information")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    last_updated: datetime = Field(..., description="Last update time")
