from app.core.base_model import ResponseSchema, APIResponse
from pydantic import ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class QuestionAnswerResponse(ResponseSchema):
	"""Response schema for question answers"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	session_id: str
	question_id: str
	question_text: Optional[str]
	answer_data: Dict[str, Any]
	answer_type: str
	submitted_at: Optional[datetime]
	create_date: datetime


class QuestionSessionResponse(ResponseSchema):
	"""Response schema for question sessions"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	name: str
	conversation_id: str
	user_id: str
	parent_session_id: Optional[str]
	session_type: str
	questions_data: Optional[List[Dict[str, Any]]]
	session_status: str
	start_date: Optional[datetime]
	completion_date: Optional[datetime]
	extra_metadata: Optional[str]
	create_date: datetime
	update_date: Optional[datetime]

	# Include answers if needed
	answers: Optional[List[QuestionAnswerResponse]] = Field(default=None)


class QuestionSessionDetailResponse(ResponseSchema):
	"""Detailed response schema for question sessions with all related data"""

	model_config = ConfigDict(from_attributes=True)

	session: QuestionSessionResponse
	answers: List[QuestionAnswerResponse]
	followup_sessions: Optional[List[QuestionSessionResponse]] = Field(default=None)


class CreateQuestionSessionResponse(APIResponse):
	"""Response for creating question session"""

	pass


class SubmitAnswersResponse(APIResponse):
	"""Response for submitting answers"""

	pass


class GetQuestionSessionsResponse(APIResponse):
	"""Response for getting question sessions list"""

	pass


class ParsedSurveyResponse(ResponseSchema):
	"""Response schema for parsed survey data"""

	session_id: str
	conversation_id: str
	total_answers: int
	answers_processed: int
	session_status: str
	completion_date: Optional[datetime]


class CompleteSurveyWorkflowResponse(ResponseSchema):
	"""Response schema for complete survey workflow processing"""

	survey_processing: Dict[str, Any]
	human_readable_response: str
	ai_response: Optional[Dict[str, Any]]
	processing_metadata: Dict[str, Any]


class FormatSurveyAsHumanMessageResponse(ResponseSchema):
	"""Response schema for formatted survey as human message"""

	human_message: str
	conversation_id: str
	processed_at: str
	user_id: str
	message_length: int
	include_analysis_request: bool


class SurveyChatIntegrationResponse(ResponseSchema):
	"""Response schema for survey chat integration"""

	survey_data: Dict[str, Any]
	human_message: str
	ai_response: Dict[str, Any]
	integration_metadata: Dict[str, Any]
