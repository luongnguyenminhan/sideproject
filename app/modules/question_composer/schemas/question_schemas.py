"""
Question schemas following the frontend question API structure.
"""

from typing import List, Optional, Union, Any, Dict, Literal
from pydantic import BaseModel, Field


class QuestionOption(BaseModel):
	"""Question option for single/multiple choice"""

	id: str = Field(..., description='Unique identifier for the option')
	label: str = Field(..., description='Display label for the option')


class TextInputField(BaseModel):
	"""Text input field configuration"""

	id: str = Field(..., description='Unique identifier for the field')
	label: str = Field(..., description='Display label for the field')
	type: str = Field(..., description='Input type (text, email, tel, etc.)')
	placeholder: str = Field(..., description='Placeholder text')
	required: bool = Field(default=True, description='Whether field is required')


class SubQuestion(BaseModel):
	"""Sub-question for sub_form type"""

	id: str = Field(..., description='Unique identifier for sub-question')
	Question: str = Field(..., description='Sub-question text')
	Question_type: Literal['single_option', 'multiple_choice'] = Field(..., description='Sub-question type')
	Question_data: List[QuestionOption] = Field(..., description='Sub-question options')


class Question(BaseModel):
	"""Main question structure matching frontend API"""

	id: str = Field(..., description='Unique identifier for the question')
	Question: str = Field(..., description='Question text')
	Question_type: Literal['single_option', 'multiple_choice', 'text_input', 'sub_form'] = Field(..., description='Type of question')
	subtitle: Optional[str] = Field(None, description='Subtitle or description')
	Question_data: Union[List[QuestionOption], List[TextInputField], List[SubQuestion]] = Field(..., description='Question data based on type')


class UserProfile(BaseModel):
	"""User profile structure for analysis"""

	current_role: Optional[str] = Field(None, description='Current professional role')
	skills: List[str] = Field(default_factory=list, description='Technical skills')
	interests: List[str] = Field(default_factory=list, description='Areas of interest')
	goals: List[str] = Field(default_factory=list, description='Professional goals')
	experience_level: Optional[str] = Field(None, description='Experience level')
	industry: Optional[str] = Field(None, description='Industry')
	personal_info: Dict[str, Any] = Field(default_factory=dict, description='Personal information')
	additional_info: Dict[str, Any] = Field(default_factory=dict, description='Additional user data')


class QuestionGenerationRequest(BaseModel):
	"""Request for generating questions"""

	existing_user_data: Optional[UserProfile] = Field(None, description='Existing user profile data')
	previous_questions: List[Question] = Field(default_factory=list, description='Previously asked questions')
	focus_areas: List[str] = Field(default_factory=list, description='Specific areas to focus on')
	max_questions: int = Field(4, description='Maximum number of questions to generate')


class QuestionGenerationResponse(BaseModel):
	"""Response containing generated questions"""

	questions: List[Question] = Field(..., description='Generated questions')
	analysis: str = Field(..., description='Analysis of user profile completeness')
	next_focus_areas: List[str] = Field(..., description='Areas that need more information')
	completeness_score: float = Field(..., description='User profile completeness score (0-1)')
	should_continue: bool = Field(..., description='Whether more questions are needed')


class AnalysisDecision(BaseModel):
	"""Decision from analysis node"""

	decision: Literal['sufficient', 'need_more_info'] = Field(..., description='Whether user information is sufficient')
	missing_areas: List[str] = Field(default_factory=list, description='Areas that need more information')
	reasoning: str = Field(..., description='Reasoning for the decision')
	completeness_score: float = Field(..., description='User profile completeness score (0-1)')
	suggested_focus: List[str] = Field(default_factory=list, description='Suggested areas to focus on next')
