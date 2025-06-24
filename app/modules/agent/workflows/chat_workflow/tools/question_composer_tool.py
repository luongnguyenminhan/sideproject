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
from datetime import datetime

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
	existing_user_data: Optional[Dict[str, Any]] = Field(None, description='Dữ liệu user hiện tại')
	previous_questions: Optional[List[Dict[str, Any]]] = Field(None, description='Câu hỏi đã hỏi')
	focus_areas: Optional[List[str]] = Field(None, description='Khu vực tập trung')
	max_questions: int = Field(4, description='Số câu hỏi tối đa')
	max_iterations: int = Field(5, description='Số iteration tối đa')


@tool('question_composer', args_schema=QuestionComposerInput, return_direct=False)
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
			print(f'📈 [QuestionComposer] Generated {json.loads(result)} questions')
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
	"""Real profile analysis using QuestionComposerRepo"""
	print(f'🔍 [QuestionComposer] Starting REAL profile analysis')

	# Input validation
	if not existing_user_data:
		return json.dumps(
			{
				'status': 'error',
				'type': 'profile_analysis',
				'error': 'No user data provided for analysis',
				'suggestion': 'Please provide user profile data to analyze',
			},
			ensure_ascii=False,
		)

	try:
		# Import the real components
		from app.modules.question_composer.repository.question_composer_repo import (
			QuestionComposerRepo,
		)
		from app.modules.question_composer.schemas.question_request import (
			AnalyzeUserProfileRequest,
		)
		from app.core.database import get_db

		# Get database session
		db_session = None
		try:
			db_session = next(get_db())
			print(f'✅ [QuestionComposer] Database session acquired')
		except Exception as db_e:
			print(f'⚠️ [QuestionComposer] Database session failed, using fallback: {str(db_e)}')
			# Fallback to mock analysis if DB not available
			return await _fallback_analysis(existing_user_data, previous_questions)

		# Create repository instance
		repo = QuestionComposerRepo(db_session)
		print(f'✅ [QuestionComposer] Repository instance created')

		# Prepare request
		analyze_request = AnalyzeUserProfileRequest(user_profile=existing_user_data, previous_questions=previous_questions or [])
		print(f'📋 [QuestionComposer] Analysis request prepared with {len(existing_user_data)} data fields')

		# Call real analysis
		print(f'🚀 [QuestionComposer] Calling real analysis service')
		analysis_response = await repo.analyze_user_profile(analyze_request)
		print(f'✅ [QuestionComposer] Analysis completed successfully')
		print(f'🔍 [QuestionComposer] Response type: {type(analysis_response).__name__}')
		print(f'🔍 [QuestionComposer] Response attributes: {dir(analysis_response)}')

		# Convert response to tool format - Use safe serialization
		missing_areas = _safe_serialize_object(analysis_response.missing_areas, [])
		suggested_focus = _safe_serialize_object(analysis_response.suggested_focus, [])
		next_steps = _safe_serialize_object(getattr(analysis_response, 'next_steps', 'Continue with profile completion'), 'Continue with profile completion')
		summary = _safe_serialize_object(getattr(analysis_response, 'summary', 'Profile analysis completed'), 'Profile analysis completed')
		print(f'🔍 [QuestionComposer] Serialized analysis data')

		result_data = {
			'status': 'success',
			'type': 'profile_analysis',
			'analysis': {
				'completeness_score': round(float(_safe_serialize_object(analysis_response.completeness_score, 0.5)), 2),
				'should_continue': bool(_safe_serialize_object(analysis_response.should_continue, True)),
				'missing_areas': missing_areas,
				'suggested_focus': suggested_focus,
				'data_quality': _safe_serialize_object(getattr(analysis_response, 'data_quality', 'good'), 'good'),
				'questions_analyzed': (len(previous_questions) if previous_questions else 0),
				'analysis_text': _safe_serialize_object(getattr(analysis_response, 'analysis_text', 'Analysis completed'), 'Analysis completed'),
			},
			'recommendations': {
				'should_ask_more': bool(_safe_serialize_object(analysis_response.should_continue, True)),
				'priority_areas': suggested_focus,
				'next_steps': next_steps,
				'summary': summary,
			},
			'metadata': {
				'analysis_timestamp': datetime.now().isoformat(),
				'data_keys_found': list(existing_user_data.keys()),
				'total_data_points': len(existing_user_data),
				'service_used': 'real_question_composer_repo',
				'response_type': str(type(analysis_response).__name__),
			},
		}

		print(f'✅ [QuestionComposer] Real analysis completed with score: {analysis_response.completeness_score:.2f}')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Real analysis error: {str(e)}')
		print(f'🔄 [QuestionComposer] Falling back to mock analysis')
		# Fallback to mock if real analysis fails
		return await _fallback_analysis(existing_user_data, previous_questions)
	finally:
		if db_session:
			db_session.close()
			print(f'🔒 [QuestionComposer] Database session closed')


async def _generate_questions_async(
	user_id: Optional[str],
	session_id: Optional[str],
	existing_user_data: Dict[str, Any],
	previous_questions: List[Dict[str, Any]],
	focus_areas: List[str],
	max_questions: int,
	max_iterations: int,
) -> str:
	"""Real question generation using QuestionComposerRepo"""
	print(f'🎨 [QuestionComposer] Starting REAL question generation')

	try:
		# Import the real components
		from app.modules.question_composer.repository.question_composer_repo import (
			QuestionComposerRepo,
		)
		from app.modules.question_composer.schemas.question_request import (
			QuestionGenerationRequest,
		)
		from app.core.database import get_db

		# Get database session
		db_session = None
		try:
			db_session = next(get_db())
			print(f'✅ [QuestionComposer] Database session acquired')
		except Exception as db_e:
			print(f'⚠️ [QuestionComposer] Database session failed, using fallback: {str(db_e)}')
			# Fallback to mock generation if DB not available
			return await _fallback_generation(
				user_id,
				session_id,
				existing_user_data,
				previous_questions,
				focus_areas,
				max_questions,
			)

		# Create repository instance
		repo = QuestionComposerRepo(db_session)
		print(f'✅ [QuestionComposer] Repository instance created')

		# Prepare request
		generation_request = QuestionGenerationRequest(
			session_id=session_id,
			user_id=user_id,
			existing_user_data=existing_user_data,
			previous_questions=previous_questions or [],
			focus_areas=focus_areas or [],
			max_questions=max_questions,
			max_iterations=max_iterations,
		)
		print(f'📋 [QuestionComposer] Generation request prepared with {len(existing_user_data)} data fields')

		# Call real generation
		print(f'🚀 [QuestionComposer] Calling real generation service')
		generation_response = await repo.generate_questions(generation_request)
		print(f'✅ [QuestionComposer] Generation completed successfully')
		print(f'🔍 [QuestionComposer] Response type: {type(generation_response).__name__}')
		print(f'🔍 [QuestionComposer] Response attributes: {dir(generation_response)}')

		# Convert response to tool format - Use safe serialization
		serialized_questions = _safe_serialize_list(generation_response.questions, [])
		next_focus_areas = _safe_serialize_object(generation_response.next_focus_areas, [])
		print(f'🔍 [QuestionComposer] Serialized {len(serialized_questions)} questions')

		result_data = {
			'status': 'success',
			'type': 'question_generation',
			'session_info': {
				'session_id': _safe_serialize_object(generation_response.session_id, session_id),
				'current_iteration': _safe_serialize_object(getattr(generation_response, 'current_iteration', 1), 1),
				'total_questions_generated': _safe_serialize_object(getattr(generation_response, 'total_questions_generated', len(serialized_questions)), len(serialized_questions)),
			},
			'analysis': {
				'completeness_score': round(float(_safe_serialize_object(generation_response.completeness_score, 0.5)), 2),
				'should_continue': bool(_safe_serialize_object(generation_response.should_continue, True)),
				'next_focus_areas': next_focus_areas,
				'analysis_text': _safe_serialize_object(getattr(generation_response, 'analysis', 'Analysis completed'), 'Analysis completed'),
			},
			'questions': serialized_questions,
			'metadata': {
				'generation_timestamp': datetime.now().isoformat(),
				'service_used': 'real_question_composer_repo',
				'focus_areas_requested': focus_areas,
				'response_type': str(type(generation_response).__name__),
			},
		}

		print(f'✅ [QuestionComposer] Real generation completed with {len(generation_response.questions)} questions')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Real generation error: {str(e)}')
		print(f'🔄 [QuestionComposer] Falling back to mock generation')
		# Fallback to mock if real generation fails
		return await _fallback_generation(
			user_id,
			session_id,
			existing_user_data,
			previous_questions,
			focus_areas,
			max_questions,
		)
	finally:
		if db_session:
			db_session.close()
			print(f'🔒 [QuestionComposer] Database session closed')


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


async def _fallback_analysis(existing_user_data: Dict[str, Any], previous_questions: List[Dict[str, Any]]) -> str:
	"""Fallback mock analysis when real service fails"""
	print(f'🔄 [QuestionComposer] Running fallback analysis')

	try:
		# Basic analysis logic
		data_keys = list(existing_user_data.keys())
		data_quality_score = min(1.0, len(data_keys) / 10)  # Normalize by 10 expected fields

		# Analyze previous questions
		questions_asked = len(previous_questions) if previous_questions else 0
		questions_impact = min(0.3, questions_asked * 0.05)  # Each question adds 5% up to 30%

		# Calculate overall completeness
		completeness_score = (data_quality_score * 0.7) + questions_impact

		# Determine missing areas based on common profile fields
		expected_areas = [
			'personal_info',
			'education',
			'experience',
			'skills',
			'goals',
			'preferences',
		]
		missing_areas = [area for area in expected_areas if area not in data_keys]

		# Create intelligent recommendations
		should_continue = completeness_score < 0.8 or len(missing_areas) > 0

		result_data = {
			'status': 'success',
			'type': 'profile_analysis',
			'analysis': {
				'completeness_score': round(completeness_score, 2),
				'should_continue': should_continue,
				'missing_areas': missing_areas,
				'suggested_focus': missing_areas[:3],  # Top 3 priorities
				'data_quality': ('good' if data_quality_score > 0.6 else 'needs_improvement'),
				'questions_analyzed': questions_asked,
				'analysis_text': (f'Profile hiện tại có điểm hoàn thiện {round(completeness_score * 100)}%. ' + f'Cần bổ sung thêm thông tin về: {", ".join(missing_areas[:3])}.' if missing_areas else 'Profile đã khá hoàn thiện.'),
			},
			'recommendations': {
				'should_ask_more': should_continue,
				'priority_areas': missing_areas[:3] if missing_areas else [],
				'next_steps': ('Tạo câu hỏi để hoàn thiện profile' if should_continue else 'Profile đã đủ thông tin'),
				'summary': (f'Cần hỏi thêm {3 - len(data_keys)} câu hỏi để có profile hoàn thiện.' if should_continue else 'Profile đã hoàn thiện.'),
			},
			'metadata': {
				'analysis_timestamp': datetime.now().isoformat(),
				'data_keys_found': data_keys,
				'total_data_points': len(data_keys),
				'service_used': 'fallback_mock_analysis',
			},
		}

		print(f'✅ [QuestionComposer] Fallback analysis completed with score: {completeness_score:.2f}')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Fallback analysis error: {str(e)}')
		error_result = {
			'status': 'error',
			'type': 'profile_analysis',
			'error': str(e),
			'fallback_recommendation': {
				'should_continue': True,
				'suggested_action': 'Continue with general questions',
			},
		}
		return json.dumps(error_result, ensure_ascii=False)


async def _fallback_generation(
	user_id: Optional[str],
	session_id: Optional[str],
	existing_user_data: Dict[str, Any],
	previous_questions: List[Dict[str, Any]],
	focus_areas: List[str],
	max_questions: int,
) -> str:
	"""Fallback mock generation when real service fails"""
	print(f'🔄 [QuestionComposer] Running fallback generation')

	try:
		# Generate mock questions based on focus areas
		mock_questions = []

		# Base questions if no focus areas
		if not focus_areas:
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
				{
					'id': 'q_3',
					'question': 'Bạn muốn phát triển sự nghiệp theo hướng nào?',
					'type': 'single_option',
					'data': {
						'options': [
							'Technical Leader',
							'Manager',
							'Specialist',
							'Entrepreneur',
						]
					},
					'required': True,
					'order': 3,
				},
				{
					'id': 'q_4',
					'question': 'Thông tin thêm về học vấn và chứng chỉ',
					'type': 'sub_form',
					'data': {
						'fields': [
							{'name': 'degree', 'type': 'text', 'label': 'Bằng cấp'},
							{
								'name': 'university',
								'type': 'text',
								'label': 'Trường học',
							},
							{
								'name': 'year',
								'type': 'number',
								'label': 'Năm tốt nghiệp',
							},
						]
					},
					'required': False,
					'order': 4,
				},
			]
		else:
			# Generate questions based on focus areas
			for i, area in enumerate(focus_areas[:max_questions]):
				if area == 'skills':
					mock_questions.append({
						'id': f'q_{i + 1}',
						'question': f'Bạn có kỹ năng gì trong lĩnh vực {area}?',
						'type': 'multiple_choice',
						'data': {
							'options': [
								'Beginner',
								'Intermediate',
								'Advanced',
								'Expert',
							]
						},
						'required': True,
						'order': i + 1,
					})
				elif area == 'experience':
					mock_questions.append({
						'id': f'q_{i + 1}',
						'question': f'Kinh nghiệm của bạn trong {area} như thế nào?',
						'type': 'text_input',
						'required': True,
						'order': i + 1,
					})
				else:
					mock_questions.append({
						'id': f'q_{i + 1}',
						'question': f'Chia sẻ thông tin về {area} của bạn',
						'type': 'text_input',
						'required': True,
						'order': i + 1,
					})

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
			'metadata': {
				'generation_timestamp': datetime.now().isoformat(),
				'service_used': 'fallback_mock_generation',
				'focus_areas_requested': focus_areas,
			},
		}

		print(f'✅ [QuestionComposer] Fallback generation completed with {len(mock_questions)} questions')
		return json.dumps(result_data, ensure_ascii=False, indent=2)

	except Exception as e:
		print(f'💥 [QuestionComposer] Fallback generation error: {str(e)}')
		raise e


def _safe_serialize_object(obj, default_value=None):
	"""Safely serialize objects to JSON-compatible format"""
	try:
		if obj is None:
			return default_value

		# Handle Pydantic models
		if hasattr(obj, 'dict'):
			return obj.dict()

		# Handle dataclasses
		if hasattr(obj, '__dict__'):
			return obj.__dict__

		# Handle iterables (but not strings)
		if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
			return list(obj)

		# Handle basic types
		if isinstance(obj, (int, float, str, bool)):
			return obj

		# Convert to string as fallback
		return str(obj)

	except Exception as e:
		print(f'⚠️ [Serialization] Error serializing {type(obj)}: {str(e)}')
		return default_value or str(obj)


def _safe_serialize_list(obj_list, default_value=None):
	"""Safely serialize a list of objects"""
	if not obj_list:
		return default_value or []

	try:
		serialized_list = []
		for item in obj_list:
			serialized_item = _safe_serialize_object(item, {})
			serialized_list.append(serialized_item)
		return serialized_list
	except Exception as e:
		print(f'⚠️ [Serialization] Error serializing list: {str(e)}')
		return default_value or []


def test_serialization():
	"""Test serialization functions"""
	import json

	# Test with various objects
	test_cases = [
		{'name': 'dict', 'value': {'a': 1, 'b': 2}},
		{'name': 'list', 'value': [1, 2, 3]},
		{'name': 'string', 'value': 'test'},
		{'name': 'int', 'value': 42},
		{'name': 'float', 'value': 3.14},
		{'name': 'bool', 'value': True},
		{'name': 'none', 'value': None},
	]

	print('🧪 Testing serialization functions:')
	for case in test_cases:
		try:
			result = _safe_serialize_object(case['value'])
			json_str = json.dumps(result, ensure_ascii=False)
			print(f'✅ {case["name"]}: {result} -> JSON OK')
		except Exception as e:
			print(f'❌ {case["name"]}: {e}')


# Uncomment to run test
# test_serialization()
