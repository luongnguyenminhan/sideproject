"""Meeting note data access layer"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from pytz import timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.enums.user_enums import UserRoleEnum
from app.modules.meeting_transcripts.models.transcript import Transcript
from app.modules.meetings.models.meeting import Meeting
from app.modules.meetings.models.meeting_note import MeetingItem, MeetingNote
from app.modules.meetings.models.token_usage import TokenUsage

logger = logging.getLogger(__name__)


class MeetingNoteDAL(BaseDAL[MeetingNote]):
	"""MeetingNoteDAL for database operations on meeting notes"""

	def __init__(self, db: Session):
		"""Initialize the MeetingNoteDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, MeetingNote)

	def get_meeting_notes(self, meeting_id: str, include_all_versions: bool = False) -> List[MeetingNote]:
		"""Get all notes for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    include_all_versions (bool): Whether to include all versions or only the latest

		Returns:
		    List[MeetingNote]: List of meeting notes
		"""
		query = self.db.query(MeetingNote).filter(and_(MeetingNote.meeting_id == meeting_id, MeetingNote.is_deleted == False))

		if not include_all_versions:
			query = query.filter(MeetingNote.is_latest)

		return query.order_by(MeetingNote.create_date.desc()).all()

	def get_note_by_id(self, note_id: str) -> MeetingNote | None:
		"""Get a meeting note by ID

		Args:
		    note_id (str): Note ID

		Returns:
		    Optional[MeetingNote]: Meeting note if found, None otherwise
		"""
		return self.db.query(MeetingNote).filter(and_(MeetingNote.id == note_id, MeetingNote.is_deleted == False)).first()

	def get_latest_note(self, meeting_id: str) -> MeetingNote | None:
		"""Get the latest note for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    Optional[MeetingNote]: Latest meeting note if found, None otherwise
		"""
		return (
			self.db.query(MeetingNote)
			.filter(
				and_(
					MeetingNote.meeting_id == meeting_id,
					MeetingNote.is_latest,
					MeetingNote.is_deleted == False,
				)
			)
			.first()
		)

	def create_note(self, note_data: dict) -> MeetingNote:
		"""Create a new meeting note

		Args:
		    note_data (dict): Note data

		Returns:
		    MeetingNote: Created meeting note
		"""
		# When creating a new version, mark all previous notes as not latest
		if note_data.get('meeting_id') and note_data.get('is_latest', True):
			existing_notes = (
				self.db.query(MeetingNote)
				.filter(
					and_(
						MeetingNote.meeting_id == note_data['meeting_id'],
						MeetingNote.is_latest,
						MeetingNote.is_deleted == False,
					)
				)
				.all()
			)

			for note in existing_notes:
				self.update(note.id, {'is_latest': False})

		return self.create(note_data)

	def update_note(self, note_id: str, note_data: dict) -> MeetingNote | None:
		"""Update an existing meeting note

		Args:
		    note_id (str): Note ID
		    note_data (dict): Updated note data

		Returns:
		    Optional[MeetingNote]: Updated meeting note if found, None otherwise
		"""
		return self.update(note_id, note_data)

	def create_meeting_note_with_related_data(
		self,
		meeting_data: Dict[str, Any],
		transcript_data: Dict[str, Any],
		note_data: Dict[str, Any],
		meeting_items: List[Dict[str, Any]],
		token_usage_data: Dict[str, Any] | None = None,
	) -> Dict[str, Any]:
		"""Create a meeting, transcript, note and related items in a single transaction

		This method ensures all database operations are performed within a single
		transaction to maintain data consistency. If no user_id is provided, it will
		use a system user for anonymous content.

		Args:
		    meeting_data: Dictionary with meeting data
		    transcript_data: Dictionary with transcript data
		    note_data: Dictionary with meeting note data
		    meeting_items: List of dictionaries with meeting item data
		    token_usage_data: Optional dictionary with token usage data

		Returns:
		    Dictionary with created objects IDs
		"""
		try:
			logger.debug('Starting create_meeting_note_with_related_data transaction')

			# Check if user_id is None and handle anonymous meeting
			if meeting_data.get('user_id') is None:
				# Find or create the system user
				system_user = self._get_or_create_system_user()
				meeting_data['user_id'] = system_user.id
				logger.debug(f'Using system user ID {system_user.id} for anonymous meeting')

				# If we have token usage data but no user, assign it to the system user
				if token_usage_data is not None:
					token_usage_data['user_id'] = system_user.id

			# Start a transaction
			with self.transaction():
				# Create meeting
				meeting = Meeting(**meeting_data)
				self.db.add(meeting)
				self.db.flush()  # Get ID without committing

				# Update transcript with meeting ID
				transcript_data['meeting_id'] = meeting.id
				transcript = Transcript(**transcript_data)
				self.db.add(transcript)
				self.db.flush()  # Get ID without committing

				# Update note data with meeting and transcript IDs
				note_data['meeting_id'] = meeting.id
				note_data['transcript_id'] = transcript.id
				note = MeetingNote(**note_data)
				self.db.add(note)
				self.db.flush()  # Get ID without committing

				# Create meeting items
				created_items = []
				for item_data in meeting_items:
					item_data['meeting_note_id'] = note.id
					item = MeetingItem(**item_data)
					self.db.add(item)
					created_items.append(item)

				# Create token usage if provided
				created_token_usage = None
				if token_usage_data:
					token_usage_data['meeting_id'] = meeting.id
					token_usage = TokenUsage(**token_usage_data)
					self.db.add(token_usage)
					self.db.flush()
					created_token_usage = token_usage

				# Return the created objects
				return {
					'meeting': meeting,
					'transcript': transcript,
					'note': note,
					'items': created_items,
					'token_usage': created_token_usage,
				}

		except Exception as ex:
			logger.error(f'Error in create_meeting_note_with_related_data: {ex}')
			raise

	def get_notes_by_transcript_id(self, transcript_id: str) -> List[MeetingNote]:
		"""Get all notes associated with a transcript ID

		Args:
		    transcript_id (str): Transcript ID

		Returns:
		    List[MeetingNote]: List of meeting notes
		"""
		transcript_notes: List[MeetingNote] = self.db.query(MeetingNote).filter(and_(MeetingNote.transcript_id == transcript_id, MeetingNote.is_deleted == False)).all()
		response = [transcript_note.to_dict() for transcript_note in transcript_notes]
		return response

	def _get_or_create_system_user(self):
		"""Get or create a system user for anonymous operations

		Returns:
		    User: The system user object
		"""
		from app.modules.users.models.users import User

		# Check if system user exists
		system_user = self.db.query(User).filter(User.email == 'system@meobeo.ai').first()

		if not system_user:
			logger.debug('Creating system user for anonymous operations')
			system_user = User(
				id=str(uuid4()),
				email='system@meobeo.ai',
				username='system',
				name='System User',
				role=UserRoleEnum.ADMIN.value,
				confirmed=True,
				oauth_provider='none',
				sso_provider='none',
				create_date=datetime.now(timezone('Asia/Ho_Chi_Minh')),
				update_date=datetime.now(timezone('Asia/Ho_Chi_Minh')),
				is_deleted=False,
			)
			self.db.add(system_user)
			self.db.commit()  # Commit immediately to ensure it exists

		return system_user


class MeetingItemDAL(BaseDAL[MeetingItem]):
	"""MeetingItemDAL for database operations on meeting items"""

	def __init__(self, db: Session):
		"""Initialize the MeetingItemDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, MeetingItem)

	def get_items_by_note(self, note_id: str, item_type: str | None = None) -> List[MeetingItem]:
		"""Get all items for a meeting note

		Args:
		    note_id (str): Meeting note ID
		    item_type (Optional[str]): Item type filter

		Returns:
		    List[MeetingItem]: List of meeting items
		"""
		query = self.db.query(MeetingItem).filter(and_(MeetingItem.meeting_note_id == note_id, MeetingItem.is_deleted == False))

		if item_type:
			query = query.filter(MeetingItem.type == item_type)

		return query.all()

	def create_items(self, items_data_list: List[dict]) -> List[MeetingItem]:
		"""Create multiple meeting items

		Args:
		    items_data_list (List[dict]): List of item data

		Returns:
		    List[MeetingItem]: List of created meeting items
		"""
		items = []
		for item_data in items_data_list:
			items.append(self.create(item_data))
		return items

	def get_item_by_id(self, item_id: str) -> MeetingItem | None:
		"""Get a meeting item by ID

		Args:
		    item_id (str): Item ID

		Returns:
		    Optional[MeetingItem]: Meeting item if found, None otherwise
		"""
		return self.db.query(MeetingItem).filter(and_(MeetingItem.id == item_id, MeetingItem.is_deleted == False)).first()
