"""Repository for group analytics operations"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import Depends

from app.core.database import get_db
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import (
	GroupMember,
	GroupMemberRole,
	GroupMemberJoinStatus,
)
from app.modules.groups.models.group_log import GroupLog
from app.modules.groups.dal.group_analytics_dal import GroupAnalyticsDAL
from app.modules.groups.schemas.group_analytics_schemas import (
	GroupOverviewStatsResponse,
	GroupMemberStatsResponse,
	GroupActivityStatsResponse,
	GroupMeetingAnalyticsResponse,
	TimeSeriesData,
	StatItem,
	TopGroupItem,
	GroupBasicInfo,
	MeetingStatsItem,
)


class GroupAnalyticsRepo:
	"""Repository cho các thao tác analytics của groups"""

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.analytics_dal = GroupAnalyticsDAL(db)

	def get_overview_stats(self, user_id: str) -> GroupOverviewStatsResponse:
		"""Lấy thống kê tổng quan groups"""

		# Lấy dữ liệu từ DAL
		data = self.analytics_dal.get_overview_stats_data(user_id)

		# Tính tỷ lệ tăng trưởng
		growth_rate = 0.0
		if data['groups_last_month'] > 0:
			growth_rate = (float(data['groups_this_month'] - data['groups_last_month']) / float(data['groups_last_month'])) * 100

		# Số thành viên trung bình mỗi group
		avg_members = float(data['total_members']) / float(data['total_groups']) if data['total_groups'] > 0 else 0

		return GroupOverviewStatsResponse(
			total_groups=data['total_groups'],
			active_groups=data['active_groups'],
			inactive_groups=data['inactive_groups'],
			public_groups=data['public_groups'],
			private_groups=data['private_groups'],
			total_members=data['total_members'],
			groups_created_this_month=data['groups_this_month'],
			groups_created_last_month=data['groups_last_month'],
			growth_rate=growth_rate,
			average_members_per_group=avg_members,
		)

	def get_member_stats(self, user_id: str, group_id: Optional[str], period_days: int) -> GroupMemberStatsResponse:
		"""Thống kê thành viên groups"""

		# Lấy dữ liệu từ DAL
		data = self.analytics_dal.get_member_stats_data(user_id, group_id, period_days)

		# Tính toán business logic
		net_growth = data['new_members'] - data['members_left']
		acceptance_rate = (float(data['accepted_invitations']) / float(data['total_invitations']) * 100) if data['total_invitations'] > 0 else 0

		# Time series data
		daily_new_members = self._get_daily_new_members(data['group_ids'], period_days)
		daily_member_count = self._get_daily_member_count(data['group_ids'], period_days)

		# Phân bố theo trạng thái
		status_breakdown = self._get_member_status_breakdown(data['group_ids'])

		return GroupMemberStatsResponse(
			total_members=data['total_members'],
			new_members_this_period=data['new_members'],
			members_left_this_period=data['members_left'],
			net_growth=net_growth,
			invitation_acceptance_rate=acceptance_rate,
			average_response_time_hours=data['avg_response_time'],
			daily_new_members=daily_new_members,
			daily_member_count=daily_member_count,
			member_status_breakdown=status_breakdown,
		)

	def get_activity_stats(self, user_id: str, group_id: Optional[str], period_days: int) -> GroupActivityStatsResponse:
		"""Thống kê hoạt động groups"""

		# Lấy dữ liệu từ DAL
		data = self.analytics_dal.get_activity_stats_data(user_id, group_id, period_days)

		# Tính toán business logic
		avg_activity = float(data['total_activities']) / len(data['group_ids']) if data['group_ids'] else 0

		# Time series data
		daily_group_creation = self._get_daily_group_creation(data['group_ids'], period_days)
		daily_group_activity = self._get_daily_group_activity(data['group_ids'], period_days)

		# Activity breakdown
		activity_breakdown = self._get_activity_type_breakdown(data['group_ids'], period_days)

		return GroupActivityStatsResponse(
			groups_created_this_period=data['groups_created'],
			groups_updated_this_period=data['groups_updated'],
			active_groups_this_period=data['active_groups'],
			average_activity_per_group=avg_activity,
			daily_group_creation=daily_group_creation,
			daily_group_activity=daily_group_activity,
			activity_type_breakdown=activity_breakdown,
		)

	def get_meeting_analytics(self, user_id: str, group_id: Optional[str], period_days: int) -> GroupMeetingAnalyticsResponse:
		"""Thống kê meetings trong groups"""

		# Lấy dữ liệu từ DAL
		data = self.analytics_dal.get_meeting_analytics_data(user_id, group_id, period_days)

		# Tính toán business logic
		avg_duration = float(data['total_duration']) / float(data['total_meetings']) if data['total_meetings'] > 0 else 0
		meetings_per_group = float(data['total_meetings']) / len(data['group_ids']) if data['group_ids'] else 0

		# Time series data
		daily_meetings_created = self._get_daily_meetings_created(data['group_ids'], period_days)
		daily_meetings_completed = self._get_daily_meetings_completed(data['group_ids'], period_days)

		# Breakdown data
		status_breakdown = self._get_meeting_status_breakdown(data['group_ids'], period_days)
		type_breakdown = self._get_meeting_type_breakdown(data['group_ids'], period_days)

		# Top groups with most meetings
		top_meeting_groups = self._get_top_meeting_groups(data['group_ids'], 5)

		return GroupMeetingAnalyticsResponse(
			total_meetings=data['total_meetings'],
			scheduled_meetings=data['scheduled_meetings'],
			completed_meetings=data['completed_meetings'],
			cancelled_meetings=data['cancelled_meetings'],
			average_duration_hours=avg_duration,
			meetings_per_group_avg=meetings_per_group,
			daily_meetings_created=daily_meetings_created,
			daily_meetings_completed=daily_meetings_completed,
			meeting_status_breakdown=status_breakdown,
			meeting_type_breakdown=type_breakdown,
			top_meeting_groups=top_meeting_groups,
		)

	# Helper methods

	def _get_daily_new_members(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Lấy số thành viên mới theo ngày"""
		daily_data = self.analytics_dal.get_daily_time_series(
			group_ids,
			'responded_at',
			GroupMember,
			period_days,
			{'join_status': GroupMemberJoinStatus.ACCEPTED},
		)

		return [TimeSeriesData(date=date, value=count) for date, count in daily_data]

	def _get_daily_member_count(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Lấy tổng số thành viên theo ngày"""
		# Simplified implementation - return empty for now
		return []

	def _get_member_status_breakdown(self, group_ids: List[str]) -> List[StatItem]:
		"""Phân bố thành viên theo trạng thái"""
		status_counts = self.analytics_dal.get_member_counts_by_status(group_ids)

		total = sum(status_counts.values())

		return [
			StatItem(
				label=status,
				value=count,
				percentage=(float(count) / total * 100) if total > 0 else 0,
			)
			for status, count in status_counts.items()
		]

	def _get_daily_group_creation(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Groups tạo theo ngày"""
		daily_data = self.analytics_dal.get_daily_time_series(group_ids, 'create_date', Group, period_days)

		return [TimeSeriesData(date=date, value=count) for date, count in daily_data]

	def _get_daily_group_activity(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Hoạt động groups theo ngày"""
		daily_data = self.analytics_dal.get_daily_time_series(group_ids, 'create_date', GroupLog, period_days)

		return [TimeSeriesData(date=date, value=count) for date, count in daily_data]

	def _get_activity_type_breakdown(self, group_ids: List[str], period_days: int) -> List[StatItem]:
		"""Phân bố loại hoạt động"""
		start_date = datetime.now() - timedelta(days=period_days)
		activity_breakdown = self.analytics_dal.get_action_breakdown(group_ids, start_date)

		total = sum(count for _, count, _ in activity_breakdown)

		return [
			StatItem(
				label=action,
				value=count,
				percentage=(float(count) / total * 100) if total > 0 else 0,
			)
			for action, count, _ in activity_breakdown
		]

	def _get_daily_meetings_created(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Meetings tạo theo ngày"""
		daily_data = self.analytics_dal.get_meeting_daily_time_series(group_ids, 'create_date', period_days)
		return [TimeSeriesData(date=date, value=count) for date, count in daily_data]

	def _get_daily_meetings_completed(self, group_ids: List[str], period_days: int) -> List[TimeSeriesData]:
		"""Meetings hoàn thành theo ngày"""
		daily_data = self.analytics_dal.get_meeting_daily_time_series(group_ids, 'meeting_date', period_days, 'completed')
		return [TimeSeriesData(date=date, value=count) for date, count in daily_data]

	def _get_meeting_status_breakdown(self, group_ids: List[str], period_days: int) -> List[MeetingStatsItem]:
		"""Phân bố meetings theo trạng thái"""
		breakdown_data = self.analytics_dal.get_meeting_status_breakdown(group_ids, period_days)
		total = sum(count for _, count in breakdown_data)

		return [
			MeetingStatsItem(
				status=status,
				count=count,
				percentage=(float(count) / total * 100) if total > 0 else 0,
			)
			for status, count in breakdown_data
		]

	def _get_meeting_type_breakdown(self, group_ids: List[str], period_days: int) -> List[StatItem]:
		"""Phân bố meetings theo loại"""
		breakdown_data = self.analytics_dal.get_meeting_type_breakdown(group_ids, period_days)
		total = sum(count for _, count in breakdown_data)

		return [
			StatItem(
				label=meeting_type or 'Unknown',
				value=count,
				percentage=(float(count) / total * 100) if total > 0 else 0,
			)
			for meeting_type, count in breakdown_data
		]

	def _get_top_meeting_groups(self, group_ids: List[str], limit: int) -> List[TopGroupItem]:
		"""Top groups có nhiều meetings nhất"""
		top_groups_data = self.analytics_dal.get_groups_with_meeting_count(group_ids, limit)

		result = []
		for rank, (group, meeting_count) in enumerate(top_groups_data, 1):
			member_count = self.analytics_dal.get_member_count_for_group(group.id)

			group_info = GroupBasicInfo(
				id=group.id,
				name=group.name,
				member_count=member_count,
				is_public=group.is_public,
				create_date=group.create_date,
			)

			result.append(TopGroupItem(group=group_info, metric_value=float(meeting_count), rank=rank))

		return result
