"""
Question generation response schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field, ConfigDict

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import ResponseSchema, APIResponse


class QuestionOptionResponse(ResponseSchema):
	"""Question option response"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Option ID')
	label: str = Field(..., description='Option label')


class TextInputFieldResponse(ResponseSchema):
	"""Text input field response"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Field ID')
	label: str = Field(..., description='Field label')
	type: str = Field(..., description='Input type')
	placeholder: str = Field(..., description='Placeholder text')
	required: bool = Field(..., description='Whether field is required')


class SubQuestionResponse(ResponseSchema):
	"""Sub-question response"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Sub-question ID')
	Question: str = Field(..., description='Sub-question text')
	Question_type: str = Field(..., description='Sub-question type')
	Question_data: List[QuestionOptionResponse] = Field(..., description='Sub-question options')


class QuestionResponse(ResponseSchema):
	"""Question response"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Question ID')
	Question: str = Field(..., description='Question text')
	Question_type: str = Field(..., description='Question type')
	subtitle: Optional[str] = Field(None, description='Question subtitle')
	Question_data: List[Any] = Field(..., description='Question data based on type')


class QuestionGenerationResponse(ResponseSchema):
	"""Response for question generation"""

	model_config = ConfigDict(from_attributes=True)

	session_id: str = Field(..., description='Session ID')
	questions: List[QuestionResponse] = Field(..., description='Generated questions')
	analysis: str = Field(..., description='Analysis of user profile completeness')
	next_focus_areas: List[str] = Field(..., description='Areas that need more information')
	completeness_score: float = Field(..., description='User profile completeness score (0-1)')
	should_continue: bool = Field(..., description='Whether more questions are needed')
	current_iteration: int = Field(..., description='Current workflow iteration')
	total_questions_generated: int = Field(..., description='Total questions generated so far')


class UserProfileAnalysisResponse(ResponseSchema):
	"""Response for user profile analysis"""

	model_config = ConfigDict(from_attributes=True)

	completeness_score: float = Field(..., description='Profile completeness score')
	missing_areas: List[str] = Field(..., description='Missing information areas')
	analysis: str = Field(..., description='Analysis summary')
	should_continue: bool = Field(..., description='Whether more information is needed')
	suggested_focus: List[str] = Field(..., description='Suggested focus areas')


class QuestionSessionResponse(ResponseSchema):
	"""Response for question session"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Session entity ID')
	session_id: str = Field(..., description='Session ID')
	user_id: Optional[str] = Field(None, description='User ID')
	status: str = Field(..., description='Session status')
	current_iteration: int = Field(..., description='Current iteration')
	max_iterations: int = Field(..., description='Maximum iterations')
	completeness_score: float = Field(..., description='Completeness score')
	should_continue: bool = Field(..., description='Should continue flag')
	workflow_complete: bool = Field(..., description='Workflow complete flag')
	total_questions_generated: int = Field(..., description='Total questions generated')
	missing_areas: Optional[List[str]] = Field(None, description='Missing areas')
	focus_areas: Optional[List[str]] = Field(None, description='Focus areas')
	error_message: Optional[str] = Field(None, description='Error message if any')
	create_date: str = Field(..., description='Creation date')
	update_date: str = Field(..., description='Last update date')


class QuestionSessionListResponse(APIResponse):
	"""Response for question session list"""

	pass


class QuestionGenerationAPIResponse(APIResponse):
	"""API Response for question generation"""

	pass


class UserProfileAnalysisAPIResponse(APIResponse):
	"""API Response for user profile analysis"""

	pass


class QuestionSessionAPIResponse(APIResponse):
	"""API Response for question session"""

	pass
