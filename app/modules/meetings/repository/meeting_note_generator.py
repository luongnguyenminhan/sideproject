"""Meeting note generator module for AI-powered meeting note generation"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import status
from pytz import timezone

from app.enums.meeting_enums import (
	MeetingItemTypeEnum,
	TokenOperationTypeEnum,
	MeetingStatusEnum,
	MeetingTypeEnum,
)
from app.exceptions.exception import CustomHTTPException
from app.middleware.translation_manager import _
from app.modules.meetings.utils.meeting_note_utils import (
	create_token_usage,
	create_note_generated_notification,
	extract_title_from_note_content,
	process_response_items,
	parse_conversation_summary,
)
from app.utils.agent_open_ai_api import AgentMicroService
from app.utils.otp_utils import OTPUtils

logger = logging.getLogger(__name__)


class MeetingNoteGenerator:
	"""Class for generating meeting notes from transcripts using AI"""

	def __init__(self, repo):
		"""Initialize the MeetingNoteGenerator

		Args:
		    repo: The main MeetingNoteRepo instance
		"""
		self.repo = repo
		self.agent_open_ai_api = AgentMicroService()

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

		Args:
		    meeting_id (str): Meeting ID
		    user_id (str): User ID
		    transcript_id (str): Transcript ID
		    language (Optional[str]): Language code for note generation
		    custom_prompt (Optional[str]): Custom prompt for note generation
		    meeting_type (Optional[str]): Type of the meeting
		Returns:
		    Dict[str, Any]: Generated meeting note

		Raises:
		    NotFoundException: If meeting or transcript not found
		    CustomHTTPException: If note generation fails
		"""

		# Ensure meeting exists and belongs to user
		meeting = self.repo.meeting_repo.get_meeting_by_id(meeting_id, user_id)

		user = self.repo.user_dal.get_user_by_id(user_id)
		# Get transcript
		transcript = self.repo.transcript_dal.get_transcript_by_id(transcript_id)
		if not transcript:
			raise CustomHTTPException(message=_('transcript_not_found'))

		# Ensure transcript belongs to the meeting
		if transcript.meeting_id != meeting_id:
			raise CustomHTTPException(
				message=_('transcript_not_for_meeting'),
			)

		# Set language from meeting if not provided
		if not language:
			language = meeting.language

		try:
			# Call the API to generate meeting notes
			response = await self.agent_open_ai_api.post_message_v2(
				transcript=transcript.content.get('text', '') if isinstance(transcript.content, dict) else transcript.content,
				email=None,
				meeting_type=meeting_type,
				custom_prompt=custom_prompt,
			)

			# Extract data from the response
			meeting_note_content = response.get('meeting_note', 'No content generated')

			# Process task items
			current_time = datetime.now(timezone('Asia/Ho_Chi_Minh'))
			meeting_items = process_response_items(response, current_time)

			# Extract token usage data from the response
			token_usage = {
				'input_tokens': response.get('token_usage', {}).get('input_tokens', 0),
				'output_tokens': response.get('token_usage', {}).get('output_tokens', 0),
				'context_tokens': response.get('token_usage', {}).get('context_tokens', 0),
			}

			# Create meeting note with related items
			with self.repo.meeting_note_dal.transaction():
				# Create note
				note_data = {
					'meeting_id': meeting_id,
					'transcript_id': transcript_id,
					'content': {'text': meeting_note_content},
					'version': 1,
					'is_latest': True,
					'is_encrypted': meeting.is_encrypted,
					'encryption_key': (meeting.encryption_key if meeting.is_encrypted else None),
				}

				note = self.repo.meeting_note_dal.create(note_data)
				self.repo.db.commit()
				self.repo.db.refresh(note)

				# Create meeting items
				for i, item_data in enumerate(meeting_items):
					item_data['meeting_note_id'] = note.id
					item = self.repo.meeting_item_dal.create(item_data)

				# Track token usage
				create_token_usage(
					self.repo.token_usage_dal,
					meeting_id,
					user_id,
					TokenOperationTypeEnum.SUMMARIZATION.value,
					token_usage,
				)

				# Create notification
				create_note_generated_notification(self.repo.notification_dal, meeting_id, user_id)

				# Get note with related items
				result = self.repo.get_note_by_id(
					note.id,
					user_id,
					include_items=True,
				)

				# Automatically save note as PDF
				try:
					await self.repo.meeting_file_repo.save_note_as_pdf(note.id, user_id)
				except Exception as pdf_ex:
					# Log error but don't fail the operation if PDF generation fails
					logger.error(f'[ERROR] Failed to save note as PDF: {pdf_ex}')

				if user.email:
					send_email = OTPUtils()
					send_email.send_meeting_note_to_email(user.email, str(note.content))
				return result
		except Exception as ex:
			logger.error(f'[ERROR] Generate meeting note failed: {ex}')
			raise CustomHTTPException(
				message=_('generate_note_failed'),
			)

	async def generate_meeting_note_no_authen(self, prompt: str, email: str | None = None) -> Dict[str, Any]:
		"""Generate a meeting note without authentication

		This method uses the external AI service to generate a meeting note without requiring authentication.
		It creates a transcript record and a meeting note in the database, and optionally sends the
		note to the provided email address. If no user is found for the given email, it creates an anonymous
		meeting to store the transcript and note.

		Args:
		    prompt (str): The transcript content to generate meeting note from
		    email (Optional[str]): Optional email to send the meeting note to

		Returns:
		    Dict[str, Any]: Generated meeting note with token usage information
		"""
		try:
			# Use the agent service to generate meeting note
			agent_service = AgentMicroService()
			response = await agent_service.post_message(prompt, email)

			if not response:
				raise CustomHTTPException(
					message=_('generate_note_failed'),
				)

			result = {
				'summary': response['meeting_note'],
				'token_usage': response['token_usage'],
			}

			# Extract title from meeting note if possible
			title = extract_title_from_note_content(response['meeting_note'])

			# Get current time with timezone
			current_time = datetime.now(timezone('Asia/Ho_Chi_Minh'))

			# Find user by email if provided
			user_id = None
			if email:
				user = self.repo.user_dal.get_user_by_email(email)
				if user:
					user_id = str(user.id)
				else:
					pass
			# Process response items into meeting items
			meeting_items = process_response_items(response, current_time)

			try:
				# Prepare data objects
				meeting_data = {
					'user_id': user_id,  # Will be None if no user was found
					'title': title,
					'description': 'Automatically generated from transcript',
					'meeting_date': current_time,
					'status': MeetingStatusEnum.COMPLETED.value,
					'meeting_type': MeetingTypeEnum.ANONYMOUS.value,
					'is_encrypted': False,
					'is_recurring': False,
					'language': 'vi',
					'create_date': current_time,
					'update_date': current_time,
				}

				transcript_data = {
					'content': {'text': prompt},
					'source': 'other',
					'language': 'vi',  # Default language
					'create_date': current_time,
					'update_date': current_time,
				}

				note_data = {
					'content': {'text': response['meeting_note']},
					'version': 1,
					'is_latest': True,
					'is_encrypted': False,
					'create_date': current_time,
					'update_date': current_time,
				}

				# Create token usage data if we have a user
				token_usage_data = None
				if 'token_usage' in response:
					token_usage_data = {
						'user_id': user_id,
						'operation_type': TokenOperationTypeEnum.SUMMARIZATION.value,
						'input_tokens': response['token_usage'].get('input_tokens', 0),
						'output_tokens': response['token_usage'].get('output_tokens', 0),
						'context_tokens': response['token_usage'].get('context_tokens', 0),
						'create_date': current_time,
						'update_date': current_time,
					}

				result_objects = self.repo.meeting_note_dal.create_meeting_note_with_related_data(
					meeting_data=meeting_data,
					transcript_data=transcript_data,
					note_data=note_data,
					meeting_items=meeting_items,
					token_usage_data=token_usage_data,
				)
				self.repo.db.commit()
				try:
					await self.repo.meeting_file_repo.save_note_as_pdf(result_objects['note'].id, result_objects['meeting'].user_id)
				except Exception as pdf_ex:
					# Log error but don't fail the operation if PDF generation fails
					print(f'[ERROR] Failed to save note as PDF: {pdf_ex}')
				if result_objects['token_usage']:
					print(f'Token usage: {str(result_objects["token_usage"].to_dict())}')

			except Exception as ex:
				raise

			return result
		except Exception as ex:
			raise CustomHTTPException(
				message=_('generate_note_failed'),
			)

	async def generate_conversation_summary(self, prompt: str):
		"""Generate a summary of a conversation

		Args:
		    prompt (str): Conversation text to summarize

		Returns:
		    Dict[str, Any]: Summary result with title, summary text, tags and token usage
		"""
		# Use the agent service to generate summary
		agent_service = AgentMicroService()
		response = await agent_service.post_summary(prompt)

		# Extract title and tags from the response
		conversation_summary = response['conversation_summary']
		title, tags = parse_conversation_summary(conversation_summary)

		result = {
			'title': title,
			'summary': conversation_summary,
			'tags': tags,
			'token_usage': response['token_usage'],
		}

		return result
