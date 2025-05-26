"""Token Usage Analytics API Routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.base_model import (
	APIResponse,
)
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.auth_middleware import verify_token
from app.middleware.translation_manager import _
from app.modules.meetings.repository.token_usage_repo import TokenUsageRepo
from app.modules.meetings.schemas.token_usage_schemas import (
	TokenUsageAnalyticsResponse,
	TokenUsageSummaryResponse,
	UserTokenUsageSummary,
)
from app.modules.users.dal.user_dal import UserDAL

route = APIRouter(prefix='/token-usage', tags=['Token Usage'], dependencies=[Depends(verify_token)])


@route.get('/analytics', response_model=APIResponse)
@handle_exceptions
async def analyze_token_usage_by_type(
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get token usage analytics grouped by operation type

	This endpoint provides an analysis of token usage grouped by operation type.
	It shows input tokens, output tokens, context tokens, total tokens used,
	usage count, and average tokens per operation.

	For admin users, this endpoint returns data for all users.
	For regular users, it returns only their own data.

	Returns:
	    List of token usage analytics by operation type
	"""
	# Get user from database
	user_dal = UserDAL(db)
	user = user_dal.get_user_by_id(current_user_payload['user_id'])
	if not user:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_NOT_FOUND,
			message=_('user_not_found'),
			data=None,
		)

	# Get analytics from repository
	token_usage_repo = TokenUsageRepo(db)
	results = token_usage_repo.get_usage_analytics_by_type(user)

	# Convert to response model
	analytics_results = [
		TokenUsageAnalyticsResponse(
			operation_type=item['operation_type'],
			input_tokens=item['input_tokens'],
			output_tokens=item['output_tokens'],
			context_tokens=item['context_tokens'],
			total_tokens=item['total_tokens'],
			total_price_vnd=item['total_price_vnd'],
			usage_count=item['usage_count'],
			average_tokens=item['average_tokens'],
		)
		for item in results
	]

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('token_usage_analytics_success'),
		data=analytics_results,
	)


@route.get('/summary', response_model=APIResponse)
@handle_exceptions
async def get_user_usage_summary(
	days: int = Query(30, ge=1, le=365, description='Number of days to look back'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get token usage summary for the current user

	This endpoint provides a summary of token usage for the current user,
	showing total input tokens, output tokens, context tokens, and price.

	Args:
	    days: Number of days to look back (default: 30)

	Returns:
	    Token usage summary
	"""
	try:
		token_usage_repo = TokenUsageRepo(db)
		results = token_usage_repo.get_user_usage_summary(current_user_payload['user_id'], days)

		# Convert to response model
		summary = TokenUsageSummaryResponse(
			total_input_tokens=results['total_input_tokens'],
			total_output_tokens=results['total_output_tokens'],
			total_context_tokens=results['total_context_tokens'],
			total_price_vnd=results['total_price_vnd'],
		)

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('token_usage_summary_success'),
			data=summary,
		)
	except Exception as e:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=str(e),
			data=None,
		)


@route.get('/all-users-summary', response_model=APIResponse)
@handle_exceptions
async def get_all_users_usage_summary(
	days: int = Query(30, ge=1, le=365, description='Number of days to look back'),
	db: Session = Depends(get_db),
	current_user_payload: dict = Depends(get_current_user),
):
	"""Get token usage summary for all users (admin only)

	This endpoint provides a summary of token usage for all users,
	showing total tokens used and price for each user.

	Args:
	    days: Number of days to look back (default: 30)

	Returns:
	    List of user token usage summaries
	"""
	# Get user from database to check if admin
	user_dal = UserDAL(db)
	user = user_dal.get_user_by_id(current_user_payload['user_id'])
	if not user or not user.role or user.role.value != 'admin':
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FORBIDDEN,
			message=_('admin_access_required'),
			data=None,
		)

	try:
		token_usage_repo = TokenUsageRepo(db)
		results = token_usage_repo.get_all_users_usage_summary(days)

		# Convert to response model
		user_summaries = [
			UserTokenUsageSummary(
				user_id=item['user_id'],
				email=item['email'],
				name=item['name'],
				total_input_tokens=item['total_input_tokens'],
				total_output_tokens=item['total_output_tokens'],
				total_context_tokens=item['total_context_tokens'],
				total_price_vnd=item['total_price_vnd'],
			)
			for item in results
		]

		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('all_users_token_usage_summary_success'),
			data=user_summaries,
		)
	except Exception as e:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=str(e),
			data=None,
		)
