"""
Workflow state for question generation workflow.
"""

from typing import List, Dict, Any, Optional, TypedDict

from app.modules.question_composer.schemas.question_schemas import AnalysisDecision, Question, UserProfile


class QuestionGenerationState(TypedDict):
	"""
	State for the question generation workflow.

	This state tracks the entire question generation process including:
	- User profile and existing data
	- Generated questions across iterations
	- Analysis decisions and completeness
	- Workflow metadata
	"""

	# Core user data
	user_profile: UserProfile
	existing_user_data: Dict[str, Any]

	# Question generation
	generated_questions: List[Question]
	all_previous_questions: List[Question]
	current_iteration: int
	max_iterations: int

	# Analysis and decision making
	analysis_decision: Optional[AnalysisDecision]
	completeness_score: float
	missing_areas: List[str]
	focus_areas: List[str]

	# Workflow control
	should_continue: bool
	workflow_complete: bool
	error_message: Optional[str]

	# Metadata
	generation_history: List[Dict[str, Any]]
	total_questions_generated: int
	session_id: Optional[str]
