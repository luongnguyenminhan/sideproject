"""Meeting note repository for handling meeting notes and related operations"""

import logging
from typing import Any, Dict, List

from fastapi import Depends, status
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _
from app.modules.meeting_files.repository.meeting_file_repo import MeetingFileRepo
from app.modules.meeting_transcripts.dal.transcript_dal import TranscriptDAL
from app.modules.meeting_transcripts.repository.transcript_repo import TranscriptRepo
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.dal.meeting_note_dal import MeetingItemDAL, MeetingNoteDAL
from app.modules.meetings.dal.notification_dal import NotificationDAL
from app.modules.meetings.dal.token_usage_dal import TokenUsageDAL
from app.modules.meetings.repository.meeting_note_calendar_sync import (
	MeetingNoteCalendarSync,
)
from app.modules.meetings.repository.meeting_note_generator import MeetingNoteGenerator
from app.modules.meetings.repository.meeting_note_item_manager import (
	MeetingNoteItemManager,
)
from app.modules.meetings.repository.meeting_repo import MeetingRepo
from app.modules.meetings.utils.meeting_note_utils import create_token_usage
from app.modules.users.dal.user_dal import UserDAL
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.enums.meeting_enums import TokenOperationTypeEnum

logger = logging.getLogger(__name__)


class MeetingNoteRepo(BaseRepo):
	"""MeetingNoteRepo for handling meeting notes and related items"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the MeetingNoteRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.meeting_note_dal = MeetingNoteDAL(db)
		self.meeting_item_dal = MeetingItemDAL(db)
		self.transcript_dal = TranscriptDAL(db)
		self.meeting_dal = MeetingDAL(db)
		self.token_usage_dal = TokenUsageDAL(db)
		self.notification_dal = NotificationDAL(db)
		self.meeting_repo = MeetingRepo(db)
		self.meeting_file_repo = MeetingFileRepo(db)
		self.transcript_repo = TranscriptRepo(db)
		self.user_dal = UserDAL(db)
		self.user_logs_dal = UserLogDAL(db)

		# Initialize specialized components
		self._note_generator = None
		self._item_manager = None
		self._calendar_sync = None

	def get_note_generator(self):
		"""Get or create the note generator component

		Returns:
		    MeetingNoteGenerator: Component for generating notes
		"""
		if not self._note_generator:
			self._note_generator = MeetingNoteGenerator(self)
		return self._note_generator

	def get_item_manager(self):
		"""Get or create the note item manager component

		Returns:
		    MeetingNoteItemManager: Component for managing note items
		"""
		if not self._item_manager:
			self._item_manager = MeetingNoteItemManager(self)
		return self._item_manager

	def get_calendar_sync(self):
		"""Get or create the calendar sync component

		Returns:
		    MeetingNoteCalendarSync: Component for calendar integration
		"""
		if not self._calendar_sync:
			self._calendar_sync = MeetingNoteCalendarSync(self)
		return self._calendar_sync

	def get_meeting_notes(self, meeting_id: str, user_id: str, include_all_versions: bool = False) -> List[Dict[str, Any]]:
		"""Get all notes for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    include_all_versions (bool): Whether to include all versions or only the latest

		Returns:
		    List[Dict[str, Any]]: List of meeting notes

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		meeting = self.meeting_repo.get_meeting_by_id(meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.is_deleted:
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			notes = self.meeting_note_dal.get_meeting_notes(meeting_id, include_all_versions)
			return [note.to_dict() for note in notes]
		except Exception as ex:
			logger.error(f'[ERROR] Get meeting notes failed: {ex}')
			raise CustomHTTPException(
				message=_('get_notes_failed'),
			)

	def get_note_by_id(self, note_id: str, user_id: str, include_items: bool = False) -> Dict[str, Any]:
		"""Get a meeting note by ID with optional related items

		Args:
		    note_id (str): Note ID
		    user_id (str): User ID
		    include_items (bool): Whether to include meeting items

		Returns:
		    Dict[str, Any]: Meeting note data

		Raises:
		    NotFoundException: If meeting note not found
		"""
		note = self.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)

		# Convert to dict
		note_dict = note.to_dict()

		# Include related items if requested
		if include_items:
			items = self.meeting_item_dal.get_items_by_note(note_id)
			note_dict['items'] = [item.to_dict() for item in items]

		return note_dict

	async def generate_meeting_note(
		self,
		meeting_id: str,
		user_id: str,
		transcript_id: str,
		language: str | None = None,
		meeting_type: str | None = None,
		custom_prompt: str | None = None,
	) -> Dict[str, Any]:
		"""Generate a meeting note from a transcript

		This delegates to the note generator component.

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    transcript_id (str): Transcript ID
		    language (Optional[str]): Language code for note generation
		    custom_prompt (Optional[str]): Custom prompt for note generation
		    meeting_type (Optional[str]): Type of meeting

		Returns:
		    Dict[str, Any]: Generated meeting note
		"""
		return await self.get_note_generator().generate_meeting_note(meeting_id, user_id, transcript_id, language, meeting_type, custom_prompt)

	async def generate_meeting_note_no_authen(self, prompt: str, email: str | None = None) -> Dict[str, Any]:
		"""Generate a meeting note without authentication

		This delegates to the note generator component.

		Args:
		    prompt (str): The transcript content
		    email (Optional[str]): Optional email to send the note to

		Returns:
		    Dict[str, Any]: Generated meeting note with token usage
		"""
		return await self.get_note_generator().generate_meeting_note_no_authen(prompt, email)

	async def create_note_version(self, note_id: str, user_id: str, note_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Create a new version of an existing meeting note

		Args:
		    note_id (str): Existing note ID
		    user_id (str): User ID
		    note_data (Dict[str, Any]): Updated note data

		Returns:
		    Dict[str, Any]: New meeting note version

		Raises:
		    NotFoundException: If meeting note not found
		"""
		# Get existing note
		existing_note = self.meeting_note_dal.get_note_by_id(note_id)
		if not existing_note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		meeting = self.meeting_repo.get_meeting_by_id(existing_note.meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))
		if meeting.is_deleted:
			raise CustomHTTPException(message=_('meeting_not_found'))

		try:
			with self.meeting_note_dal.transaction():
				# Create new version
				new_note_data = {
					'meeting_id': existing_note.meeting_id,
					'transcript_id': existing_note.transcript_id,
					'content': {'text': note_data.get('content', existing_note.content.get('text', '') if isinstance(existing_note.content, dict) else existing_note.content)},
					'version': existing_note.version + 1,
					'is_latest': True,
					'is_encrypted': existing_note.is_encrypted,
					'encryption_key': existing_note.encryption_key,
				}

				new_note = self.meeting_note_dal.create_note(new_note_data)

				# Copy or create new meeting items if provided
				if 'items' in note_data:
					for item_data in note_data['items']:
						item_data['meeting_note_id'] = new_note.id
						self.meeting_item_dal.create(item_data)

				# Track token usage if provided
				if 'token_usage' in note_data:
					create_token_usage(
						self.token_usage_dal,
						existing_note.meeting_id,
						user_id,
						TokenOperationTypeEnum.SUMMARIZATION.value,
						note_data['token_usage'],
					)

				result = self.get_note_by_id(new_note.id, user_id, include_items=True)

				# Automatically save new note version as PDF
				try:
					logger.debug('[DEBUG] Saving new note version as PDF')
					await self.meeting_file_repo.save_note_as_pdf(new_note.id, user_id)
					logger.debug('[DEBUG] Successfully saved note as PDF')
				except Exception as pdf_ex:
					# Log error but don't fail the operation if PDF generation fails
					logger.error(f'[ERROR] Failed to save note as PDF: {pdf_ex}')

				return result
		except Exception as ex:
			logger.error(f'[ERROR] Create note version failed: {ex}')
			raise CustomHTTPException(
				message=_('create_note_version_failed'),
			)

	def delete_note(self, note_id: str, user_id: str) -> bool:
		"""Delete a meeting note

		Args:
		    note_id (str): Note ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If meeting note not found
		"""
		note = self.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)

		try:
			# Soft delete note
			with self.meeting_note_dal.transaction():
				result = self.meeting_note_dal.update(note_id, {'is_deleted': True})
				if not result:
					raise CustomHTTPException(
						message=_('delete_note_failed'),
					)

				# If this was the latest version and there are other versions,
				# make the previous version the latest
				if note.is_latest:
					previous_notes = self.meeting_note_dal.get_meeting_notes(note.meeting_id, include_all_versions=True)

					valid_previous_notes = [n for n in previous_notes if n.id != note_id and not n.is_deleted]
					if valid_previous_notes:
						# Sort by version in descending order
						valid_previous_notes.sort(key=lambda n: n.version, reverse=True)
						# Mark the highest version as latest
						self.meeting_note_dal.update(valid_previous_notes[0].id, {'is_latest': True})

			return True
		except Exception as ex:
			logger.error(f'[ERROR] Delete note failed: {ex}')
			raise CustomHTTPException(
				message=_('delete_note_failed'),
			)

	async def generate_conversation_summary(self, prompt: str) -> Dict[str, Any]:
		"""Generate a summary of a conversation text

		This delegates to the note generator component.

		Args:
		    prompt (str): Conversation text to summarize

		Returns:
		    Dict[str, Any]: Summary with title, content, tags and token usage
		"""
		return await self.get_note_generator().generate_conversation_summary(prompt)

	def get_meeting_transcript_notes(self, transcript_id: str, user_id: str) -> List[Dict[str, Any]]:
		"""Get all transcripts for a meeting

		Args:
		    transcript_id (str): Transcript ID
		    user_id (str): User ID

		Returns:
		    List[Dict[str, Any]]: List of meeting transcripts

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		self.transcript_repo.get_transcript_by_id(transcript_id, user_id)

		# Get transcript notes
		transcript_notes = self.meeting_note_dal.get_notes_by_transcript_id(transcript_id)
		return transcript_notes

	def get_note_items(self, note_id: str, user_id: str) -> List[Dict[str, Any]]:
		"""Get all items for a meeting note

		Args:
		    note_id (str): Note ID
		    user_id (str): User ID

		Returns:
		    List[Dict[str, Any]]: List of meeting note items

		Raises:
		    NotFoundException: If meeting note not found
		"""
		note = self.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)

		items = self.meeting_item_dal.get_items_by_note(note_id)
		return [item.to_dict() for item in items]

	def get_note_item(self, note_id: str, item_id: str, user_id: str) -> Dict[str, Any]:
		"""Get a specific note item

		Args:
		    note_id (str): Note ID
		    item_id (str): Item ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: Meeting note item data

		Raises:
		    NotFoundException: If meeting note or item not found
		"""
		note = self.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)

		item = self.meeting_item_dal.get_item_by_id(item_id)
		if not item:
			raise CustomHTTPException(message=_('item_not_found'))

		return item.to_dict()

	def update_note_item(self, note_id: str, item_id: str, user_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Update a specific note item

		This delegates to the item manager component.

		Args:
		    note_id (str): Note ID
		    item_id (str): Item ID
		    user_id (str): User ID
		    item_data (Dict[str, Any]): Updated item data

		Returns:
		    Dict[str, Any]: Updated note item
		"""
		return self.get_item_manager().update_note_item(note_id, item_id, user_id, item_data)

	def delete_note_item(self, note_id: str, item_id: str, user_id: str) -> bool:
		"""Delete a meeting note item

		This delegates to the item manager component.

		Args:
		    note_id (str): Note ID
		    item_id (str): Item ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful
		"""
		return self.get_item_manager().delete_note_item(note_id, item_id, user_id)

	async def add_note_item_event(self, note_id: str, item_id: str, user_id: str, emails: list[str]) -> Dict[str, Any]:
		"""Add an event for a meeting note item (task)

		This delegates to the calendar sync component.

		Args:
		    note_id (str): Meeting note ID
		    item_id (str): Meeting item ID
		    user_id (str): User ID
		    emails (List[str]): List of email addresses for attendees

		Returns:
		    Dict[str, Any]: Updated meeting item data
		"""
		return await self.get_calendar_sync().add_note_item_event(note_id, item_id, user_id, emails)
