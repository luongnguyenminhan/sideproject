"""API routes for group analytics and statistics"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.groups.repository.group_analytics_repo import GroupAnalyticsRepo
from app.modules.groups.schemas.group_analytics_schemas import (
	GroupOverviewStatsResponse,
	GroupMemberStatsResponse,
	GroupActivityStatsResponse,
	GroupMeetingAnalyticsResponse,
)

route = APIRouter(prefix='/groups/analytics', tags=['Group Analytics'], dependencies=[Depends(verify_token)])


@route.get('/overview', response_model=APIResponse)
@handle_exceptions
async def get_group_overview_stats(
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Thống kê tổng quan về groups"""
	user_id = current_user.get('user_id')
	analytics_repo = GroupAnalyticsRepo(db)

	stats = analytics_repo.get_overview_stats(user_id)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_overview_stats_retrieved_successfully'),
		data=stats,
	)


@route.get('/member-stats', response_model=APIResponse)
@handle_exceptions
async def get_group_member_stats(
	group_id: Optional[str] = Query(None, description='ID của group cụ thể'),
	period_days: int = Query(30, description='Số ngày để thống kê'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Thống kê thành viên groups"""
	user_id = current_user.get('user_id')
	analytics_repo = GroupAnalyticsRepo(db)

	stats = analytics_repo.get_member_stats(user_id, group_id, period_days)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_member_stats_retrieved_successfully'),
		data=stats,
	)


@route.get('/activity-stats', response_model=APIResponse)
@handle_exceptions
async def get_group_activity_stats(
	group_id: Optional[str] = Query(None, description='ID của group cụ thể'),
	period_days: int = Query(30, description='Số ngày để thống kê'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Thống kê hoạt động groups"""
	user_id = current_user.get('user_id')
	analytics_repo = GroupAnalyticsRepo(db)

	stats = analytics_repo.get_activity_stats(user_id, group_id, period_days)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_activity_stats_retrieved_successfully'),
		data=stats,
	)


@route.get('/meeting-analytics', response_model=APIResponse)
@handle_exceptions
async def get_group_meeting_analytics(
	group_id: Optional[str] = Query(None, description='ID của group cụ thể'),
	period_days: int = Query(30, description='Số ngày để thống kê'),
	db: Session = Depends(get_db),
	current_user: Dict[str, Any] = Depends(get_current_user),
):
	"""Thống kê meetings trong groups"""
	user_id = current_user.get('user_id')
	analytics_repo = GroupAnalyticsRepo(db)

	stats = analytics_repo.get_meeting_analytics(user_id, group_id, period_days)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('group_meeting_analytics_retrieved_successfully'),
		data=stats,
	)
