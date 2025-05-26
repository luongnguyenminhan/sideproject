"""Meeting note item manager module for handling note items (tasks, decisions, questions)"""

import json
import logging
from typing import Any, Dict

from fastapi import status

from app.exceptions.exception import CustomHTTPException, NotFoundException
from app.middleware.translation_manager import _
from app.modules.meetings.models.meeting_note import MeetingItem, MeetingNote

logger = logging.getLogger(__name__)


class MeetingNoteItemManager:
	"""Class for managing meeting note items"""

	def __init__(self, repo):
		"""Initialize the MeetingNoteItemManager

		Args:
		    repo: The main MeetingNoteRepo instance
		"""
		self.repo = repo

	def update_note_item(self, note_id: str, item_id: str, user_id: str, item_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Update a specific note item

		Args:
		    note_id (str): Note ID
		    item_id (str): Item ID
		    user_id (str): User ID
		    item_data (Dict[str, Any]): Updated item data

		Returns:
		    Dict[str, Any]: Updated note item

		Raises:
		    NotFoundException: If meeting note or item not found
		"""

		# Get existing note
		note = self.repo.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		meeting = self.repo.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)
		if not meeting:
			raise CustomHTTPException(message=_('meeting_not_found'))

		# Get existing item
		item = self.repo.meeting_item_dal.get_item_by_id(item_id)
		if not item:
			raise CustomHTTPException(message=_('item_not_found'))

		# Ensure item belongs to the note
		if item.meeting_note_id != note.id:
			raise CustomHTTPException(message=_('item_not_found'))

		try:
			with self.repo.meeting_item_dal.transaction():
				# Update item
				updated_item = self.repo.meeting_item_dal.update(item.id, item_data)
				if not updated_item:
					raise CustomHTTPException(
						message=_('update_note_item_failed'),
					)

				return updated_item.to_dict()

		except Exception as ex:
			logger.error(f'[ERROR] Update note item failed: {ex}')
			raise CustomHTTPException(
				message=_('update_note_item_failed'),
			)

	def delete_note_item(self, note_id: str, item_id: str, user_id: str) -> bool:
		"""Delete a meeting note item

		Args:
		    note_id (str): Note ID
		    item_id (str): Item ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If meeting note or item not found
		"""
		# Get existing note
		note = self.repo.meeting_note_dal.get_note_by_id(note_id)
		if not note:
			raise CustomHTTPException(message=_('note_not_found'))

		# Ensure note belongs to user through meeting
		self.repo.meeting_repo.get_meeting_by_id(note.meeting_id, user_id)

		# Get existing item
		item = self.repo.meeting_item_dal.get_item_by_id(item_id)
		if not item:
			raise CustomHTTPException(message=_('item_not_found'))

		# Ensure item belongs to the note
		if item.meeting_note_id != note.id:
			raise CustomHTTPException(message=_('item_not_found'))

		try:
			# Soft delete item
			with self.repo.meeting_item_dal.transaction():
				result = self.repo.meeting_item_dal.update(item.id, {'is_deleted': True})
				if not result:
					raise CustomHTTPException(
						message=_('delete_note_item_failed'),
					)

			return True
		except Exception as ex:
			logger.error(f'[ERROR] Delete note item failed: {ex}')
			raise CustomHTTPException(
				message=_('delete_note_item_failed'),
			)
