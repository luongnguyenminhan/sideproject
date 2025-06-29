import logging
from typing import Optional, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.database import get_db
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import (
	ProcessCVRequest,
	CVAnalysisResult,
	ProcessCVResponse,
)
from app.utils.n8n_api_client import n8n_client
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


class CVRepo:
	"""
	CV Repository for handling CV processing operations using N8N API client.
	Follows 3-layer architecture - repository layer for business logic.
	"""

	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		logger.info('[CVRepo] Initialized CV repository')

	async def process_cv(self, request: ProcessCVRequest) -> APIResponse:
		"""Process CV from URL using N8N API client"""
		logger.info(f'[CVRepo] Processing CV from URL: {request.cv_file_url}')

		if not request.cv_file_url:
			raise ValidationException(_('cv_file_url_required'))

		try:
			# Download CV file using N8N client helper
			file_content, filename = await n8n_client.download_file_content(request.cv_file_url)
			if not file_content:
				logger.error('[CVRepo] Failed to download CV file')
				return APIResponse(
					error_code=1,
					message=_('failed_to_download_file'),
					data=None,
				)

			# Analyze CV using N8N client
			result = await n8n_client.analyze_cv(file_content, filename)
			print(f'[CVRepo] Result from N8N API: {result}')

			logger.info('[CVRepo] CV processed successfully via N8N API')
			print(f'[CVRepo] Processed CV result: {result}')
			return self._build_success_response(result, request.cv_file_url)

		except ValidationException as e:
			logger.error(f'[CVRepo] Validation error processing CV: {str(e)}')
			raise
		except Exception as e:
			logger.error(f'[CVRepo] Error processing CV: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)

	async def process_cv_binary(self, request: ProcessCVRequest, file_content: bytes, filename: str) -> APIResponse:
		"""Process CV from binary file content using N8N API client"""
		logger.info(f'[CVRepo] Processing binary CV file: {filename}')

		if not file_content or not filename:
			raise ValidationException(_('invalid_file_content_or_filename'))

		try:
			# Analyze CV using N8N client
			result = await n8n_client.analyze_cv(file_content, filename)
			print(f'[CVRepo] Result from N8N API: {result}')
			logger.info('[CVRepo] Binary CV processed successfully via N8N API')
			return self._build_success_response(result, filename=filename)

		except ValidationException as e:
			logger.error(f'[CVRepo] Validation error processing binary CV: {str(e)}')
			raise
		except Exception as e:
			logger.error(f'[CVRepo] Error processing binary CV: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_analyzing_cv'),
				data=None,
			)

	def _build_success_response(
		self,
		result: Dict[str, Any],
		cv_file_url: Optional[str] = None,
		filename: Optional[str] = None,
	) -> APIResponse:
		"""Build success response from N8N API result"""
		try:
			# Extract data with safe defaults
			print(f'[CVRepo] Building response from result: {result}')
			skills_items = result.get('skills_summary', {}).get('items', []) if isinstance(result.get('skills_summary'), dict) else []
			experience_items = result.get('work_experience_history', {}).get('items', []) if isinstance(result.get('work_experience_history'), dict) else []

			response_data = ProcessCVResponse(
				cv_file_url=cv_file_url,
				filename=filename,
				cv_analysis_result=CVAnalysisResult(**result),
				personal_info=result.get('personal_information'),
				skills_count=len(skills_items) if isinstance(skills_items, list) else 0,
				experience_count=(len(experience_items) if isinstance(experience_items, list) else 0),
				cv_summary=result.get('cv_summary'),
			)

			return APIResponse(
				error_code=0,
				message=_('cv_processed_successfully'),
				data=response_data,
			)

		except (ValueError, KeyError) as e:
			logger.error(f'[CVRepo] Error building response: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_processing_cv_response'),
				data=None,
			)
		except Exception as e:
			logger.error(f'[CVRepo] Unexpected error building response: {str(e)}')
			return APIResponse(
				error_code=1,
				message=_('error_processing_cv_response'),
				data=None,
			)
