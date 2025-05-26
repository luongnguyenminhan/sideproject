import logging
from datetime import datetime
from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.core.base_model import Pagination
from app.enums.base_enums import Constants
from app.modules.meeting_calendar.models.calendar import (
	CalendarEvent,
	CalendarIntegration,
)
from app.modules.users.models.users import User
from app.utils.filter_utils import apply_dynamic_filters

logger = logging.getLogger(__name__)


class CalendarIntegrationDAL(BaseDAL[CalendarIntegration]):
	"""CalendarIntegrationDAL for database operations on calendar integrations"""

	def __init__(self, db: Session):
		"""Initialize the CalendarIntegrationDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, CalendarIntegration)

	def get_user_integrations(self, user_id: str) -> List[CalendarIntegration]:
		"""Get all calendar integrations for a user

		Args:
		    user_id (str): User ID

		Returns:
		    List[CalendarIntegration]: List of calendar integrations
		"""
		return (
			self.db.query(CalendarIntegration)
			.filter(
				and_(
					CalendarIntegration.user_id == user_id,
					CalendarIntegration.is_deleted == False,
				)
			)
			.all()
		)

	def get_integration_by_provider(self, user_id: str, provider: str) -> CalendarIntegration | None:
		"""Get a calendar integration by provider

		Args:
		    user_id (str): User ID
		    provider (str): Calendar provider

		Returns:
		    Optional[CalendarIntegration]: Calendar integration if found, None otherwise
		"""
		return (
			self.db.query(CalendarIntegration)
			.filter(
				and_(
					CalendarIntegration.user_id == user_id,
					CalendarIntegration.provider == provider,
					CalendarIntegration.is_deleted == False,
				)
			)
			.first()
		)

	def create_integration(self, user_id: str, provider: str) -> CalendarIntegration:
		"""Create a new calendar integration

		Args:
		    user_id (str): User ID
		    provider (str): Calendar provider

		Returns:
		    CalendarIntegration: Created calendar integration
		"""
		user: User = self.db.query(User).filter(User.id == user_id, User.is_deleted == 0).first()

		if not user:
			raise ValueError('User not found or is deleted.')

		google_credentials_json = user.get_google_credentials()
		access_token = google_credentials_json.get('access_token')
		token_expiry = google_credentials_json.get('expires_at')
		# Convert token_expiry from timestamp to datetime if it exists
		if token_expiry:
			if isinstance(token_expiry, int):
				token_expiry = datetime.fromtimestamp(token_expiry)
			elif isinstance(token_expiry, str):
				try:
					token_expiry = datetime.fromisoformat(token_expiry)
				except ValueError:
					# Try parsing as timestamp if it's a numeric string
					token_expiry = datetime.fromtimestamp(int(token_expiry))
		scope = google_credentials_json.get('scope')

		integration = CalendarIntegration(
			user_id=user_id,
			provider=provider,
			scope=scope,
			access_token=access_token,
			token_expiry=token_expiry,
		)

		self.db.add(integration)
		self.db.commit()
		self.db.refresh(integration)
		return integration


class CalendarEventDAL(BaseDAL[CalendarEvent]):
	"""CalendarEventDAL for database operations on calendar events"""

	def __init__(self, db: Session):
		"""Initialize the CalendarEventDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, CalendarEvent)

	def get_user_events(
		self,
		user_id: str,
		start_date: datetime | None = None,
		end_date: datetime | None = None,
	) -> List[CalendarEvent]:
		"""Get all calendar events for a user within a date range

		Args:
		    user_id (str): User ID
		    start_date (Optional[datetime]): Start date for filtering
		    end_date (Optional[datetime]): End date for filtering

		Returns:
		    List[CalendarEvent]: List of calendar events
		"""
		query = self.db.query(CalendarEvent).filter(and_(CalendarEvent.user_id == user_id, CalendarEvent.is_deleted == False))

		if start_date:
			query = query.filter(CalendarEvent.start_time >= start_date)

		if end_date:
			query = query.filter(CalendarEvent.end_time <= end_date)

		return query.order_by(CalendarEvent.start_time).all()

	def get_events_by_meeting(self, meeting_id: str) -> List[CalendarEvent]:
		"""Get all events associated with a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[CalendarEvent]: List of calendar events
		"""
		return (
			self.db.query(CalendarEvent)
			.filter(
				and_(
					CalendarEvent.meeting_id == meeting_id,
					CalendarEvent.is_deleted == False,
				)
			)
			.order_by(CalendarEvent.start_time)
			.all()
		)

	def get_event_by_external_id(self, integration_id: str, external_event_id: str) -> CalendarEvent | None:
		"""Get a calendar event by external event ID

		Args:
		    integration_id (str): Calendar integration ID
		    external_event_id (str): External event ID

		Returns:
		    Optional[CalendarEvent]: Calendar event if found, None otherwise
		"""
		return (
			self.db.query(CalendarEvent)
			.filter(
				and_(
					CalendarEvent.calendar_integration_id == integration_id,
					CalendarEvent.external_event_id == external_event_id,
					CalendarEvent.is_deleted == False,
				)
			)
			.first()
		)

	def get_by_external_id(self, user_id: str, external_event_id: str) -> CalendarEvent | None:
		"""Get a calendar event by external event ID and user ID

		Args:
			user_id (str): User ID
			external_event_id (str): External event ID

		Returns:
			Optional[CalendarEvent]: Calendar event if found, None otherwise
		"""
		return (
			self.db.query(CalendarEvent)
			.filter(
				and_(
					CalendarEvent.user_id == user_id,
					CalendarEvent.external_event_id == external_event_id,
					CalendarEvent.is_deleted == False,
				)
			)
			.first()
		)

	def search_events(self, user_id: str, params: dict) -> Pagination[CalendarEvent]:
		"""Search calendar events with filters for a specific user

		Args:
		    user_id (str): User ID to filter by
		    params (dict): Search parameters and filters

		Returns:
		    Pagination[CalendarEvent]: Paginated event results
		"""
		logger.info(f'Searching events for user {user_id} with parameters: {params}')
		page = int(params.get('page', 1))
		page_size = int(params.get('page_size', Constants.PAGE_SIZE))

		# Start building the query - filter by user_id
		query = self.db.query(CalendarEvent).filter(and_(CalendarEvent.user_id == user_id, CalendarEvent.is_deleted == False))

		# Apply dynamic filters using the common utility function
		query = apply_dynamic_filters(query, CalendarEvent, params)

		# Order by start time (most recent first)
		query = query.order_by(CalendarEvent.start_time.desc())

		# Get total count
		total_count = query.count()

		# Apply pagination
		events = query.offset((page - 1) * page_size).limit(page_size).all()

		logger.info(f'Found {total_count} events, returning page {page} with {len(events)} items')

		return Pagination(items=events, total_count=total_count, page=page, page_size=page_size)
