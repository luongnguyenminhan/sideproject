"""
Business Process Configuration for Chat Workflow
Definition of business rules, validation processes, and workflow logic
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class BusinessProcessType(str, Enum):
	"""Types of business processes supported"""

	CUSTOMER_SUPPORT = 'customer_support'
	SALES_INQUIRY = 'sales_inquiry'
	TECHNICAL_ASSISTANCE = 'technical_assistance'
	CV_ANALYSIS = 'cv_analysis'
	CAREER_GUIDANCE = 'career_guidance'
	GENERAL_CONVERSATION = 'general_conversation'
	SURVEY_GENERATION = 'survey_generation'


class ProcessStep(str, Enum):
	"""Standard process steps"""

	INTAKE = 'intake'
	VALIDATION = 'validation'
	PROCESSING = 'processing'
	REVIEW = 'review'
	COMPLETION = 'completion'
	ESCALATION = 'escalation'


@dataclass
class BusinessRule:
	"""Individual business rule definition"""

	name: str
	description: str
	condition: str  # Python expression or pattern
	action: str  # Action to take when rule triggers
	priority: int = 1  # Higher numbers = higher priority
	enabled: bool = True


@dataclass
class ProcessDefinition:
	"""Complete business process definition"""

	process_type: BusinessProcessType
	name: str
	description: str
	steps: List[ProcessStep]
	rules: List[BusinessRule]
	required_tools: List[str]
	escalation_conditions: List[str]
	completion_criteria: List[str]


class BusinessProcessManager:
	"""Manages business processes and rules enforcement"""

	def __init__(self):
		self.processes = self._initialize_processes()
		self.active_rules = {}

	def _initialize_processes(self) -> Dict[BusinessProcessType, ProcessDefinition]:
		"""Initialize all business process definitions"""
		return {
			BusinessProcessType.CV_ANALYSIS: ProcessDefinition(
				process_type=BusinessProcessType.CV_ANALYSIS,
				name='CV Analysis Process',
				description='Process for analyzing user CVs and providing career guidance',
				steps=[ProcessStep.INTAKE, ProcessStep.PROCESSING, ProcessStep.REVIEW, ProcessStep.COMPLETION],
				rules=[BusinessRule(name='cv_required', description='CV file must be provided for analysis', condition="'cv' in user_input.lower() and not has_cv_context", action='request_cv_upload', priority=3), BusinessRule(name='privacy_protection', description='Protect user privacy in CV analysis', condition='contains_personal_info', action='sanitize_response', priority=5)],
				required_tools=['get_cv_profile', 'rag_retrieval', 'generate_survey_questions'],
				escalation_conditions=['analysis_confidence < 0.7', 'user_requests_human_review'],
				completion_criteria=['cv_analyzed', 'feedback_provided', 'user_satisfied'],
			),
			BusinessProcessType.SURVEY_GENERATION: ProcessDefinition(
				process_type=BusinessProcessType.SURVEY_GENERATION,
				name='Survey Generation Process',
				description='Process for generating intelligent surveys via N8N integration',
				steps=[ProcessStep.INTAKE, ProcessStep.VALIDATION, ProcessStep.PROCESSING, ProcessStep.COMPLETION],
				rules=[BusinessRule(name='authorization_required', description='Valid authorization token required for N8N API', condition='not has_valid_auth_token', action='request_authentication', priority=5), BusinessRule(name='survey_context_validation', description='Ensure sufficient context for survey generation', condition='insufficient_context_for_survey', action='gather_more_context', priority=3)],
				required_tools=['generate_survey_questions'],
				escalation_conditions=['n8n_api_unavailable', 'repeated_survey_failures'],
				completion_criteria=['survey_generated', 'websocket_delivered', 'user_acknowledged'],
			),
			BusinessProcessType.CAREER_GUIDANCE: ProcessDefinition(
				process_type=BusinessProcessType.CAREER_GUIDANCE,
				name='Career Guidance Process',
				description='Process for providing comprehensive career guidance',
				steps=[ProcessStep.INTAKE, ProcessStep.PROCESSING, ProcessStep.REVIEW, ProcessStep.COMPLETION],
				rules=[BusinessRule(name='profile_completeness', description='Ensure user profile is complete enough for guidance', condition='profile_completeness < 0.6', action='request_profile_completion', priority=4), BusinessRule(name='evidence_based_advice', description='Provide evidence-based career advice', condition='advice_without_evidence', action='include_supporting_data', priority=3)],
				required_tools=['rag_retrieval', 'generate_survey_questions'],
				escalation_conditions=['complex_career_transition', 'user_requires_professional_counselor'],
				completion_criteria=['guidance_provided', 'actionable_steps_given', 'user_understanding_confirmed'],
			),
		}

	def identify_process_type(self, user_input: str, context: Dict[str, Any]) -> BusinessProcessType:
		"""Identify the appropriate business process for user input"""
		user_input_lower = user_input.lower()

		# Priority-based detection
		if any(keyword in user_input_lower for keyword in ['survey', 'question', 'questionnaire', 'form']):
			return BusinessProcessType.SURVEY_GENERATION

		if any(keyword in user_input_lower for keyword in ['cv', 'resume', 'curriculum']):
			return BusinessProcessType.CV_ANALYSIS

		if any(keyword in user_input_lower for keyword in ['career', 'job', 'work', 'professional', 'interview']):
			return BusinessProcessType.CAREER_GUIDANCE

		if any(keyword in user_input_lower for keyword in ['help', 'support', 'problem', 'issue']):
			return BusinessProcessType.CUSTOMER_SUPPORT

		return BusinessProcessType.GENERAL_CONVERSATION

	def get_process_definition(self, process_type: BusinessProcessType) -> Optional[ProcessDefinition]:
		"""Get process definition by type"""
		return self.processes.get(process_type)

	def evaluate_rules(self, process_type: BusinessProcessType, context: Dict[str, Any]) -> List[BusinessRule]:
		"""Evaluate business rules for a process and return triggered rules"""
		process_def = self.get_process_definition(process_type)
		if not process_def:
			return []

		triggered_rules = []
		for rule in process_def.rules:
			if not rule.enabled:
				continue

			try:
				# Simple condition evaluation (in production, use safer evaluation)
				if self._evaluate_condition(rule.condition, context):
					triggered_rules.append(rule)
			except Exception as e:
				logger.warning(f'Failed to evaluate rule {rule.name}: {e}')

		# Sort by priority (higher priority first)
		return sorted(triggered_rules, key=lambda r: r.priority, reverse=True)

	def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
		"""Safely evaluate rule condition"""
		# Simple keyword-based evaluation for demo
		# In production, use ast.literal_eval or a proper rule engine

		if condition == "'cv' in user_input.lower() and not has_cv_context":
			user_input = context.get('user_input', '').lower()
			has_cv_context = context.get('has_cv_context', False)
			return 'cv' in user_input and not has_cv_context

		if condition == 'not has_valid_auth_token':
			return not context.get('has_valid_auth_token', False)

		if condition == 'insufficient_context_for_survey':
			context_score = context.get('context_completeness', 1.0)
			return context_score < 0.5

		if condition == 'profile_completeness < 0.6':
			completeness = context.get('profile_completeness', 1.0)
			return completeness < 0.6

		return False

	def get_required_tools(self, process_type: BusinessProcessType) -> List[str]:
		"""Get required tools for a business process"""
		process_def = self.get_process_definition(process_type)
		return process_def.required_tools if process_def else []

	def should_escalate(self, process_type: BusinessProcessType, context: Dict[str, Any]) -> bool:
		"""Check if process should be escalated"""
		process_def = self.get_process_definition(process_type)
		if not process_def:
			return False

		for condition in process_def.escalation_conditions:
			if self._evaluate_escalation_condition(condition, context):
				return True
		return False

	def _evaluate_escalation_condition(self, condition: str, context: Dict[str, Any]) -> bool:
		"""Evaluate escalation condition"""
		if condition == 'analysis_confidence < 0.7':
			return context.get('analysis_confidence', 1.0) < 0.7
		if condition == 'n8n_api_unavailable':
			return context.get('n8n_api_error', False)
		if condition == 'repeated_survey_failures':
			return context.get('survey_failure_count', 0) > 2
		return False


# Global business process manager instance
business_process_manager = BusinessProcessManager()


def get_business_process_manager() -> BusinessProcessManager:
	"""Get the global business process manager instance"""
	return business_process_manager
