"""
Question Generation Workflow using LangGraph.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.modules.question_composer.workflows.question_generation.state.workflow_state import (
	QuestionGenerationState,
)
from app.modules.question_composer.workflows.question_generation.config.workflow_config import (
	QuestionGenerationWorkflowConfig,
)
from app.modules.question_composer.workflows.question_generation.config.prompts import (
	QUESTION_GENERATION_SYSTEM_PROMPT,
	ANALYSIS_SYSTEM_PROMPT,
	ROUTER_PROMPT,
)
from app.modules.question_composer.schemas.question_schemas import (
	Question,
	UserProfile,
	AnalysisDecision,
	QuestionGenerationResponse,
)

logger = logging.getLogger(__name__)


class QuestionGenerationWorkflow:
	"""
	LangGraph workflow để tạo câu hỏi khảo sát thông minh.

	Workflow bao gồm:
	1. Analyze User Info - Phân tích thông tin người dùng hiện có
	2. Generate Questions - Tạo 4 câu hỏi mới
	3. Router - Quyết định tiếp tục hay dừng lại
	"""

	def __init__(self, config: Optional[QuestionGenerationWorkflowConfig] = None):
		self.config = config or QuestionGenerationWorkflowConfig.from_env()
		self.llm = ChatGoogleGenerativeAI(
			model=self.config.model_name,
			temperature=self.config.temperature,
			max_tokens=self.config.max_tokens,
		)

		# Setup parsers
		self.question_parser = PydanticOutputParser(pydantic_object=QuestionGenerationResponse)
		self.analysis_parser = PydanticOutputParser(pydantic_object=AnalysisDecision)

		# Build workflow
		self.workflow = self._build_workflow()
		self.checkpointer = MemorySaver()
		self.compiled_workflow = self.workflow.compile(checkpointer=self.checkpointer)

		logger.info('QuestionGenerationWorkflow initialized successfully')

	def _build_workflow(self) -> StateGraph:
		"""Build the LangGraph workflow"""
		workflow = StateGraph(QuestionGenerationState)

		# Add nodes
		workflow.add_node('analyze_user_info', self._analyze_user_info)
		workflow.add_node('generate_questions', self._generate_questions)
		workflow.add_node('router', self._router)

		# Add edges
		workflow.set_entry_point('analyze_user_info')
		workflow.add_edge('analyze_user_info', 'router')
		workflow.add_edge('generate_questions', 'analyze_user_info')

		# Conditional routing
		workflow.add_conditional_edges(
			'router',
			self._should_continue,
			{'continue': 'generate_questions', 'end': END},
		)

		return workflow

	async def _analyze_user_info(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Phân tích thông tin người dùng và quyết định có cần thêm câu hỏi không"""
		logger.info(f'Analyzing user info - Iteration {state["current_iteration"]}')

		try:
			# Prepare analysis prompt
			analysis_prompt = ChatPromptTemplate.from_messages([
				('system', ANALYSIS_SYSTEM_PROMPT),
				(
					'user',
					"""
Phân tích thông tin người dùng hiện có:

THÔNG TIN NGƯỜI DÙNG:
{user_data}

CÁC CÂU HỎI ĐÃ HỎI:
{previous_questions}

Hãy đánh giá mức độ đầy đủ thông tin và quyết định có cần hỏi thêm không.

{format_instructions}
""",
				),
			])

			# Format previous questions
			previous_q_text = '\n'.join([f'- {q.Question} ({q.Question_type})' for q in state['all_previous_questions']]) if state['all_previous_questions'] else 'Chưa có câu hỏi nào'

			# Run analysis
			chain = analysis_prompt | self.llm | self.analysis_parser
			analysis_result = await chain.ainvoke({
				'user_data': state['user_profile'].model_dump(),
				'previous_questions': previous_q_text,
				'format_instructions': self.analysis_parser.get_format_instructions(),
			})

			logger.info(f'Analysis completed - Decision: {analysis_result.decision}, Score: {analysis_result.completeness_score}')

			return {
				'analysis_decision': analysis_result,
				'completeness_score': analysis_result.completeness_score,
				'missing_areas': analysis_result.missing_areas,
				'focus_areas': analysis_result.suggested_focus,
				'should_continue': analysis_result.decision == 'need_more_info' and state['current_iteration'] < state['max_iterations'],
			}

		except Exception as e:
			logger.error(f'Error in analyze_user_info: {str(e)}')
			return {
				'analysis_decision': AnalysisDecision(
					decision='need_more_info',
					missing_areas=['general_info'],
					reasoning=f'Analysis failed: {str(e)}',
					completeness_score=0.0,
					suggested_focus=['skills', 'goals'],
				),
				'should_continue': False,
				'error_message': str(e),
			}

	async def _generate_questions(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Tạo 4 câu hỏi mới dựa trên phân tích"""
		logger.info(f'Generating questions - Focus areas: {state["focus_areas"]}')

		try:
			# Prepare generation prompt
			generation_prompt = ChatPromptTemplate.from_messages([
				('system', QUESTION_GENERATION_SYSTEM_PROMPT),
				(
					'user',
					"""
Tạo 4 câu hỏi mới để bổ sung thông tin người dùng:

THÔNG TIN HIỆN TẠI:
{user_data}

CÁC LĨNH VỰC CẦN TẬP TRUNG:
{focus_areas}

CÁC CÂU HỎI ĐÃ HỎI (tránh lặp lại):
{previous_questions}

YÊU CẦU:
- Tạo đúng 4 câu hỏi: 1 single_option, 1 multiple_choice, 1 text_input, 1 sub_form
- Tập trung vào các lĩnh vực: {focus_areas}
- Không lặp lại nội dung đã hỏi
- Sử dụng tiếng Việt tự nhiên

{format_instructions}
""",
				),
			])

			# Format data
			previous_q_text = '\n'.join([f'- {q.Question}' for q in state['all_previous_questions']]) if state['all_previous_questions'] else 'Chưa có'

			focus_text = ', '.join(state['focus_areas']) if state['focus_areas'] else 'Thông tin tổng quát'

			# Run generation
			chain = generation_prompt | self.llm | self.question_parser
			result = await chain.ainvoke({
				'user_data': state['user_profile'].model_dump(),
				'focus_areas': focus_text,
				'previous_questions': previous_q_text,
				'format_instructions': self.question_parser.get_format_instructions(),
			})

			# Update state
			new_questions = result.questions
			logger.info(f'Generated {len(new_questions)} questions')

			# Create generation history entry
			history_entry = {
				'iteration': state['current_iteration'],
				'focus_areas': state['focus_areas'],
				'questions_generated': [q.model_dump() for q in new_questions],
				'completeness_before': state['completeness_score'],
			}

			return {
				'generated_questions': new_questions,
				'all_previous_questions': state['all_previous_questions'] + new_questions,
				'current_iteration': state['current_iteration'] + 1,
				'total_questions_generated': state['total_questions_generated'] + len(new_questions),
				'generation_history': state['generation_history'] + [history_entry],
			}

		except Exception as e:
			logger.error(f'Error in generate_questions: {str(e)}')
			return {'error_message': str(e), 'should_continue': False}

	async def _router(self, state: QuestionGenerationState) -> Dict[str, Any]:
		"""Router node - quyết định tiếp tục hay dừng"""
		decision = state.get('analysis_decision')
		current_iteration = state.get('current_iteration', 0)
		max_iterations = state.get('max_iterations', 5)

		if not decision:
			return {'should_continue': False, 'workflow_complete': True}

		should_continue = decision.decision == 'need_more_info' and current_iteration < max_iterations and not state.get('error_message')

		logger.info(f'Router decision - Continue: {should_continue}, Iteration: {current_iteration}/{max_iterations}')

		return {
			'should_continue': should_continue,
			'workflow_complete': not should_continue,
		}

	def _should_continue(self, state: QuestionGenerationState) -> str:
		"""Conditional routing logic"""
		return 'continue' if state.get('should_continue', False) else 'end'

	async def generate_questions(
		self,
		user_profile: Optional[UserProfile] = None,
		existing_questions: Optional[List[Question]] = None,
		session_id: Optional[str] = None,
	) -> QuestionGenerationResponse:
		"""
		Main method để generate questions
		"""
		logger.info('Starting question generation workflow')

		# Prepare initial state
		initial_state: QuestionGenerationState = {
			'user_profile': user_profile or UserProfile(),
			'existing_user_data': user_profile.model_dump() if user_profile else {},
			'generated_questions': [],
			'all_previous_questions': existing_questions or [],
			'current_iteration': 0,
			'max_iterations': self.config.max_iterations,
			'analysis_decision': None,
			'completeness_score': 0.0,
			'missing_areas': [],
			'focus_areas': [],
			'should_continue': True,
			'workflow_complete': False,
			'error_message': None,
			'generation_history': [],
			'total_questions_generated': 0,
			'session_id': session_id,
		}

		# Run workflow
		config = {'configurable': {'thread_id': session_id or 'default'}}
		final_state = await self.compiled_workflow.ainvoke(initial_state, config=config)

		# Extract result
		return QuestionGenerationResponse(
			questions=final_state.get('generated_questions', []),
			analysis=final_state.get('analysis_decision', {}).reasoning,
			next_focus_areas=final_state.get('focus_areas', []),
			completeness_score=final_state.get('completeness_score', 0.0),
			should_continue=final_state.get('should_continue', False),
		)

	async def analyze_user_completeness(self, user_profile: UserProfile, previous_questions: List[Question] = None) -> Dict[str, Any]:
		"""
		Analyze user profile completeness without generating new questions.
		"""
		try:
			# Prepare analysis prompt
			analysis_prompt = ChatPromptTemplate.from_messages([
				('system', ANALYSIS_SYSTEM_PROMPT),
				(
					'user',
					"""
Phân tích thông tin người dùng hiện có:

THÔNG TIN NGƯỜI DÙNG:
{user_data}

CÁC CÂU HỎI ĐÃ HỎI:
{previous_questions}

Hãy đánh giá mức độ đầy đủ thông tin.

{format_instructions}
""",
				),
			])

			# Format previous questions
			previous_q_text = '\n'.join([f'- {q.Question} ({q.Question_type})' for q in (previous_questions or [])]) if previous_questions else 'Chưa có câu hỏi nào'

			# Run analysis
			chain = analysis_prompt | self.llm | self.analysis_parser
			analysis_result = await chain.ainvoke({
				'user_data': user_profile.model_dump(),
				'previous_questions': previous_q_text,
				'format_instructions': self.analysis_parser.get_format_instructions(),
			})

			return {
				'completeness_score': analysis_result.completeness_score,
				'missing_areas': analysis_result.missing_areas,
				'analysis': analysis_result.reasoning,
				'should_continue': analysis_result.decision == 'need_more_info',
			}

		except Exception as e:
			logger.error(f'Error analyzing user completeness: {str(e)}')
			return {
				'completeness_score': 0.0,
				'missing_areas': ['general_info'],
				'analysis': f'Analysis failed: {str(e)}',
				'should_continue': True,
			}

	def get_workflow_info(self) -> Dict[str, Any]:
		"""Get workflow information"""
		return {
			'name': 'Question Generation Workflow',
			'version': '1.0.0',
			'config': self.config.to_dict(),
			'nodes': ['analyze_user_info', 'generate_questions', 'router'],
			'max_iterations': self.config.max_iterations,
			'question_types': [
				'single_option',
				'multiple_choice',
				'text_input',
				'sub_form',
			],
		}


# Factory function
def create_question_generation_workflow(
	config: Optional[QuestionGenerationWorkflowConfig] = None,
) -> QuestionGenerationWorkflow:
	"""Create question generation workflow instance"""
	return QuestionGenerationWorkflow(config)


logger.info('Question Generation Workflow module loaded!')
