"""
Question Composer Tool for Chat Agent - Simplified Function-based Implementation
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.modules.question_composer.repository.question_composer_repo import (
	QuestionComposerRepo,
)
from app.modules.question_composer.schemas.question_request import (
	QuestionGenerationRequest,
	AnalyzeUserProfileRequest,
)
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


class QuestionComposerInput(BaseModel):
	"""Input schema for Question Composer tool"""

	action: str = Field(description="'generate' hoặc 'analyze'")
	user_id: Optional[str] = Field(None, description='ID của user')
	session_id: Optional[str] = Field(None, description='Session ID')
	existing_user_data: Dict[str, Any] = Field(default_factory=dict, description='Dữ liệu user hiện tại')
	previous_questions: List[Dict[str, Any]] = Field(default_factory=list, description='Câu hỏi đã hỏi')
	focus_areas: List[str] = Field(default_factory=list, description='Khu vực tập trung')
	max_questions: int = Field(4, description='Số câu hỏi tối đa')
	max_iterations: int = Field(5, description='Số iteration tối đa')


@tool('question_composer', args_schema=QuestionComposerInput)
def question_composer_tool(
	action: str,
	user_id: Optional[str] = None,
	session_id: Optional[str] = None,
	existing_user_data: Dict[str, Any] = None,
	previous_questions: List[Dict[str, Any]] = None,
	focus_areas: List[str] = None,
	max_questions: int = 4,
	max_iterations: int = 5,
) -> str:
	"""
	❓ QUESTION COMPOSER TOOL - BẮT BUỘC cho CV, profile, câu hỏi!

	📋 ƯU TIÊN SỬ DỤNG TOOL NÀY KHI:
	✅ User đề cập đến "CV", "profile", "resume", "hồ sơ"
	✅ User hỏi về "compose questions", "tạo câu hỏi"
	✅ User muốn "analyze", "phân tích" profile/CV
	✅ User cần "interview questions", "câu hỏi phỏng vấn"
	✅ User hỏi về "career development", "phát triển sự nghiệp"
	✅ User upload CV hoặc nói về kinh nghiệm làm việc
	✅ User muốn "cải thiện CV", "hoàn thiện profile"
	✅ User hỏi về "skills assessment", "đánh giá kỹ năng"

	⚠️ LUÔN SỬ DỤNG tool này cho mọi chủ đề liên quan CV/profile!

	🛠️ HAI CHỨC NĂNG CHÍNH:
	1️⃣ ANALYZE (action="analyze"): Phân tích độ hoàn thiện profile
	2️⃣ GENERATE (action="generate"): Tạo câu hỏi thông minh

	Args:
	    action: "analyze" hoặc "generate" (BẮT BUỘC)
	    user_id: ID người dùng (optional)
	    session_id: ID session (optional)
	    existing_user_data: Dict thông tin user hiện có
	    previous_questions: List câu hỏi đã hỏi
	    focus_areas: List khu vực focus (optional)
	    max_questions: Số câu hỏi tối đa (default: 4)
	    max_iterations: Số iteration tối đa (default: 5)

	Returns:
	    JSON string với kết quả analysis hoặc questions
	"""
	print(f'🎯 [QuestionComposer] Tool called with action: {action}')

	try:
		# Normalize inputs
		existing_user_data = existing_user_data or {}
		previous_questions = previous_questions or []
		focus_areas = focus_areas or []

		print(f'📊 [QuestionComposer] Processing - User: {user_id}, Session: {session_id}')
		print(f'📋 [QuestionComposer] Data keys: {list(existing_user_data.keys())}')
		print(f'❓ [QuestionComposer] Previous questions: {len(previous_questions)}')

		# Execute action using asyncio
		if action == 'analyze':
			result = asyncio.run(_analyze_profile_async(existing_user_data, previous_questions))
		elif action == 'generate':
			result = asyncio.run(
				_generate_questions_async(
					user_id,
					session_id,
					existing_user_data,
					previous_questions,
					focus_areas,
					max_questions,
					max_iterations,
				)
			)
		else:
			raise ValidationException(f"Invalid action: {action}. Use 'generate' or 'analyze'")

		print(f'✅ [QuestionComposer] Tool execution completed successfully')
		return result

	except Exception as e:
		print(f'💥 [QuestionComposer] Error: {str(e)}')
		error_data = {
			'status': 'error',
			'type': f'question_{action}',
			'error': str(e),
		}
		return json.dumps(error_data, ensure_ascii=False)


async def _analyze_profile_async(existing_user_data: Dict[str, Any], previous_questions: List[Dict[str, Any]]) -> str:
	"""Async profile analysis"""
	print(f'🔍 [QuestionComposer] Starting profile analysis')

	if not existing_user_data:
		return json.dumps(
			{
				'status': 'error',
				'type': 'profile_analysis',
				'error': 'No user data provided for analysis',
			},
			ensure_ascii=False,
		)

	try:
		# Get DB session from global context (needs to be passed somehow)
		# For now, we'll create a mock response
		# TODO: Need to pass db_session properly

		result_data = {
			'status': 'success',
			'type': 'profile_analysis',
			'analysis': {
				'completeness_score': 0.7,  # Mock score
				'should_continue': True,
				'missing_areas': ['skills', 'experience_details'],
				'suggested_focus': ['technical_skills', 'work_experience'],
				'analysis_text': 'Profile cần bổ sung thêm thông tin về kỹ năng và kinh nghiệm chi tiết.',
			},
			'recommendations': {
				'should_ask_more': True,
				'priority_areas': ['technical_skills', 'work_experience'],
				'summary': 'Nên hỏi thêm để có profile hoàn thiện hơn.',
			},
		}

		print(f'✅ [QuestionComposer] Analysis completed')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Analysis error: {str(e)}')
		raise e


async def _generate_questions_async(
	user_id: Optional[str],
	session_id: Optional[str],
	existing_user_data: Dict[str, Any],
	previous_questions: List[Dict[str, Any]],
	focus_areas: List[str],
	max_questions: int,
	max_iterations: int,
) -> str:
	"""Async question generation"""
	print(f'🎨 [QuestionComposer] Starting question generation')

	try:
		# Mock question generation
		# TODO: Use actual QuestionComposerRepo when db_session is available

		mock_questions = [
			{
				'id': 'q_1',
				'question': 'Bạn có kinh nghiệm làm việc với công nghệ nào?',
				'type': 'multiple_choice',
				'data': {'options': ['Python', 'JavaScript', 'Java', 'C++', 'Khác']},
				'required': True,
				'order': 1,
			},
			{
				'id': 'q_2',
				'question': 'Mô tả dự án ấn tượng nhất bạn đã thực hiện?',
				'type': 'text_input',
				'required': True,
				'order': 2,
			},
		]

		result_data = {
			'status': 'success',
			'type': 'question_generation',
			'session_info': {
				'session_id': session_id or f'session_{user_id}',
				'current_iteration': 1,
				'total_questions_generated': len(mock_questions),
			},
			'analysis': {
				'completeness_score': 0.6,
				'should_continue': True,
				'next_focus_areas': focus_areas or ['skills', 'experience'],
				'analysis_text': 'Profile cần thêm thông tin để hoàn thiện.',
			},
			'questions': mock_questions,
		}

		print(f'✅ [QuestionComposer] Generated {len(mock_questions)} questions')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Generation error: {str(e)}')
		raise e


def get_question_composer_tool(db_session: Session):
	"""Factory function để tạo question composer tool với db_session"""
	print(f'🏭 [Factory] Creating simplified question composer tool')

	# Store db_session in global context or closure
	# For a more robust solution, you could use a closure or global variable
	global _global_db_session
	_global_db_session = db_session

	print(f'✅ [Factory] Question composer tool created')
	return question_composer_tool


# Global variable to store db_session (not ideal but simple)
_global_db_session = None
