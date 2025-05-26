"""Conversation Summary API Routes"""

from fastapi import APIRouter, Body, Depends, Header
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.modules.meetings.repository.meeting_note_repo import MeetingNoteRepo
from app.modules.meetings.schemas.conversation_schemas import (
	ConversationSummaryRequest,
)

# API token for public endpoints
API_TOKEN_KEY = '20266b8af7acf6dea12999a1d03ba25d'

# Create two separate routers - one for authenticated routes, one for public routes
route = APIRouter(
	prefix='',
	tags=['Conversation Summary'],
)


@route.post('/conversation-summary', response_model=APIResponse)
@handle_exceptions
async def generate_conversation_summary(
	request_data: ConversationSummaryRequest = Body(...),
	db: Session = Depends(get_db),
):
	"""Generate a summary from conversation transcript

	This endpoint processes a conversation transcript and generates a structured summary
	including a title, markdown-formatted summary text, extracted tags, and token usage information.

	Args:
	    request_data: Conversation transcript and optional email

	Returns:
	    Structured conversation summary
	"""
	# Initialize repository
	meeting_note_repo = MeetingNoteRepo(db)

	# Generate summary
	result = await meeting_note_repo.generate_conversation_summary(
		request_data.prompt,
	)

	return APIResponse(
		error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
		message=_('conversation_summary_success'),
		data=result,
	)


@route.post('/generate-meeting-note', response_model=APIResponse)
@handle_exceptions
async def generate_meeting_note_public(
	request_data: ConversationSummaryRequest = Body(...),
	token_key: str = Header(..., alias='token-key'),
	db: Session = Depends(get_db),
):
	"""Generate a meeting note without authentication

	This endpoint processes a conversation transcript and generates a meeting note
	without requiring user authentication. Instead, it uses a token-key header for authorization.

	Args:
	    request_data: Conversation transcript and optional email
	    token_key: API token key for authorization

	Returns:
	    Generated meeting note with token usage information
	"""
	# Verify the token key
	if token_key != API_TOKEN_KEY:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('invalid_or_missing_token_key'),
			data=None,
		)

	try:
		# Initialize repository
		meeting_note_repo = MeetingNoteRepo(db)
		# Generate meeting note
		result = await meeting_note_repo.generate_meeting_note_no_authen(request_data.prompt, email=request_data.email)
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
			message=_('generate_note_success'),
			data=result,
		)
	except Exception:
		return APIResponse(
			error_code=BaseErrorCode.ERROR_CODE_FAIL,
			message=_('generate_note_failed'),
			data=None,
		)
