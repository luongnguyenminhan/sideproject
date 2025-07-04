from app.core.base_model import RequestSchema, FilterableRequestSchema
from pydantic import Field
from typing import Optional, Dict, Any, List


class CreateQuestionSessionRequest(RequestSchema):
	"""Request schema for creating a new question session"""

	name: str = Field(..., description='Session name')
	conversation_id: str = Field(..., description='Associated conversation ID')
	session_type: str = Field(default='survey', description='Type of session (survey, quiz, assessment)')
	questions_data: Optional[List[Dict[str, Any]]] = Field(default=None, description='Questions data structure')
	parent_session_id: Optional[str] = Field(default=None, description='Parent session ID for follow-up sessions')
	extra_metadata: Optional[str] = Field(default=None, description='Additional metadata as JSON string')


class UpdateQuestionSessionRequest(RequestSchema):
	"""Request schema for updating a question session"""

	name: Optional[str] = Field(default=None, description='Session name')
	session_status: Optional[str] = Field(default=None, description='Session status')
	questions_data: Optional[List[Dict[str, Any]]] = Field(default=None, description='Questions data structure')
	extra_metadata: Optional[str] = Field(default=None, description='Additional metadata as JSON string')


class SubmitAnswersRequest(RequestSchema):
	"""Request schema for submitting answers to a question session"""

	session_id: str = Field(..., description='Question session ID')
	answers: Dict[str, Any] = Field(..., description='Answers data mapping question_id to answer')
	conversation_id: Optional[str] = Field(default=None, description='Conversation ID for validation')


class GetQuestionSessionsRequest(FilterableRequestSchema):
	"""Request schema for getting question sessions with filtering"""

	conversation_id: Optional[str] = Field(default=None, description='Filter by conversation ID')
	session_status: Optional[str] = Field(default=None, description='Filter by session status')
	session_type: Optional[str] = Field(default=None, description='Filter by session type')
	order_by: str = Field(default='create_date', description='Order by field')
	order_direction: str = Field(default='desc', description='Order direction (asc/desc)')


class ParseSurveyResponseRequest(RequestSchema):
	"""Request schema for parsing survey response from WebSocket"""

	type: str = Field(..., description="Message type (should be 'survey_response')")
	answers: Dict[str, Any] = Field(..., description='Raw answers data from frontend')
	conversation_id: str = Field(..., description='Conversation ID')
	session_id: Optional[str] = Field(default=None, description='Question session ID for question metadata')
	timestamp: Optional[str] = Field(default=None, description='Response timestamp')


class CompleteSurveyWorkflowRequest(RequestSchema):
	"""Request schema for complete survey workflow processing with AI integration"""

	type: str = Field(..., description="Message type (should be 'survey_response')")
	answers: Dict[str, Any] = Field(..., description='Raw answers data from frontend')
	conversation_id: str = Field(..., description='Conversation ID')
	session_id: Optional[str] = Field(default=None, description='Question session ID for question metadata')
	timestamp: Optional[str] = Field(default=None, description='Response timestamp')
	processing_type: Optional[str] = Field(
		default='analysis',
		description='Type of AI processing: analysis, summary, insights',
	)
	custom_ai_prompt: Optional[str] = Field(default=None, description='Custom prompt for AI processing')
	enable_chat_integration: Optional[bool] = Field(default=True, description='Enable chat integration')


class FormatSurveyAsHumanMessageRequest(RequestSchema):
	"""Request schema for formatting survey response as human message"""

	type: str = Field(..., description="Message type (should be 'survey_response')")
	answers: Dict[str, Any] = Field(..., description='Raw answers data from frontend')
	conversation_id: str = Field(..., description='Conversation ID')
	session_id: Optional[str] = Field(default=None, description='Question session ID for question metadata')
	timestamp: Optional[str] = Field(default=None, description='Response timestamp')
	include_analysis_request: Optional[bool] = Field(default=True, description='Include request for AI analysis')
