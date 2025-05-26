"""Schemas for group analytics API responses"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.base_model import ResponseSchema


class TimeSeriesData(BaseModel):
	"""Schema cho dữ liệu time series"""

	date: str = Field(..., description='Ngày (YYYY-MM-DD)')
	value: int = Field(..., description='Giá trị')


class StatItem(BaseModel):
	"""Schema cho một item thống kê"""

	label: str = Field(..., description='Nhãn')
	value: int = Field(..., description='Giá trị')
	percentage: Optional[float] = Field(None, description='Phần trăm')


class GroupBasicInfo(BaseModel):
	"""Thông tin cơ bản của group"""

	id: str
	name: str
	member_count: int
	is_public: bool
	create_date: datetime


class GroupOverviewStatsResponse(ResponseSchema):
	"""Thống kê tổng quan groups"""

	total_groups: int = Field(..., description='Tổng số groups')
	active_groups: int = Field(..., description='Số groups đang hoạt động')
	inactive_groups: int = Field(..., description='Số groups không hoạt động')
	public_groups: int = Field(..., description='Số groups công khai')
	private_groups: int = Field(..., description='Số groups riêng tư')
	total_members: int = Field(..., description='Tổng số thành viên')
	groups_created_this_month: int = Field(..., description='Số groups tạo trong tháng')
	groups_created_last_month: int = Field(..., description='Số groups tạo tháng trước')
	growth_rate: float = Field(..., description='Tỷ lệ tăng trưởng (%)')
	average_members_per_group: float = Field(..., description='Số thành viên trung bình mỗi group')


class GroupMemberStatsResponse(ResponseSchema):
	"""Thống kê thành viên groups"""

	total_members: int = Field(..., description='Tổng số thành viên')
	new_members_this_period: int = Field(..., description='Thành viên mới trong kỳ')
	members_left_this_period: int = Field(..., description='Thành viên rời đi trong kỳ')
	net_growth: int = Field(..., description='Tăng trưởng ròng')
	invitation_acceptance_rate: float = Field(..., description='Tỷ lệ chấp nhận lời mời (%)')
	average_response_time_hours: float = Field(..., description='Thời gian phản hồi trung bình (giờ)')
	daily_new_members: List[TimeSeriesData] = Field(..., description='Thành viên mới theo ngày')
	daily_member_count: List[TimeSeriesData] = Field(..., description='Tổng thành viên theo ngày')
	member_status_breakdown: List[StatItem] = Field(..., description='Phân bố theo trạng thái')


class GroupActivityStatsResponse(ResponseSchema):
	"""Thống kê hoạt động groups"""

	groups_created_this_period: int = Field(..., description='Groups tạo trong kỳ')
	groups_updated_this_period: int = Field(..., description='Groups cập nhật trong kỳ')
	active_groups_this_period: int = Field(..., description='Groups có hoạt động trong kỳ')
	average_activity_per_group: float = Field(..., description='Hoạt động trung bình mỗi group')
	daily_group_creation: List[TimeSeriesData] = Field(..., description='Tạo groups theo ngày')
	daily_group_activity: List[TimeSeriesData] = Field(..., description='Hoạt động groups theo ngày')
	activity_type_breakdown: List[StatItem] = Field(..., description='Phân bố theo loại hoạt động')


class MeetingStatsItem(BaseModel):
	"""Thống kê meetings"""

	status: str = Field(..., description='Trạng thái meeting')
	count: int = Field(..., description='Số lượng')
	percentage: float = Field(..., description='Phần trăm')


class TopGroupItem(BaseModel):
	"""Item trong danh sách top groups"""

	group: GroupBasicInfo = Field(..., description='Thông tin group')
	metric_value: float = Field(..., description='Giá trị metric')
	rank: int = Field(..., description='Thứ hạng')


class GroupMeetingAnalyticsResponse(ResponseSchema):
	"""Thống kê meetings trong groups"""

	total_meetings: int = Field(..., description='Tổng số meetings')
	scheduled_meetings: int = Field(..., description='Meetings đã lên lịch')
	completed_meetings: int = Field(..., description='Meetings đã hoàn thành')
	cancelled_meetings: int = Field(..., description='Meetings đã hủy')
	average_duration_hours: float = Field(..., description='Thời lượng trung bình (giờ)')
	meetings_per_group_avg: float = Field(..., description='Số meetings trung bình mỗi group')
	daily_meetings_created: List[TimeSeriesData] = Field(..., description='Meetings tạo theo ngày')
	daily_meetings_completed: List[TimeSeriesData] = Field(..., description='Meetings hoàn thành theo ngày')
	meeting_status_breakdown: List[MeetingStatsItem] = Field(..., description='Phân bố theo trạng thái')
	meeting_type_breakdown: List[StatItem] = Field(..., description='Phân bố theo loại meeting')
	top_meeting_groups: List[TopGroupItem] = Field(..., description='Groups có nhiều meetings nhất')
