"""
Question Composer Tool for Chat Agent
Tool để agent có thể tạo câu hỏi thông minh cho người dùng
"""

import logging
import json
from typing import Dict, Any, Optional, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from sqlalchemy.orm import Session

from app.modules.question_composer.repository.question_composer_repo import (
	QuestionComposerRepo,
)
from app.modules.question_composer.schemas.question_request import (
	QuestionGenerationRequest,
	AnalyzeUserProfileRequest,
)
from app.exceptions.exception import ValidationException, CustomHTTPException

logger = logging.getLogger(__name__)


class QuestionComposerInput(BaseModel):
	"""Input schema for Question Composer tool"""

	user_id: Optional[str] = Field(None, description='ID của user để track session')
	session_id: Optional[str] = Field(None, description='Session ID (nếu có), để continue session cũ')
	existing_user_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description='Dữ liệu user hiện tại (CV, profile, etc.)')
	previous_questions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description='Các câu hỏi đã hỏi trước đó')
	focus_areas: Optional[List[str]] = Field(default_factory=list, description='Các lĩnh vực cần tập trung hỏi')
	max_questions: int = Field(4, description='Số lượng câu hỏi tối đa tạo ra')
	max_iterations: int = Field(5, description='Số iteration tối đa của workflow')
	action: str = Field(
		'generate',
		description="Hành động: 'generate' để tạo câu hỏi, 'analyze' để phân tích profile",
	)


class QuestionComposerTool(BaseTool):
	"""Tool để agent tạo câu hỏi thông minh cho user"""

	name: str = 'question_composer'
	description: str = """
	TOOL BẮT BUỘC cho tất cả yêu cầu về CV, câu hỏi, profile analysis!
	
	SỬ DỤNG TOOL NÀY KHI:
	- User hỏi về "compose questions", "tạo câu hỏi"
	- User đề cập đến "CV", "profile", "resume" 
	- User muốn "analyze", "phân tích" profile
	- User cần "interview questions", "câu hỏi phỏng vấn"
	- User hỏi về "career development", "phát triển sự nghiệp"
	
	CHỨC NĂNG:
	1. Tạo câu hỏi thông minh dựa trên user profile
	2. Phân tích độ hoàn thiện của user profile  
	3. Đề xuất các lĩnh vực cần hỏi thêm
	4. Quản lý session để track quá trình hỏi đáp
	
	LOẠI CÂU HỎI:
	- multiple_choice: Câu hỏi trắc nghiệm
	- text_input: Câu hỏi nhập text tự do
	- combined_question: Câu hỏi kết hợp nhiều dạng
	- interview_flow: Câu hỏi phỏng vấn có logic
	
	INPUT TỐI THIỂU:
	- action: "generate" (tạo câu hỏi) hoặc "analyze" (phân tích)
	- existing_user_data: thông tin user hiện có (có thể là {})
	- max_questions: số câu hỏi tối đa (default: 4)
	
	OUTPUT FORMAT:
	- Trả về JSON format với đầy đủ thông tin câu hỏi
	- Mỗi lần gọi sẽ tạo ra nhiều câu hỏi cùng lúc
	- Frontend có thể parse JSON để hiển thị interactive questions
	
	⚠️ LƯU Ý: Tool này BẮT BUỘC phải được gọi khi user hỏi về CV/câu hỏi!
	"""

	db_session: Session = Field(exclude=True)
	_question_composer_repo: Any = PrivateAttr()

	def __init__(self, db_session: Session, **kwargs):
		print(f'🚀 [QuestionComposerTool] Initializing QuestionComposerTool with db_session')
		super().__init__(db_session=db_session, **kwargs)
		self._question_composer_repo = QuestionComposerRepo(db=db_session)
		print(f'✅ [QuestionComposerTool] QuestionComposerRepo initialized successfully')

	def _run(self, **kwargs) -> str:
		"""Sync run method"""
		print(f'🔄 [QuestionComposerTool] _run called with kwargs: {list(kwargs.keys())}')
		# Convert to async call
		import asyncio

		try:
			result = asyncio.run(self._arun(**kwargs))
			print(f'✅ [QuestionComposerTool] _run completed successfully')
			return result
		except Exception as e:
			print(f'💥 [QuestionComposerTool] Error in _run: {str(e)}')
			raise e

	async def _arun(self, **kwargs) -> str:
		"""Main async execution method"""
		print(f'🎯 [QuestionComposerTool] Starting _arun with kwargs: {kwargs}')

		try:
			# Parse input
			print(f'📝 [QuestionComposerTool] Parsing input parameters')
			input_data = QuestionComposerInput(**kwargs)
			print(f'✅ [QuestionComposerTool] Input parsed successfully')
			print(f'📊 [QuestionComposerTool] Action: {input_data.action}')
			print(f'👤 [QuestionComposerTool] User ID: {input_data.user_id}')
			print(f'🆔 [QuestionComposerTool] Session ID: {input_data.session_id}')
			print(f'📋 [QuestionComposerTool] Existing user data keys: {list(input_data.existing_user_data.keys())}')
			print(f'❓ [QuestionComposerTool] Previous questions count: {len(input_data.previous_questions)}')
			print(f'🎯 [QuestionComposerTool] Focus areas: {input_data.focus_areas}')
			print(f'🔢 [QuestionComposerTool] Max questions: {input_data.max_questions}')

			if input_data.action == 'analyze':
				print(f'🔍 [QuestionComposerTool] Executing profile analysis')
				result = await self._analyze_profile(input_data)
				print(f'✅ [QuestionComposerTool] Profile analysis completed')
			elif input_data.action == 'generate':
				print(f'🎨 [QuestionComposerTool] Executing question generation')
				result = await self._generate_questions(input_data)
				print(f'✅ [QuestionComposerTool] Question generation completed')
			else:
				print(f'❌ [QuestionComposerTool] Invalid action: {input_data.action}')
				raise ValidationException(f"Invalid action: {input_data.action}. Use 'generate' or 'analyze'")

			print(f'� [QuestionComposerTool] Tool execution completed successfully')
			return result

		except ValidationException as e:
			print(f'⚠️ [QuestionComposerTool] Validation error: {str(e)}')
			return f'❌ Validation Error: {str(e)}'
		except Exception as e:
			print(f'💥 [QuestionComposerTool] Unexpected error: {str(e)}')
			logger.error(f'Error in QuestionComposerTool: {str(e)}', exc_info=True)
			return f'❌ Error: {str(e)}'

	async def _generate_questions(self, input_data: QuestionComposerInput) -> str:
		"""Generate intelligent questions for user"""
		print(f'� [QuestionComposerTool] Starting question generation process')

		try:
			# Create request for question generation
			print(f'📝 [QuestionComposerTool] Creating QuestionGenerationRequest')
			request = QuestionGenerationRequest(
				session_id=input_data.session_id,
				user_id=input_data.user_id,
				existing_user_data=input_data.existing_user_data,
				previous_questions=input_data.previous_questions,
				focus_areas=input_data.focus_areas,
				max_questions=input_data.max_questions,
				max_iterations=input_data.max_iterations,
			)

			print(f'✅ [QuestionComposerTool] Request created successfully')
			print(f'📊 [QuestionComposerTool] Request details - User: {request.user_id}, Session: {request.session_id}')

			# Generate questions using repository
			print(f'🚀 [QuestionComposerTool] Calling _question_composer_repo.generate_questions')
			response = await self._question_composer_repo.generate_questions(request)
			print(f'✅ [QuestionComposerTool] Questions generated successfully')

			# Format response for agent
			print(f'🔄 [QuestionComposerTool] Formatting response for agent')
			result = self._format_generation_response(response)
			print(f'✅ [QuestionComposerTool] Response formatted successfully')
			print(f'📊 [QuestionComposerTool] Generated {len(response.questions)} questions')
			print(f'📈 [QuestionComposerTool] Completeness score: {response.completeness_score:.3f}')
			print(f'🔄 [QuestionComposerTool] Should continue: {response.should_continue}')

			return result

		except Exception as e:
			print(f'💥 [QuestionComposerTool] Error in question generation: {str(e)}')
			raise e

	async def _analyze_profile(self, input_data: QuestionComposerInput) -> str:
		"""Analyze user profile completeness"""
		print(f'🔍 [QuestionComposerTool] Starting profile analysis process')

		try:
			if not input_data.existing_user_data:
				print(f'⚠️ [QuestionComposerTool] No user data provided for analysis')
				return '❌ No user data provided for analysis. Please provide existing_user_data.'

			# Create request for profile analysis
			print(f'📝 [QuestionComposerTool] Creating AnalyzeUserProfileRequest')
			request = AnalyzeUserProfileRequest(
				user_profile=input_data.existing_user_data,
				previous_questions=input_data.previous_questions,
			)

			print(f'✅ [QuestionComposerTool] Analysis request created successfully')
			print(f'📊 [QuestionComposerTool] User profile data keys: {list(input_data.existing_user_data.keys())}')
			print(f'❓ [QuestionComposerTool] Previous questions count: {len(input_data.previous_questions)}')

			# Analyze profile using repository
			print(f'🚀 [QuestionComposerTool] Calling _question_composer_repo.analyze_user_profile')
			response = await self._question_composer_repo.analyze_user_profile(request)
			print(f'✅ [QuestionComposerTool] Profile analysis completed successfully')

			# Format response for agent
			print(f'🔄 [QuestionComposerTool] Formatting analysis response for agent')
			result = self._format_analysis_response(response)
			print(f'✅ [QuestionComposerTool] Analysis response formatted successfully')
			print(f'📈 [QuestionComposerTool] Completeness score: {response.completeness_score:.3f}')
			print(f'🎯 [QuestionComposerTool] Missing areas count: {len(response.missing_areas)}')
			print(f'🔄 [QuestionComposerTool] Should continue: {response.should_continue}')

			return result

		except Exception as e:
			print(f'💥 [QuestionComposerTool] Error in profile analysis: {str(e)}')
			raise e

	def _format_generation_response(self, response) -> str:
		"""Format question generation response for agent - Return JSON instead of formatted text"""
		print(f'🔄 [QuestionComposerTool] Formatting question generation response as JSON')

		try:
			# Convert response to JSON format
			result_data = {
				'status': 'success',
				'type': 'question_generation',
				'session_info': {
					'session_id': response.session_id,
					'current_iteration': response.current_iteration,
					'total_questions_generated': response.total_questions_generated,
				},
				'analysis': {
					'completeness_score': response.completeness_score,
					'should_continue': response.should_continue,
					'next_focus_areas': response.next_focus_areas,
					'analysis_text': response.analysis,
				},
				'questions': [],
			}

			# Process each question
			print(f'📝 [QuestionComposerTool] Processing {len(response.questions)} questions for JSON')
			for i, question in enumerate(response.questions):
				print(f'📋 [QuestionComposerTool] Processing question {i + 1}: Type={question.Question_type}')

				question_data = {
					'id': f'q_{i + 1}',
					'question': question.Question,
					'type': question.Question_type,
					'subtitle': getattr(question, 'subtitle', None),
					'data': getattr(question, 'Question_data', None),
					'required': getattr(question, 'required', True),
					'order': i + 1,
				}

				result_data['questions'].append(question_data)

			# Convert to JSON string
			import json

			json_result = json.dumps(result_data, ensure_ascii=False, indent=2)

			print(f'✅ [QuestionComposerTool] JSON response created successfully')
			print(f'📊 [QuestionComposerTool] Generated {len(result_data["questions"])} questions in JSON format')
			print(f'📈 [QuestionComposerTool] Completeness score: {result_data["analysis"]["completeness_score"]:.3f}')

			return json_result

		except Exception as e:
			print(f'💥 [QuestionComposerTool] Error formatting generation response as JSON: {str(e)}')
			# Return error as JSON
			error_data = {
				'status': 'error',
				'type': 'question_generation',
				'error': str(e),
			}
			return json.dumps(error_data, ensure_ascii=False)

	def _format_analysis_response(self, response) -> str:
		"""Format profile analysis response for agent - Return JSON instead of formatted text"""
		print(f'🔄 [QuestionComposerTool] Formatting profile analysis response as JSON')

		try:
			# Convert analysis response to JSON format
			result_data = {
				'status': 'success',
				'type': 'profile_analysis',
				'analysis': {
					'completeness_score': response.completeness_score,
					'should_continue': response.should_continue,
					'missing_areas': response.missing_areas,
					'suggested_focus': response.suggested_focus,
					'analysis_text': response.analysis,
				},
				'recommendations': {
					'should_ask_more': response.should_continue,
					'priority_areas': response.suggested_focus,
					'summary': ('Profile đã đủ thông tin cơ bản.' if not response.should_continue else 'Nên hỏi thêm để có profile hoàn thiện hơn.'),
				},
			}

			# Convert to JSON string
			import json

			json_result = json.dumps(result_data, ensure_ascii=False, indent=2)

			print(f'✅ [QuestionComposerTool] Analysis JSON response created successfully')
			print(f'📈 [QuestionComposerTool] Completeness score: {result_data["analysis"]["completeness_score"]:.3f}')
			print(f'🎯 [QuestionComposerTool] Missing areas count: {len(result_data["analysis"]["missing_areas"])}')

			return json_result

		except Exception as e:
			print(f'💥 [QuestionComposerTool] Error formatting analysis response as JSON: {str(e)}')
			# Return error as JSON
			error_data = {
				'status': 'error',
				'type': 'profile_analysis',
				'error': str(e),
			}
			return json.dumps(error_data, ensure_ascii=False)


def get_question_composer_tool(db_session: Session) -> QuestionComposerTool:
	"""Factory function để tạo QuestionComposerTool instance"""
	print(f'🏭 [Factory] Creating QuestionComposerTool instance')
	tool = QuestionComposerTool(db_session=db_session)
	print(f'✅ [Factory] QuestionComposerTool instance created successfully')
	return tool
