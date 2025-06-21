"""
Question Composer API routes.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.database import get_db

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import APIResponse, PaginatedResponse, PagingInfo

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.exceptions.handlers import handle_exceptions

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.middleware.translation_manager import _

from ...repository.question_composer_repo import QuestionComposerRepo
from ...schemas.question_request import (
	QuestionGenerationRequest,
	AnalyzeUserProfileRequest,
	GetQuestionSessionRequest,
	SearchQuestionSessionsRequest,
)
from ...schemas.question_response import (
	QuestionGenerationAPIResponse,
	UserProfileAnalysisAPIResponse,
	QuestionSessionAPIResponse,
	QuestionSessionListResponse,
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router - MUST be named 'route'
route = APIRouter(prefix='/question-composer', tags=['Question Composer'])


# Dependency injection
def get_question_composer_repo(db: Session = Depends(get_db)) -> QuestionComposerRepo:
	"""Get question composer repository instance"""
	return QuestionComposerRepo(db)


@route.post(
	'/generate',
	response_model=QuestionGenerationAPIResponse,
	summary='Generate intelligent questions',
	description='Generate personalized questions based on user profile and history',
)
@handle_exceptions
async def generate_questions(
	request: QuestionGenerationRequest,
	repo: QuestionComposerRepo = Depends(get_question_composer_repo),
) -> APIResponse:
	"""
	Generate câu hỏi thông minh dựa trên profile người dùng.

	- **request**: Thông tin request bao gồm user profile và câu hỏi đã hỏi

	Returns danh sách câu hỏi được generate và analysis.
	"""
	logger.info(f'Generating questions for session: {request.session_id}')

	result = await repo.generate_questions(request)

	logger.info(f'Successfully generated {len(result.questions)} questions')
	return APIResponse(error_code=0, message=_('success'), data=result.model_dump())


@route.post(
	'/analyze',
	response_model=UserProfileAnalysisAPIResponse,
	summary='Analyze user profile completeness',
	description='Analyze how complete the user profile is without generating questions',
)
@handle_exceptions
async def analyze_user_profile(
	request: AnalyzeUserProfileRequest,
	repo: QuestionComposerRepo = Depends(get_question_composer_repo),
) -> APIResponse:
	"""
	Phân tích mức độ đầy đủ của user profile.

	- **request**: User profile data để phân tích

	Returns analysis kết quả với completeness score và missing areas.
	"""
	logger.info('Analyzing user profile completeness')

	result = await repo.analyze_user_profile(request)

	logger.info(f'Analysis completed - Score: {result.completeness_score:.2f}')
	return APIResponse(error_code=0, message=_('success'), data=result.model_dump())


@route.get(
	'/session/{session_id}',
	response_model=QuestionSessionAPIResponse,
	summary='Get question session',
	description='Get question session details by session ID',
)
@handle_exceptions
async def get_question_session(session_id: str, repo: QuestionComposerRepo = Depends(get_question_composer_repo)) -> APIResponse:
	"""
	Get chi tiết question session.

	- **session_id**: Session ID để retrieve

	Returns session details bao gồm progress và questions.
	"""
	logger.info(f'Getting question session: {session_id}')

	result = repo.get_question_session(session_id)

	return APIResponse(error_code=0, message=_('success'), data=result.model_dump())


@route.get(
	'/sessions',
	response_model=QuestionSessionListResponse,
	summary='Search question sessions',
	description='Search and filter question sessions',
)
@handle_exceptions
async def search_question_sessions(
	request: SearchQuestionSessionsRequest = Depends(),
	repo: QuestionComposerRepo = Depends(get_question_composer_repo),
) -> APIResponse:
	"""
	Search question sessions với filtering.

	- **request**: Search criteria và filters

	Returns danh sách sessions matching criteria.
	"""
	logger.info('Searching question sessions')

	results = repo.search_question_sessions(request)

	# For simplicity, returning all results without pagination
	# In production, you might want to implement proper pagination
	return APIResponse(
		error_code=0,
		message=_('success'),
		data=PaginatedResponse(
			items=results,
			paging=PagingInfo(total=len(results), total_pages=1, page=1, page_size=len(results)),
		).model_dump(),
	)


@route.get(
	'/health',
	response_model=APIResponse,
	summary='Health check',
	description='Check if the question composer service is running',
)
@handle_exceptions
async def health_check() -> APIResponse:
	"""
	Health check endpoint.
	"""
	return APIResponse(
		error_code=0,
		message=_('success'),
		data={'status': 'healthy', 'service': 'question-composer', 'version': '1.0.0'},
	)


@route.get(
	'/info',
	response_model=APIResponse,
	summary='Service information',
	description='Get detailed information about the question composer service',
)
@handle_exceptions
async def get_service_info(
	repo: QuestionComposerRepo = Depends(get_question_composer_repo),
) -> APIResponse:
	"""
	Get service information và configuration.
	"""
	info = repo.get_service_info()

	return APIResponse(error_code=0, message=_('success'), data=info)


@route.get(
	'/question-types',
	response_model=APIResponse,
	summary='Get supported question types',
	description='Get list of supported question types and their descriptions',
)
@handle_exceptions
async def get_question_types() -> APIResponse:
	"""
	Get danh sách các loại câu hỏi được support.
	"""
	return APIResponse(
		error_code=0,
		message=_('success'),
		data={
			'question_types': [
				{
					'type': 'single_option',
					'description': 'Single choice question with radio buttons',
					'example': 'Bạn thích làm việc theo cách nào nhất?',
				},
				{
					'type': 'multiple_choice',
					'description': 'Multiple choice question with checkboxes',
					'example': 'Bạn có kinh nghiệm với những công nghệ nào?',
				},
				{
					'type': 'text_input',
					'description': 'Text input fields for detailed information',
					'example': 'Mô tả về dự án quan trọng nhất của bạn',
				},
				{
					'type': 'sub_form',
					'description': 'Nested questions about related topics',
					'example': 'Về việc học tập và phát triển bản thân',
				},
			],
			'max_questions_per_round': 4,
			'supported_languages': ['vi', 'en'],
		},
	)


logger.info('Question Composer API routes loaded!')
