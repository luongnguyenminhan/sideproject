"""Utility functions for Google Calendar service creation and authentication"""

import json
import logging
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pytz import timezone

from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from app.modules.meeting_calendar.dal.calendar_dal import CalendarIntegrationDAL
from app.modules.meeting_calendar.models.calendar import CalendarIntegration
from app.modules.users.models.users import User

logger = logging.getLogger(__name__)


def create_google_calendar_service(user: User, integration: CalendarIntegration | None = None, calendar_integration_dal: CalendarIntegrationDAL = None) -> any:
	"""Create Google Calendar API service with proper authentication

	Args:
	    user (User): User object
	    integration (Optional[CalendarIntegration]): Integration object if available
	    calendar_integration_dal: DAL to update integration if needed

	Returns:
	    Any: Google Calendar service or None if failed
	"""
	try:
		if not integration and calendar_integration_dal:
			# Try to get the integration if not provided
			integration = calendar_integration_dal.get_integration_by_provider(user.id, 'google')

		google_credentials = user.get_google_credentials()
		if not google_credentials:
			logger.error(f'No Google credentials found for user {user.id}')
			return None

		creds = Credentials(
			token=google_credentials['access_token'],
			refresh_token=google_credentials.get('refresh_token'),
			token_uri='https://oauth2.googleapis.com/token',
			client_id=GOOGLE_CLIENT_ID,
			client_secret=GOOGLE_CLIENT_SECRET,
			scopes=['https://www.googleapis.com/auth/calendar'],
		)

		# Check if token needs refresh
		if creds.expired and creds.refresh_token:
			logger.info(f'Refreshing expired token for user {user.id}')
			request = Request()
			creds.refresh(request)

			# Update stored credentials
			google_credentials['access_token'] = creds.token
			google_credentials['expires_at'] = int((datetime.now(timezone('Asia/Ho_Chi_Minh')) + timedelta(seconds=creds.expires_in)).timestamp())

			# Update credentials in the user record
			if calendar_integration_dal:
				try:
					calendar_integration_dal.user_dal.update(
						user.id,
						{'google_credentials_json': json.dumps(google_credentials)},
					)

					# Also update in the integration record if it exists
					if integration:
						calendar_integration_dal.update(
							integration.id,
							{
								'access_token': creds.token,
								'token_expiry': datetime.fromtimestamp(google_credentials['expires_at']),
							},
						)

				except Exception as ex:
					logger.error(f'Failed to update refreshed credentials: {ex}')

		# Create and return the Google Calendar service
		return build('calendar', 'v3', credentials=creds)

	except Exception as ex:
		logger.error(f'Error creating Google Calendar service: {ex}')
		return None


def get_or_create_calendar_integration(user_id: str, calendar_integration_dal: CalendarIntegrationDAL) -> CalendarIntegration | None:
	"""Get or create calendar integration for a user

	Args:
	    user_id (str): User ID
	    calendar_integration_dal: DAL for calendar integration operations

	Returns:
	    Optional[CalendarIntegration]: Calendar integration or None if failed
	"""
	try:
		# Check if user already has a Google Calendar integration
		integration = calendar_integration_dal.get_integration_by_provider(user_id, 'google')

		if integration:
			# Check if token is expired and needs refresh
			if integration.token_expiry and integration.token_expiry <= datetime.now():
				# Token expired, need to refresh
				logger.info(f'Token expired for user {user_id}, needs refresh')
				# Will be handled by the Google Calendar service creation

			return integration
		else:
			# Create new integration
			logger.info(f'Creating new Google Calendar integration for user {user_id}')
			return calendar_integration_dal.create_integration(user_id, 'google')

	except Exception as ex:
		logger.error(f'Error getting or creating calendar integration: {ex}')
		return None
