"""Token usage data access layer"""

from datetime import datetime, timedelta
from typing import Dict, List

from pytz import timezone
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.meetings.models.token_usage import TokenUsage


class TokenUsageDAL(BaseDAL[TokenUsage]):
	"""TokenUsageDAL for database operations on token usage"""

	def __init__(self, db: Session):
		"""Initialize the TokenUsageDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, TokenUsage)

	def get_usage_by_meeting(self, meeting_id: str) -> List[TokenUsage]:
		"""Get all token usage records for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[TokenUsage]: List of token usage records
		"""
		return self.db.query(TokenUsage).filter(and_(TokenUsage.meeting_id == meeting_id, TokenUsage.is_deleted == False)).all()

	def get_usage_by_user(
		self,
		user_id: str,
		start_date: datetime | None = None,
		end_date: datetime | None = None,
	) -> List[TokenUsage]:
		"""Get all token usage records for a user within a date range

		Args:
		    user_id (str): User ID
		    start_date (Optional[datetime]): Start date for filtering
		    end_date (Optional[datetime]): End date for filtering

		Returns:
		    List[TokenUsage]: List of token usage records
		"""
		query = self.db.query(TokenUsage).filter(and_(TokenUsage.user_id == user_id, TokenUsage.is_deleted == False))

		if start_date:
			query = query.filter(TokenUsage.create_date >= start_date)

		if end_date:
			query = query.filter(TokenUsage.create_date <= end_date)

		return query.order_by(TokenUsage.create_date.desc()).all()

	def get_user_summary(self, user_id: str, days: int = 30) -> Dict[str, int]:
		"""Get a summary of token usage for a user over a period

		Args:
		    user_id (str): User ID
		    days (int): Number of days to look back

		Returns:
		    Dict[str, int]: Summary of token usage
		"""
		start_date = datetime.now(timezone('Asia/Ho_Chi_Minh')) - timedelta(days=days)

		result = (
			self.db.query(
				func.sum(TokenUsage.input_tokens).label('total_input_tokens'),
				func.sum(TokenUsage.output_tokens).label('total_output_tokens'),
				func.sum(TokenUsage.context_tokens).label('total_context_tokens'),
				func.sum(TokenUsage.price_vnd).label('total_price'),
			)
			.filter(
				and_(
					TokenUsage.user_id == user_id,
					TokenUsage.create_date >= start_date,
					TokenUsage.is_deleted == False,
				)
			)
			.first()
		)

		return {
			'total_input_tokens': result.total_input_tokens or 0,
			'total_output_tokens': result.total_output_tokens or 0,
			'total_context_tokens': result.total_context_tokens or 0,
			'total_price_vnd': float(result.total_price) if result.total_price else 0.0,
		}
