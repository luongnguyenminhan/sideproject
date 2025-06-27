"""
N8N API Response Schemas
Schemas for handling N8N API responses and converting them to our format
"""

from typing import List, Optional, Dict, Any
from pydantic import Field, ConfigDict
from app.core.base_model import ResponseSchema


class N8NQuestionOption(ResponseSchema):
	"""Option for N8N question"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Option ID')
	label: str = Field(..., description='Option label')
	value: Optional[str] = Field(None, description='Option value')


class N8NQuestion(ResponseSchema):
	"""Question from N8N API"""

	model_config = ConfigDict(from_attributes=True)

	id: str = Field(..., description='Question ID')
	question: str = Field(..., description='Question text')
	type: str = Field(..., description='Question type')
	subtitle: Optional[str] = Field(None, description='Question subtitle')
	options: Optional[List[N8NQuestionOption]] = Field(None, description='Question options')
	data: Optional[List[Any]] = Field(None, description='Question data')
	required: bool = Field(True, description='Whether question is required')
	order: Optional[int] = Field(None, description='Question order')


class N8NAnalysis(ResponseSchema):
	"""Analysis from N8N API"""

	model_config = ConfigDict(from_attributes=True)

	completeness_score: float = Field(..., description='Profile completeness score (0-1)')
	should_continue: bool = Field(..., description='Whether more questions are needed')
	next_focus_areas: List[str] = Field(default_factory=list, description='Areas that need more information')
	analysis_text: str = Field(..., description='Analysis summary text')
	missing_areas: Optional[List[str]] = Field(None, description='Missing information areas')
	suggested_focus: Optional[List[str]] = Field(None, description='Suggested focus areas')


class N8NSessionInfo(ResponseSchema):
	"""Session info from N8N API"""

	model_config = ConfigDict(from_attributes=True)

	session_id: str = Field(..., description='Session ID')
	current_iteration: Optional[int] = Field(None, description='Current iteration')
	total_questions_generated: Optional[int] = Field(None, description='Total questions generated')
	status: Optional[str] = Field(None, description='Session status')


class N8NAPIResponse(ResponseSchema):
	"""Complete response from N8N API"""

	model_config = ConfigDict(from_attributes=True)

	status: str = Field(..., description='Response status')
	type: str = Field(..., description='Response type')
	session_info: Optional[N8NSessionInfo] = Field(None, description='Session information')
	analysis: Optional[N8NAnalysis] = Field(None, description='Analysis results')
	questions: List[N8NQuestion] = Field(default_factory=list, description='Generated questions')
	error: Optional[str] = Field(None, description='Error message if any')


def convert_n8n_to_internal_format(n8n_response: Dict[str, Any]) -> Dict[str, Any]:
	"""
	Convert N8N API response to our internal format

	Args:
	    n8n_response: Response từ N8N API

	Returns:
	    Response theo format internal của chúng ta
	"""
	# Default values
	result = {
		'session_id': n8n_response.get('sessionId', 'unknown'),
		'questions': [],
		'analysis': n8n_response.get('analysis', 'No analysis provided'),
		'next_focus_areas': n8n_response.get('next_focus_areas', []),
		'completeness_score': n8n_response.get('completeness_score', 0.5),
		'should_continue': n8n_response.get('should_continue', True),
		'current_iteration': n8n_response.get('current_iteration', 1),
		'total_questions_generated': 0,
	}

	# Convert questions
	questions = n8n_response.get('questions', [])
	converted_questions = []

	for i, question in enumerate(questions):
		if isinstance(question, dict):
			converted_question = {
				'id': question.get('id', f'q_{i + 1}'),
				'Question': question.get('question', question.get('Question', '')),
				'Question_type': question.get('type', question.get('Question_type', 'text_input')),
				'subtitle': question.get('subtitle'),
				'Question_data': question.get('data', question.get('Question_data', question.get('options', []))),
				'required': question.get('required', True),
				'order': question.get('order', i + 1),
			}
			converted_questions.append(converted_question)

	result['questions'] = converted_questions
	result['total_questions_generated'] = len(converted_questions)

	# Handle session info
	session_info = n8n_response.get('session_info', {})
	if session_info:
		result['session_id'] = session_info.get('session_id', result['session_id'])
		result['current_iteration'] = session_info.get('current_iteration', result['current_iteration'])
		result['total_questions_generated'] = session_info.get('total_questions_generated', result['total_questions_generated'])

	# Handle analysis
	analysis_data = n8n_response.get('analysis', {})
	if isinstance(analysis_data, dict):
		result['completeness_score'] = analysis_data.get('completeness_score', result['completeness_score'])
		result['should_continue'] = analysis_data.get('should_continue', result['should_continue'])
		result['next_focus_areas'] = analysis_data.get('next_focus_areas', result['next_focus_areas'])
		result['analysis'] = analysis_data.get('analysis_text', analysis_data.get('analysis', result['analysis']))

	return result
