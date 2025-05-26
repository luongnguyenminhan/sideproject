"""Data Access Layer for group analytics operations"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct, case, text

from app.core.base_dal import BaseDAL
from app.enums.meeting_enums import MeetingStatusEnum
from app.modules.groups.models.group import Group
from app.modules.groups.models.group_member import GroupMember, GroupMemberJoinStatus
from app.modules.groups.models.group_log import GroupLog


class GroupAnalyticsDAL(BaseDAL[Group]):
	"""DAL cho các thao tác analytics của groups"""

	def __init__(self, db: Session):
		super().__init__(db, Group)

	def get_accessible_groups_query(self, user_id: str):
		"""Lấy query cho các groups mà user có quyền truy cập"""
		return (
			self.db.query(Group)
			.join(GroupMember)
			.filter(
				or_(
					and_(
						GroupMember.user_id == user_id,
						GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
						GroupMember.is_deleted == False,
					),
					Group.is_public == True,
				),
				Group.is_deleted == False,
			)
			.distinct()
		)

	def count_groups_by_status(self, group_ids: List[str]) -> Dict[str, int]:
		"""Đếm groups theo trạng thái"""
		if not group_ids:
			return {'active': 0, 'inactive': 0, 'public': 0, 'private': 0}

		results = (
			self.db.query(
				func.sum(case((Group.is_active == True, 1), else_=0)).label('active'),
				func.sum(case((Group.is_active == False, 1), else_=0)).label('inactive'),
				func.sum(case((Group.is_public == True, 1), else_=0)).label('public'),
				func.sum(case((Group.is_public == False, 1), else_=0)).label('private'),
			)
			.filter(Group.id.in_(group_ids))
			.first()
		)

		return {
			'active': results.active or 0,
			'inactive': results.inactive or 0,
			'public': results.public or 0,
			'private': results.private or 0,
		}

	def count_total_members(self, group_ids: List[str]) -> int:
		"""Đếm tổng số thành viên trong các groups"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

	def count_groups_created_in_period(self, group_ids: List[str], start_date: datetime, end_date: datetime) -> int:
		"""Đếm groups tạo trong khoảng thời gian"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(Group.id))
			.filter(
				Group.id.in_(group_ids),
				Group.create_date >= start_date,
				Group.create_date < end_date,
			)
			.scalar()
			or 0
		)

	def get_member_counts_by_status(self, group_ids: List[str], start_date: Optional[datetime] = None) -> Dict[str, int]:
		"""Lấy số lượng thành viên theo trạng thái"""
		if not group_ids:
			return {}

		query = self.db.query(GroupMember.join_status, func.count(GroupMember.id)).filter(GroupMember.group_id.in_(group_ids), GroupMember.is_deleted == False)

		if start_date:
			query = query.filter(GroupMember.invited_at >= start_date)

		results = query.group_by(GroupMember.join_status).all()

		return {status.value: count for status, count in results}

	def get_new_members_in_period(self, group_ids: List[str], start_date: datetime) -> int:
		"""Lấy số thành viên mới trong khoảng thời gian"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.responded_at >= start_date,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

	def get_members_left_in_period(self, group_ids: List[str], start_date: datetime) -> int:
		"""Lấy số thành viên rời đi trong khoảng thời gian"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.is_deleted == True,
				GroupMember.update_date >= start_date,
			)
			.scalar()
			or 0
		)

	def get_average_response_time_hours(self, group_ids: List[str], start_date: Optional[datetime] = None) -> float:
		"""Lấy thời gian phản hồi trung bình (giờ)"""
		if not group_ids:
			return 0.0

		# MySQL compatible: TIMESTAMPDIFF(SECOND, invited_at, responded_at) / 3600
		query = self.db.query(func.avg(func.timestampdiff(text('SECOND'), GroupMember.invited_at, GroupMember.responded_at) / 3600)).filter(
			GroupMember.group_id.in_(group_ids),
			GroupMember.responded_at.isnot(None),
			GroupMember.is_deleted == False,
		)

		if start_date:
			query = query.filter(GroupMember.invited_at >= start_date)

		result = query.scalar()
		return float(result) if result is not None else 0.0

	def get_daily_time_series(
		self,
		group_ids: List[str],
		date_field: str,
		table_class,
		period_days: int,
		additional_filters: Optional[Dict] = None,
	) -> List[Tuple[str, int]]:
		"""Lấy dữ liệu time series theo ngày"""
		if not group_ids:
			return []

		start_date = datetime.now() - timedelta(days=period_days)

		# Xác định field và table
		if table_class == GroupMember:
			date_column = getattr(GroupMember, date_field)
			filter_column = GroupMember.group_id
		elif table_class == Group:
			date_column = getattr(Group, date_field)
			filter_column = Group.id
		elif table_class == GroupLog:
			date_column = getattr(GroupLog, date_field)
			filter_column = GroupLog.group_id
		else:
			return []

		query = self.db.query(func.date(date_column).label('date'), func.count().label('count')).filter(filter_column.in_(group_ids), date_column >= start_date)

		# Thêm filters bổ sung
		if additional_filters:
			for field, value in additional_filters.items():
				if hasattr(table_class, field):
					query = query.filter(getattr(table_class, field) == value)

		# Thêm filter is_deleted nếu có
		if hasattr(table_class, 'is_deleted'):
			query = query.filter(getattr(table_class, 'is_deleted') == False)

		results = query.group_by(func.date(date_column)).all()

		return [(str(date), count) for date, count in results]

	def get_action_breakdown(self, group_ids: List[str], start_date: datetime) -> List[Tuple[str, int, float]]:
		"""Lấy phân bố actions trong logs"""
		if not group_ids:
			return []

		results = (
			self.db.query(GroupLog.action, func.count(GroupLog.id).label('count'))
			.filter(
				GroupLog.group_id.in_(group_ids),
				GroupLog.create_date >= start_date,
				GroupLog.is_deleted == False,
			)
			.group_by(GroupLog.action)
			.all()
		)

		total = sum(count for _, count in results)
		return [(action, count, (float(count) / total * 100) if total > 0 else 0) for action, count in results]

	# Additional methods for repository operations

	def get_overview_stats_data(self, user_id: str) -> Dict[str, Any]:
		"""Lấy dữ liệu thống kê tổng quan"""
		accessible_groups = self.get_accessible_groups_query(user_id)
		group_ids = [g.id for g in accessible_groups.all()]

		# Tổng số groups
		total_groups = accessible_groups.count()

		# Groups theo trạng thái
		status_counts = self.count_groups_by_status(group_ids)

		# Tổng số thành viên
		total_members = self.count_total_members(group_ids)

		# Groups tạo trong tháng này và tháng trước
		now = datetime.now()
		start_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		start_last_month = (start_this_month - timedelta(days=1)).replace(day=1)

		groups_this_month = self.count_groups_created_in_period(group_ids, start_this_month, now)
		groups_last_month = self.count_groups_created_in_period(group_ids, start_last_month, start_this_month)

		return {
			'total_groups': total_groups,
			'active_groups': status_counts['active'],
			'inactive_groups': status_counts['inactive'],
			'public_groups': status_counts['public'],
			'private_groups': status_counts['private'],
			'total_members': total_members,
			'groups_this_month': groups_this_month,
			'groups_last_month': groups_last_month,
		}

	def get_member_stats_data(self, user_id: str, group_id: Optional[str], period_days: int) -> Dict[str, Any]:
		"""Lấy dữ liệu thống kê thành viên"""
		start_date = datetime.now() - timedelta(days=period_days)
		accessible_groups = self.get_accessible_groups_query(user_id)

		if group_id:
			accessible_groups = accessible_groups.filter(Group.id == group_id)

		group_ids = [g.id for g in accessible_groups.all()]

		# Tổng số thành viên hiện tại
		total_members = (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

		# Thành viên mới trong kỳ
		new_members = self.get_new_members_in_period(group_ids, start_date)

		# Thành viên rời đi
		members_left = self.get_members_left_in_period(group_ids, start_date)

		# Tỷ lệ chấp nhận lời mời
		total_invitations = (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.invited_at >= start_date,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

		accepted_invitations = (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id.in_(group_ids),
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.invited_at >= start_date,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

		# Thời gian phản hồi trung bình
		avg_response_time = self.get_average_response_time_hours(group_ids, start_date)

		return {
			'total_members': total_members,
			'new_members': new_members,
			'members_left': members_left,
			'total_invitations': total_invitations,
			'accepted_invitations': accepted_invitations,
			'avg_response_time': avg_response_time,
			'group_ids': group_ids,
		}

	def get_activity_stats_data(self, user_id: str, group_id: Optional[str], period_days: int) -> Dict[str, Any]:
		"""Lấy dữ liệu thống kê hoạt động"""
		start_date = datetime.now() - timedelta(days=period_days)
		accessible_groups = self.get_accessible_groups_query(user_id)

		if group_id:
			accessible_groups = accessible_groups.filter(Group.id == group_id)

		group_ids = [g.id for g in accessible_groups.all()]

		# Groups tạo trong kỳ
		groups_created = self.count_groups_created_in_period(group_ids, start_date, datetime.now())

		# Groups cập nhật trong kỳ
		groups_updated = self.db.query(func.count(Group.id)).filter(Group.id.in_(group_ids), Group.update_date >= start_date).scalar() or 0

		# Groups có hoạt động
		active_groups = self.count_active_groups_with_logs(group_ids, start_date)

		# Tổng hoạt động
		total_activities = self.count_total_actions(group_ids, start_date)

		return {
			'groups_created': groups_created,
			'groups_updated': groups_updated,
			'active_groups': active_groups,
			'total_activities': total_activities,
			'group_ids': group_ids,
		}

	def get_member_count_for_group(self, group_id: str) -> int:
		"""Lấy số thành viên của một group"""
		return (
			self.db.query(func.count(GroupMember.id))
			.filter(
				GroupMember.group_id == group_id,
				GroupMember.join_status == GroupMemberJoinStatus.ACCEPTED,
				GroupMember.is_deleted == False,
			)
			.scalar()
			or 0
		)

	def get_meeting_analytics_data(self, user_id: str, group_id: Optional[str], period_days: int) -> Dict[str, Any]:
		"""Lấy dữ liệu analytics meetings"""
		# Lấy accessible groups
		accessible_groups = self.get_accessible_groups_query(user_id)

		if group_id:
			accessible_groups = accessible_groups.filter(Group.id == group_id)

		group_ids = [g.id for g in accessible_groups.all()]

		if not group_ids:
			return {
				'group_ids': [],
				'total_meetings': 0,
				'scheduled_meetings': 0,
				'completed_meetings': 0,
				'cancelled_meetings': 0,
				'total_duration': 0.0,
			}

		# Import Meeting model
		from app.modules.meetings.models.meeting import Meeting

		start_date = datetime.now() - timedelta(days=period_days)

		# Count meetings by status
		meeting_counts = (
			self.db.query(
				func.count(Meeting.id).label('total'),
				func.sum(
					case(
						(Meeting.status == MeetingStatusEnum.SCHEDULED.value, 1),
						else_=0,
					)
				).label('scheduled'),
				func.sum(
					case(
						(Meeting.status == MeetingStatusEnum.COMPLETED.value, 1),
						else_=0,
					)
				).label('completed'),
				func.sum(
					case(
						(Meeting.status == MeetingStatusEnum.CANCELLED.value, 1),
						else_=0,
					)
				).label('cancelled'),
				func.sum(Meeting.duration_seconds).label('total_duration_seconds'),
			)
			.filter(
				Meeting.group_id.in_(group_ids),
				Meeting.meeting_date >= start_date,
				Meeting.is_deleted == False,
			)
			.first()
		)

		total_duration_hours = float(meeting_counts.total_duration_seconds or 0) / 3600.0

		return {
			'group_ids': group_ids,
			'total_meetings': meeting_counts.total or 0,
			'scheduled_meetings': meeting_counts.scheduled or 0,
			'completed_meetings': meeting_counts.completed or 0,
			'cancelled_meetings': meeting_counts.cancelled or 0,
			'total_duration': total_duration_hours,
		}

	def get_meeting_daily_time_series(
		self,
		group_ids: List[str],
		date_field: str,
		period_days: int,
		status_filter: Optional[str] = None,
	) -> List[Tuple[str, int]]:
		"""Lấy dữ liệu time series meetings theo ngày"""
		if not group_ids:
			return []

		from app.modules.meetings.models.meeting import Meeting

		start_date = datetime.now() - timedelta(days=period_days)
		date_column = getattr(Meeting, date_field)

		query = self.db.query(func.date(date_column).label('date'), func.count().label('count')).filter(
			Meeting.group_id.in_(group_ids),
			date_column >= start_date,
			Meeting.is_deleted == False,
		)

		if status_filter:
			query = query.filter(Meeting.status == status_filter)

		results = query.group_by(func.date(date_column)).all()
		return [(str(date), count) for date, count in results]

	def get_meeting_status_breakdown(self, group_ids: List[str], period_days: int) -> List[Tuple[str, int]]:
		"""Lấy phân bố meetings theo trạng thái"""
		if not group_ids:
			return []

		from app.modules.meetings.models.meeting import Meeting

		start_date = datetime.now() - timedelta(days=period_days)

		results = (
			self.db.query(Meeting.status, func.count(Meeting.id))
			.filter(
				Meeting.group_id.in_(group_ids),
				Meeting.meeting_date >= start_date,
				Meeting.is_deleted == False,
			)
			.group_by(Meeting.status)
			.all()
		)

		return [(status, count) for status, count in results]

	def get_meeting_type_breakdown(self, group_ids: List[str], period_days: int) -> List[Tuple[str, int]]:
		"""Lấy phân bố meetings theo loại"""
		if not group_ids:
			return []

		from app.modules.meetings.models.meeting import Meeting

		start_date = datetime.now() - timedelta(days=period_days)

		results = (
			self.db.query(Meeting.meeting_type, func.count(Meeting.id))
			.filter(
				Meeting.group_id.in_(group_ids),
				Meeting.meeting_date >= start_date,
				Meeting.is_deleted == False,
			)
			.group_by(Meeting.meeting_type)
			.all()
		)

		return [(meeting_type, count) for meeting_type, count in results]

	def get_groups_with_meeting_count(self, group_ids: List[str], limit: int) -> List[Tuple[Group, int]]:
		"""Lấy groups với số lượng meetings"""
		if not group_ids:
			return []

		from app.modules.meetings.models.meeting import Meeting

		results = (
			self.db.query(Group, func.count(Meeting.id).label('meeting_count'))
			.join(Meeting, Group.id == Meeting.group_id)
			.filter(Group.id.in_(group_ids), Meeting.is_deleted == False)
			.group_by(Group.id)
			.order_by(func.count(Meeting.id).desc())
			.limit(limit)
			.all()
		)

		return results

	def count_active_groups_with_logs(self, group_ids: List[str], start_date: datetime) -> int:
		"""Đếm số groups có hoạt động logs"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(distinct(GroupLog.group_id)))
			.filter(
				GroupLog.group_id.in_(group_ids),
				GroupLog.create_date >= start_date,
				GroupLog.is_deleted == False,
			)
			.scalar()
			or 0
		)

	def count_total_actions(self, group_ids: List[str], start_date: datetime) -> int:
		"""Đếm tổng số actions trong logs"""
		if not group_ids:
			return 0

		return (
			self.db.query(func.count(GroupLog.id))
			.filter(
				GroupLog.group_id.in_(group_ids),
				GroupLog.create_date >= start_date,
				GroupLog.is_deleted == False,
			)
			.scalar()
			or 0
		)
