"""
Question generation request schemas.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from app.core.base_model import RequestSchema, FilterableRequestSchema


class QuestionGenerationRequest(RequestSchema):
	"""Request for generating questions"""

	session_id: Optional[str] = Field(None, description='Session ID for tracking')
	user_id: Optional[str] = Field(None, description='User ID')
	existing_user_data: Optional[Dict[str, Any]] = Field(None, description='Existing user profile data')
	previous_questions: List[Dict[str, Any]] = Field(default_factory=list, description='Previously asked questions')
	focus_areas: List[str] = Field(default_factory=list, description='Specific areas to focus on')
	max_questions: int = Field(4, description='Maximum number of questions to generate')
	max_iterations: int = Field(5, description='Maximum workflow iterations')


class AnalyzeUserProfileRequest(RequestSchema):
	"""Request for analyzing user profile completeness"""

	user_profile: Dict[str, Any] = Field(..., description='User profile data to analyze')
	previous_questions: List[Dict[str, Any]] = Field(default_factory=list, description='Previously asked questions')


class GetQuestionSessionRequest(RequestSchema):
	"""Request for getting question session"""

	session_id: str = Field(..., description='Session ID to retrieve')


class SearchQuestionSessionsRequest(FilterableRequestSchema):
	"""Request for searching question sessions with filtering"""

	user_id: Optional[str] = Field(None, description='Filter by user ID')
	status: Optional[str] = Field(None, description='Filter by session status')
	session_id: Optional[str] = Field(None, description='Filter by session ID')
