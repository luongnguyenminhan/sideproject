"""Transcript repository"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import Depends, UploadFile
from pytz import timezone
from sqlalchemy.orm import Session

from app.core.base_model import Pagination
from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.core.event_hooks import EventHooks
from app.enums.meeting_enums import (
	FileTypeEnum,
	MeetingStatusEnum,
	MeetingTypeEnum,
	TokenOperationTypeEnum,
)
from app.enums.transcript_enums import AudioSourceEnum
from app.exceptions.exception import CustomHTTPException, NotFoundException

from app.jobs.tasks import process_audio_task
from app.middleware.translation_manager import _
from app.modules.meeting_files.repository.meeting_file_repo import MeetingFileRepo
from app.modules.meeting_transcripts.dal.transcript_dal import TranscriptDAL
from app.modules.meeting_transcripts.models.transcript import Transcript
from app.modules.meeting_transcripts.schemas.transcript_schemas import (
	SearchTranscriptRequest,
)
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.dal.token_usage_dal import TokenUsageDAL
from app.modules.meetings.repository.meeting_repo import MeetingRepo
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.modules.users.repository.user_repo import UserRepo

logger = logging.getLogger(__name__)

# Define persistent storage location for audio files
AUDIO_FILES_DIR = '/data/audio'


class TranscriptRepo(BaseRepo):
	"""TranscriptRepo for handling transcripts and speech-to-text operations"""

	def __init__(self, db: Session = Depends(get_db)):
		"""Initialize the TranscriptRepo

		Args:
		    db (Session): Database session
		"""
		self.db = db
		self.transcript_dal = TranscriptDAL(db)
		self.meeting_dal = MeetingDAL(db)
		self.token_usage_dal = TokenUsageDAL(db)
		self.meeting_repo = MeetingRepo(db)
		self.file_repo = MeetingFileRepo(db)
		self.user_repo = UserRepo(db)
		self.event_hooks = EventHooks()

		# Create audio directory if it doesn't exist
		os.makedirs(AUDIO_FILES_DIR, exist_ok=True)

	def _save_audio_file_to_persistent_storage(self, temp_audio_path: str) -> str:
		"""Save audio file from temporary location to persistent storage

		Args:
		    temp_audio_path (str): Path to temporary audio file

		Returns:
		    str: Path to audio file in persistent storage

		Raises:
		    CustomHTTPException: If file operation fails
		"""
		try:
			# Generate a unique filename for the audio file
			filename = f'{uuid.uuid4().hex}_{os.path.basename(temp_audio_path)}'
			persistent_path = os.path.join(AUDIO_FILES_DIR, filename)

			# Copy the file to persistent storage
			shutil.copy2(temp_audio_path, persistent_path)
			logger.info(f'Audio file copied from {temp_audio_path} to {persistent_path}')

			return persistent_path
		except Exception as ex:
			logger.error(f'Failed to copy audio file to persistent storage: {ex}')
			raise CustomHTTPException(
				message=_('audio_file_storage_failed'),
			)

	def get_meeting_transcripts(self, meeting_id: str, user_id: str) -> List[Dict[str, Any]]:
		"""Get all transcripts for a meeting

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID

		Returns:
		    List[Dict[str, Any]]: List of transcripts

		Raises:
		    NotFoundException: If meeting not found
		"""
		# Ensure meeting exists and belongs to user
		self.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		try:
			transcripts = self.transcript_dal.get_meeting_transcripts(meeting_id)
			return [transcript.to_dict() for transcript in transcripts]
		except Exception as ex:
			logger.error(f'[ERROR] Get meeting transcripts failed: {ex}')
			raise CustomHTTPException(
				message=_('get_transcripts_failed'),
			)

	def get_transcript_by_id(self, transcript_id: str, user_id: str) -> Dict[str, Any]:
		"""Get a transcript by ID

		Args:
		    transcript_id (str): Transcript ID
		    user_id (str): User ID

		Returns:
		    Dict[str, Any]: Transcript data

		Raises:
		    NotFoundException: If transcript not found
		"""
		transcript = self.transcript_dal.get_transcript_by_id(transcript_id)
		if not transcript:
			raise CustomHTTPException(message=_('transcript_not_found'))

		# Ensure transcript belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(transcript.meeting_id, user_id)

		return transcript.to_dict()

	async def create_transcript_from_text(self, meeting_id: str, user_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Create a new transcript from text data (manual upload)

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    transcript_data (Dict[str, Any]): Transcript data

		Returns:
		    Dict[str, Any]: Created transcript

		Raises:
		    NotFoundException: If meeting not found
		    CustomHTTPException: If transcript creation fails
		"""

		# Ensure meeting exists and belongs to user
		meeting = self.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		try:
			with self.transcript_dal.transaction():
				# Create transcript
				transcript_record_data = {
					'meeting_id': meeting_id,
					'content': {'text': transcript_data.get('content', {}).get('text', '') if isinstance(transcript_data.get('content'), dict) else transcript_data.get('content', '')},
					'source': AudioSourceEnum.OTHER.value,
					'language': transcript_data.get('language', meeting.language),
				}

				transcript = self.transcript_dal.create(transcript_record_data)
				self.db.commit()
				self.db.refresh(transcript)

			# Track token usage (if applicable)
			if 'token_usage' in transcript_data:
				token_usage = transcript_data['token_usage']
				if isinstance(token_usage, str):
					token_usage = json.loads(token_usage)
					self._create_token_usage(
						meeting_id,
						user_id,
						TokenOperationTypeEnum.TRANSCRIPTION.value,
						token_usage,
					)
				else:
					pass

			# Trigger transcript_created event
			self.event_hooks.trigger('transcript_created', transcript.id)

			# Log the transcript creation
			self._log_user_action(
				user_id,
				'transcript_created',
				f'Created transcript for meeting {meeting_id}',
			)
			from app.modules.meetings.repository.meeting_note_repo import MeetingNoteRepo

			meeting_note_repo = MeetingNoteRepo(self.db)
			# Generate meeting note
			# Generate meeting note with the correct parameters
			note = await meeting_note_repo.generate_meeting_note(
				meeting_id=meeting_id,
				user_id=user_id,
				transcript_id=transcript.id,
				language=transcript_data.get('language', meeting.language),
				meeting_type='general',
			)
			if note:
				# Create a notification for meeting note generation
				self._create_token_usage(
					meeting_id,
					user_id,
					TokenOperationTypeEnum.SUMMARIZATION.value,
					{
						'input_tokens': note.get('input_tokens', 0),
						'output_tokens': note.get('output_tokens', 0),
						'context_tokens': note.get('context_tokens', 0),
						'price_vnd': note.get('price_vnd', 0),
					},
				)
				self._log_user_action(
					user_id,
					'meeting_note_generated',
					f'Generated meeting note for meeting {meeting_id}',
				)
			# update meeting
			meeting_data = {
				'status': MeetingStatusEnum.COMPLETED.value,
				'meeting_type': MeetingTypeEnum.EXTENSION.value,
			}
			self.meeting_repo.update_meeting(meeting_id, user_id=meeting.user_id, meeting_data=meeting_data)
			self.db.commit()
			response = transcript.to_dict()
			response['meeting_note'] = note
			return response
		except Exception as ex:
			logger.error(f'[ERROR] Create transcript failed: {ex}')
			raise CustomHTTPException(
				message=_('create_transcript_failed'),
			)

	async def create_new_transcript_from_text(self, user_id: str, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
		"""Create a new transcript from text data (manual upload)

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    transcript_data (Dict[str, Any]): Transcript data

		Returns:
		    Dict[str, Any]: Created transcript

		Raises:
		    NotFoundException: If meeting not found
		    CustomHTTPException: If transcript creation fails
		"""

		# Ensure meeting exists and belongs to user
		try:
			# Get user to ensure they exist
			user = self.user_repo.get_user_by_id(user_id)
			if not user:
				raise CustomHTTPException(message=_('user_not_found'))

			# Create a new meeting for this transcript
			meeting_data = {
				'title': f'Text Meeting {datetime.now(timezone("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M")}',
				'description': 'Automatically created from text transcript',
				'meeting_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				'meeting_type': MeetingTypeEnum.OTHER.value,
				'status': MeetingStatusEnum.COMPLETED.value,
				'organizer_email': user.email,
				'organizer_name': user.name,
				'language': transcript_data.get('language', 'en'),
				'platform': 'Text Upload',
			}

			meeting = self.meeting_repo.create_meeting(user_id, meeting_data)

			# Create transcript
			transcript_record_data = {
				'meeting_id': meeting.id,
				'content': {'text': transcript_data.get('content', {}).get('text', '') if isinstance(transcript_data.get('content'), dict) else transcript_data.get('content', '')},
				'source': AudioSourceEnum.OTHER.value,
				'language': transcript_data.get('language', meeting.language),
			}
			with self.transcript_dal.transaction():
				transcript = self.transcript_dal.create(transcript_record_data)
				self.db.commit()
				self.db.refresh(transcript)

			# Track token usage (if applicable)
			if 'token_usage' in transcript_data:
				token_usage = transcript_data['token_usage']
				if isinstance(token_usage, str):
					token_usage = json.loads(token_usage)
					self._create_token_usage(
						meeting.id,
						user_id,
						TokenOperationTypeEnum.TRANSCRIPTION.value,
						token_usage,
					)
				else:
					pass

			# Log the transcript creation
			self._log_user_action(
				user_id,
				'transcript_created',
				f'Created transcript for new meeting {meeting.id}',
			)

			# Trigger transcript_created event
			self.event_hooks.trigger('transcript_created', transcript.id)
			from app.modules.meetings.repository.meeting_note_repo import MeetingNoteRepo

			meeting_note_repo = MeetingNoteRepo(self.db)
			# Generate meeting note
			# Generate meeting note with the correct parameters
			print('Generating meeting note...Real')
			note = await meeting_note_repo.generate_meeting_note(
				meeting_id=meeting.id,
				user_id=user_id,
				transcript_id=transcript.id,
				language=transcript_data.get('language', meeting.language),
				meeting_type='general',
			)
			if note:
				# Create a notification for meeting note generation
				self._create_token_usage(
					meeting.id,
					user_id,
					TokenOperationTypeEnum.SUMMARIZATION.value,
					{
						'input_tokens': note.get('input_tokens', 0),
						'output_tokens': note.get('output_tokens', 0),
						'context_tokens': note.get('context_tokens', 0),
						'price_vnd': note.get('price_vnd', 0),
					},
				)
				self._log_user_action(
					user_id,
					'meeting_note_generated',
					f'Generated meeting note for meeting {meeting.id}',
				)
			response = transcript.to_dict()
			response['meeting_note'] = note
			return response
		except Exception as ex:
			logger.error(f'[ERROR] Create transcript failed: {ex}')
			raise CustomHTTPException(
				message=_('create_transcript_failed'),
			)

	async def create_transcript_from_audio(
		self,
		meeting_id: str,
		user_id: str,
		audio_file_path: str,
		language: str | None = None,
	) -> Dict[str, Any]:
		"""Create a new transcript from audio file using background task

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    audio_file_path (str): Path to audio file
		    language (Optional[str]): Language code for transcription

		Returns:
		    Dict[str, Any]: Created placeholder transcript

		Raises:
		    NotFoundException: If meeting not found
		    CustomHTTPException: If transcription fails
		"""
		try:
			# Save audio file to persistent storage
			persistent_audio_path = self._save_audio_file_to_persistent_storage(audio_file_path)
			logger.info(f'Audio file saved to persistent storage: {persistent_audio_path}')

			# Create placeholder transcript and file record
			placeholder_result = await self.create_transcript_placeholder(meeting_id, user_id, persistent_audio_path, language)

			if isinstance(placeholder_result, tuple) and len(placeholder_result) >= 3:
				placeholder_transcript, file_record, meeting_dict = placeholder_result
				# print ==== with red color
				# Get the meeting ID (either from existing meeting or newly created one)
				meeting_id = placeholder_transcript['meeting_id']
				transcript_id = placeholder_transcript['id']

				# Log that we're starting the task
				logger.info(f'Starting background task for audio processing: {persistent_audio_path}')

				# Apply the task asynchronously with proper configuration using the persistent file path
				task = process_audio_task.apply_async(
					args=[
						persistent_audio_path,
						transcript_id,
						meeting_id,
						user_id,
						file_record['id'],
					],
				)

				logger.info(f'Task started with ID: {task.id}')

				# Log thông tin task đã được khởi tạo
				self._log_user_action(
					user_id,
					'transcript_processing_started',
					f'Background task started for transcribing audio file in meeting {meeting_id}',
				)

				# Cập nhật file_id trong bản ghi transcript
				if file_record:
					self.transcript_dal.update(
						transcript_id,
						{
							'file_id': file_record.get('id'),
							'audio_path': persistent_audio_path,  # Store the persistent path for reference
						},
					)
					self.db.commit()

				return placeholder_transcript
			else:
				raise CustomHTTPException(
					message=_('invalid_placeholder_result'),
				)
		except Exception as ex:
			logger.error(f'[ERROR] Create transcript from audio failed: {ex}')
			self._log_user_action(
				user_id,
				'transcript_creation_failed',
				f'Failed to create transcript: {str(ex)}',
			)
			raise CustomHTTPException(
				message=_('transcription_failed'),
			)

	async def create_new_transcript_from_audio(self, user_id: str, audio_file_path: str, language: str | None = None) -> Dict[str, Any]:
		"""Create a new transcript from audio file with a new meeting using background task

		Args:
		    user_id (str): User ID
		    audio_file_path (str): Path to audio file
		    language (Optional[str]): Language code for transcription

		Returns:
		    Dict[str, Any]: Created placeholder transcript

		Raises:
		    NotFoundException: If user not found
		    CustomHTTPException: If transcription fails
		"""
		try:
			# Save audio file to persistent storage
			persistent_audio_path = self._save_audio_file_to_persistent_storage(audio_file_path)
			logger.info(f'Audio file saved to persistent storage: {persistent_audio_path}')

			# Use create_transcript_placeholder with None as meeting_id to create a new meeting
			placeholder_result = await self.create_transcript_placeholder(None, user_id, persistent_audio_path, language)

			if isinstance(placeholder_result, tuple) and len(placeholder_result) >= 3:
				placeholder_transcript, file_record, meeting_dict = placeholder_result

				# Get the meeting ID from the newly created meeting
				meeting_id = placeholder_transcript['meeting_id']
				transcript_id = placeholder_transcript['id']

				# Log that we're starting the task
				logger.info(f'Starting background task for audio processing: {persistent_audio_path}')

				# Apply the task asynchronously with proper configuration using the persistent file path
				task = process_audio_task.apply_async(
					args=[
						persistent_audio_path,
						transcript_id,
						meeting_id,
						user_id,
						file_record['id'],
					],
				)

				logger.info(f'Task started with ID: {task.id}')

				# Log thông tin task đã được khởi tạo
				self._log_user_action(
					user_id,
					'transcript_processing_started',
					f'Background task started for transcribing audio file in new meeting {meeting_id}',
				)

				# Cập nhật file_id trong bản ghi transcript
				if file_record:
					self.transcript_dal.update(
						transcript_id,
						{
							'file_id': file_record.get('id'),
							'audio_path': persistent_audio_path,  # Store the persistent path for reference
						},
					)
					self.db.commit()

				return placeholder_transcript
			else:
				raise CustomHTTPException(
					message=_('invalid_placeholder_result'),
				)
		except Exception as ex:
			logger.error(f'[ERROR] Create transcript from audio failed: {ex}')
			# Log the failure
			self._log_user_action(
				user_id,
				'transcript_creation_failed',
				f'Failed to create transcript: {str(ex)}',
			)
			raise CustomHTTPException(
				message=_('transcription_failed'),
			)

	def _log_user_action(self, user_id: str, action: str, details: str):
		"""Log user action

		Args:
		    user_id (str): User ID
		    action (str): Action performed
		    details (str): Details of the action
		"""
		try:
			if not user_id or user_id == 'None':
				logger.warning('Cannot log action: No user ID provided')
				return

			# Create user log entry
			user_log_data = {
				'user_id': user_id,
				'action': action,
				'details': details,
			}

			# Check if user_logs_dal is available or create it
			if not hasattr(self, 'user_logs_dal'):
				self.user_logs_dal = UserLogDAL(self.db)

			self.user_logs_dal.create(user_log_data)

		except Exception as ex:
			# Just log the error, don't raise an exception as logging failure
			# shouldn't affect the main functionality
			logger.error(f'Logging error for user {user_id}: {ex}')

	def _create_token_usage(
		self,
		meeting_id: str,
		user_id: str,
		operation_type: str,
		token_usage: Dict[str, Any],
	) -> None:
		"""Create a token usage record

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    operation_type (str): Operation type
		    token_usage (Dict[str, Any]): Token usage data
		"""
		token_usage_data = {
			'user_id': user_id,
			'meeting_id': meeting_id,
			'operation_type': operation_type,
			'input_tokens': token_usage.get('input_tokens', 0),
			'output_tokens': token_usage.get('output_tokens', 0),
			'context_tokens': token_usage.get('context_tokens', 0),
			'price_vnd': token_usage.get('price_vnd', 0),
		}

		self.token_usage_dal.create(token_usage_data)

	def delete_transcript(self, transcript_id: str, user_id: str) -> bool:
		"""Delete a transcript

		Args:
		    transcript_id (str): Transcript ID
		    user_id (str): User ID

		Returns:
		    bool: True if successful

		Raises:
		    NotFoundException: If transcript not found
		"""
		transcript = self.transcript_dal.get_transcript_by_id(transcript_id)
		if not transcript:
			raise CustomHTTPException(message=_('transcript_not_found'))

		# Ensure transcript belongs to user through meeting
		self.meeting_repo.get_meeting_by_id(transcript.meeting_id, user_id)

		try:
			# Soft delete
			result = self.transcript_dal.update(transcript_id, {'is_deleted': True})
			if not result:
				raise CustomHTTPException(
					message=_('delete_transcript_failed'),
				)

			return True
		except Exception as ex:
			logger.error(f'[ERROR] Delete transcript failed: {ex}')
			raise CustomHTTPException(
				message=_('delete_transcript_failed'),
			)

	def search_transcripts(self, user_id: str, request: SearchTranscriptRequest) -> Pagination[Transcript]:
		"""Search transcripts with filters for a specific user

		Args:
		    user_id (str): User ID to filter transcripts by
		    request (SearchTranscriptRequest): Search parameters and filters

		Returns:
		    Pagination[Transcript]: Paginated transcript results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			result = self.transcript_dal.search_transcripts(user_id, request.model_dump())
			return result
		except Exception as ex:
			logger.error(f'[ERROR] Search transcripts failed: {ex}')
			raise CustomHTTPException(
				message=_('search_transcripts_failed'),
			)

	def admin_search_transcripts(self, request: dict) -> Pagination[Transcript]:
		"""Admin search for transcripts across all users

		Args:
		    request (dict): Search parameters and filters

		Returns:
		    Pagination[Transcript]: Paginated transcript results

		Raises:
		    CustomHTTPException: If search operation fails
		"""
		try:
			return self.transcript_dal.admin_search_transcripts(request)
		except Exception:
			raise CustomHTTPException(
				message=_('search_transcripts_failed'),
			)

	async def create_transcript_placeholder(
		self,
		meeting_id: str,
		user_id: str,
		audio_file_path: str,
		language: str | None = None,
	) -> Dict[str, Any]:
		"""Create a placeholder transcript record for async processing

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    audio_file_path (str): Path to the audio file
		    language (Optional[str]): Language code for transcription

		Returns:
		    Dict[str, Any]: Placeholder transcript

		Raises:
		    NotFoundException: If meeting not found
		"""
		user = self.user_repo.get_user_by_id(user_id)
		if not user:
			raise CustomHTTPException(message=_('user_not_found'))
		# Ensure meeting exists and belongs to user
		if not meeting_id or meeting_id == 'None':
			# Create meeting data for a new meeting from audio file

			meeting_data = {
				'title': f'Meeting {datetime.now(timezone("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M")}',
				'description': 'Automatically created from uploaded audio file',
				'meeting_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				'meeting_type': MeetingTypeEnum.OTHER.value,
				'status': MeetingStatusEnum.COMPLETED.value,
				'organizer_email': user.email,
				'organizer_name': user.name,
				'language': language or 'en',
				'platform': 'File Upload',
			}

			# Create a meeting and log the action
			meeting = self.meeting_repo.create_meeting(user_id, meeting_data)
			self.db.commit()
		else:
			meeting = self.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		# Set language from meeting if not provided
		if not language:
			language = meeting.language

		try:
			self._log_user_action(
				user_id,
				'transcript_creation_started',
				f'Started asynchronous transcription process for meeting {meeting.id}',
			)
			# Create a placeholder transcript record to track the request
			placeholder_transcript_data = {
				'meeting_id': meeting.id,
				'content': {
					'text': 'PROCESSING ...',
				},
				'source': AudioSourceEnum.OTHER.value,
				'language': language or 'en',
			}

			placeholder_transcript = self.transcript_dal.create(placeholder_transcript_data)

			# Trigger transcript_created event
			self.event_hooks.trigger('transcript_created', placeholder_transcript.id)

			upload_file = UploadFile(
				filename=audio_file_path.split('/')[-1],
				file=None,
			)

			# Set the file content
			upload_file.file = open(audio_file_path, 'rb')

			# Upload to MinIO and create file entry in database
			file_record = await self.file_repo.upload_meeting_file(
				meeting_id=meeting.id,
				user_id=user_id,
				file=upload_file,
				file_type=FileTypeEnum.AUDIO.value,
			)
			# After upload is complete, close the file
			upload_file.file.close()
			self.db.commit()
			if meeting_id:
				return placeholder_transcript.to_dict(), file_record, meeting.to_dict()
			else:
				return placeholder_transcript.to_dict(), file_record, None
		except Exception as ex:
			logger.error(f'[ERROR] Creating transcript placeholder failed: {ex}')
			raise CustomHTTPException(
				message=_('create_transcript_failed'),
			)
