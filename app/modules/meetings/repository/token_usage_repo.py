"""Token usage repository"""

import logging
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meetings.dal.token_usage_dal import TokenUsageDAL
from app.modules.meetings.models.token_usage import TokenUsage
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.models.users import User
from fastapi import status

logger = logging.getLogger(__name__)


class TokenUsageRepo(BaseRepo):
	"""TokenUsageRepo for token usage analytics and management"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the TokenUsageRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.token_usage_dal = TokenUsageDAL(db)
		self.user_dal = UserDAL(db)

	def get_usage_analytics_by_type(self, user: User) -> List[Dict[str, Any]]:
		"""Get token usage analytics grouped by operation type

		This aggregates token usage data by operation_type. Admin users can see all data,
		while regular users only see their own.

		Args:
		    user (User): Current user

		Returns:
		    List[Dict[str, Any]]: Aggregated usage data by operation type
		"""
		try:
			# Check if user is admin to determine if they should see all data
			is_admin = user.role and user.role.value == 'admin'

			# Calculate total tokens for sorting
			total_tokens = func.sum(func.coalesce(TokenUsage.input_tokens, 0) + func.coalesce(TokenUsage.output_tokens, 0) + func.coalesce(TokenUsage.context_tokens, 0)).label('total_tokens')

			# Base query to aggregate data by operation_type
			if is_admin:
				query = self.db.query(
					TokenUsage.operation_type,
					func.sum(TokenUsage.input_tokens).label('input_tokens'),
					func.sum(TokenUsage.output_tokens).label('output_tokens'),
					func.sum(TokenUsage.context_tokens).label('context_tokens'),
					func.sum(TokenUsage.price_vnd).label('total_price'),
					func.count(TokenUsage.id).label('usage_count'),
					total_tokens,
				).filter(TokenUsage.is_deleted == False)
			else:
				# Regular users can only see their own data
				query = self.db.query(
					TokenUsage.operation_type,
					func.sum(TokenUsage.input_tokens).label('input_tokens'),
					func.sum(TokenUsage.output_tokens).label('output_tokens'),
					func.sum(TokenUsage.context_tokens).label('context_tokens'),
					func.sum(TokenUsage.price_vnd).label('total_price'),
					func.count(TokenUsage.id).label('usage_count'),
					total_tokens,
				).filter(TokenUsage.user_id == user.id, TokenUsage.is_deleted == False)

			# Group by operation type and order by total tokens descending
			results = query.group_by(TokenUsage.operation_type).order_by(desc('total_tokens')).all()

			# Convert SQLAlchemy results to dictionaries
			return [
				{
					'operation_type': r.operation_type,
					'input_tokens': int(r.input_tokens) if r.input_tokens else 0,
					'output_tokens': int(r.output_tokens) if r.output_tokens else 0,
					'context_tokens': int(r.context_tokens) if r.context_tokens else 0,
					'total_tokens': int(r.input_tokens or 0) + int(r.output_tokens or 0) + int(r.context_tokens or 0),
					'total_price_vnd': float(r.total_price) if r.total_price else 0.0,
					'usage_count': int(r.usage_count),
					'average_tokens': ((int(r.input_tokens or 0) + int(r.output_tokens or 0) + int(r.context_tokens or 0)) / int(r.usage_count) if r.usage_count else 0),
				}
				for r in results
			]

		except Exception as ex:
			logger.error(f'Error getting token usage analytics: {ex}')
			raise CustomHTTPException(
				message=_('get_usage_analytics_failed'),
			)

	def get_user_usage_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
		"""Get usage summary for a specific user

		Args:
		    user_id (str): User ID
		    days (int): Number of days to look back

		Returns:
		    Dict[str, Any]: Summary of token usage

		Raises:
		    NotFoundException: If user not found
		"""
		try:
			# Check if user exists
			user = self.user_dal.get_user_by_id(user_id)
			if not user:
				raise CustomHTTPException(message=_('user_not_found'))

			# Get usage summary from DAL
			return self.token_usage_dal.get_user_summary(user_id, days)

		except NotFoundException:
			raise
		except Exception as ex:
			logger.error(f'Error getting user usage summary: {ex}')
			raise CustomHTTPException(
				message=_('get_usage_summary_failed'),
			)

	def get_all_users_usage_summary(self, days: int = 30) -> List[Dict[str, Any]]:
		"""Get usage summary for all users (admin only)

		Args:
		    days (int): Number of days to look back

		Returns:
		    List[Dict[str, Any]]: List of user summaries
		"""
		try:
			# Get all active users
			users = self.db.query(User).filter(User.is_deleted == False).all()
			results = []

			for user in users:
				# Get summary for each user
				summary = self.token_usage_dal.get_user_summary(str(user.id), days)

				# Add user information to summary
				summary['user_id'] = str(user.id)
				summary['email'] = user.email
				summary['name'] = user.name or user.username

				results.append(summary)

			# Sort by total tokens descending
			results.sort(
				key=lambda x: x.get('total_input_tokens', 0) + x.get('total_output_tokens', 0) + x.get('total_context_tokens', 0),
				reverse=True,
			)

			return results

		except Exception as ex:
			logger.error(f'Error getting all users usage summary: {ex}')
			raise CustomHTTPException(
				message=_('get_all_users_summary_failed'),
			)
