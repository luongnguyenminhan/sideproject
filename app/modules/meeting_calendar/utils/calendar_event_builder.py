"""Utility functions for building Google Calendar events from meeting data"""

import logging
from datetime import timedelta
from typing import Any, Dict, List

from app.modules.meetings.models.meeting import Meeting
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.models.users import User

logger = logging.getLogger(__name__)


def prepare_event_data(meeting: Meeting, description: str) -> Dict[str, Any]:
	"""Prepare Google Calendar event data from meeting

	Args:
	    meeting (Meeting): Meeting object
	    description (str): Formatted event description

	Returns:
	    Dict[str, Any]: Prepared event data for Google Calendar API
	"""
	# Calculate end time based on meeting date and duration
	end_time = meeting.meeting_date + timedelta(seconds=meeting.duration_seconds or 3600)

	# Prepare event object
	event_data: Dict[str, Any] = {
		'summary': meeting.title,
		'description': description,
		'start': {
			'dateTime': meeting.meeting_date.isoformat(),
			'timeZone': 'Asia/Ho_Chi_Minh',
		},
		'end': {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Ho_Chi_Minh'},
	}

	# Add color based on meeting characteristics
	event_data['colorId'] = get_event_color(meeting)

	# Add location/conferencing details if we have a meeting link
	if meeting.meeting_link:
		# For Google Meet links, use conferenceData
		if meeting.platform == 'Google Meet' or 'meet.google.com' in meeting.meeting_link:
			event_data['conferenceData'] = {
				'createRequest': {
					'requestId': f'meobeo-{meeting.id}',
					'conferenceSolutionKey': {'type': 'hangoutsMeet'},
				}
			}
		else:
			# For other platforms, add the meeting link as location
			event_data['location'] = meeting.meeting_link

	# Add attendees if any information is available
	attendees = get_meeting_attendees(meeting)
	if attendees:
		event_data['attendees'] = attendees

	# Set up recurrence if applicable
	if meeting.is_recurring:
		# Default weekly recurrence
		event_data['recurrence'] = ['RRULE:FREQ=WEEKLY;COUNT=10']

	return event_data


def get_event_color(meeting: Meeting) -> str:
	"""Determine appropriate color for calendar event based on meeting characteristics

	Google Calendar API color IDs:
	1: Lavender    2: Sage        3: Grape       4: Flamingo    5: Banana
	6: Tangerine   7: Peacock     8: Graphite    9: Blueberry   10: Basil
	11: Tomato

	Args:
	    meeting (Meeting): Meeting object

	Returns:
	    str: Color ID for Google Calendar event
	"""
	# Set color based on meeting type or other characteristics

	# Check if meeting has priority field and set colors accordingly
	if hasattr(meeting, 'priority'):
		if meeting.priority == 'high':
			return '11'  # Tomato (red) for high priority
		elif meeting.priority == 'medium':
			return '6'  # Tangerine (orange) for medium priority
		elif meeting.priority == 'low':
			return '5'  # Banana (yellow) for low priority

	# If no priority, set colors based on meeting type
	if hasattr(meeting, 'meeting_type'):
		meeting_type = meeting.meeting_type.lower() if meeting.meeting_type else ''

		# Colors for each meeting type according to MeetingTypeEnum
		meeting_type_colors = {
			'one_on_one': '4',  # Flamingo (pink) for one-on-one meetings
			'team': '2',  # Sage (green) for team meetings
			'client': '6',  # Tangerine (orange) for client meetings
			'interview': '3',  # Grape (purple) for interviews
			'conference': '3',  # Grape (purple) for conferences
		}

		# Get color from mapping or use default behavior for other/anonymous types
		if meeting_type in meeting_type_colors:
			return meeting_type_colors[meeting_type]
		else:
			# For OTHER, ANONYMOUS or any other types, use a hash-based color
			if meeting.id:
				color_id = abs(hash(meeting.id)) % 11 + 1
				return str(color_id)
			return '8'  # Graphite (gray) as default

	# Check meeting platform and set color accordingly
	if meeting.platform:
		platform = meeting.platform.lower()
		if 'zoom' in platform:
			return '9'  # Blueberry (blue) for Zoom
		elif 'meet' in platform or 'google' in platform:
			return '4'  # Flamingo (red/pink) for Google Meet
		elif 'teams' in platform:
			return '7'  # Peacock (teal) for Microsoft Teams

	# Check recurring status
	if meeting.is_recurring:
		return '2'  # Sage (green) for recurring meetings

	# Default color for other meetings
	# Use a hash of the meeting ID to pseudo-randomly select a color
	# This ensures the same meeting always gets the same color
	if meeting.id:
		color_id = abs(hash(meeting.id)) % 11 + 1
		return str(color_id)

	return '8'  # Graphite (gray) as final default


def get_meeting_attendees(meeting: Meeting, user_dal: UserDAL = None) -> List[Dict[str, str]]:
	"""Get meeting attendees information

	Args:
	    meeting (Meeting): Meeting object
	    user_dal: User DAL for retrieving user information

	Returns:
	    List[Dict[str, str]]: List of attendees for Google Calendar API
	"""
	attendees: List[Dict[str, str]] = []

	# Add organizer if we have that information
	if meeting.organizer_email:
		attendees.append({
			'email': meeting.organizer_email,
			'displayName': meeting.organizer_name or meeting.organizer_email,
			'organizer': True,
			'responseStatus': 'accepted',
		})

	# Get user email from the user record
	if user_dal:
		user: User = user_dal.get_by_id(meeting.user_id)
		if user and user.email and (not meeting.organizer_email or user.email != meeting.organizer_email):
			attendees.append({
				'email': user.email,
				'displayName': user.name or user.email,
				'responseStatus': 'accepted',
			})

	return attendees
