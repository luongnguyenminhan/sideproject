from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.core.base_model import APIResponse
from app.middleware.translation_manager import _
from app.exceptions.exception import NotFoundException
from app.modules.cv_generation.dal.cv_generation_dal import CVGenerationDAL
from app.core.database import get_db
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.modules.cv_generation.models.cv_generation import CVGeneration


class CVGenerationRepo:
	def __init__(self, db: Session = Depends(get_db)):
		self.db = db
		self.cv_dal = CVGenerationDAL(db)

	def get_by_id(self, cv_id: str):
		cv = self.cv_dal.get_by_id(cv_id)
		if not cv:
			raise NotFoundException(_('cv_not_found'))
		return cv

	def create_cv(self, cv_data: dict):
		return self.cv_dal.create(cv_data)

	def update_cv(self, cv_id: str, update_data: dict):
		updated_cv = self.cv_dal.update(cv_id, update_data)
		if not updated_cv:
			raise NotFoundException(_('cv_not_found'))
		return updated_cv


class CVGenerationRepository:
	"""Repository cho CV Generation operations"""

	def __init__(self, db: Session):
		self.dal = CVGenerationDAL(db)

	def create_job(
		self,
		template_type: str = 'modern',
		color_theme: str = 'blue',
		user_id: Optional[str] = None,
		cv_extraction_id: Optional[str] = None,
		custom_prompt: Optional[str] = None,
		generation_config: Optional[Dict[str, Any]] = None,
		cv_data_snapshot: Optional[Dict[str, Any]] = None,
	) -> CVGeneration:
		"""Tạo CV generation job mới với unique job_id"""
		job_id = f'cv_gen_{uuid.uuid4().hex[:12]}'

		return self.dal.create_generation_job(
			job_id=job_id,
			template_type=template_type,
			color_theme=color_theme,
			user_id=user_id,
			cv_extraction_id=cv_extraction_id,
			custom_prompt=custom_prompt,
			generation_config=generation_config,
			cv_data_snapshot=cv_data_snapshot,
		)

	def get_job_by_id(self, job_id: str) -> Optional[CVGeneration]:
		"""Lấy job theo job_id"""
		return self.dal.get_by_job_id(job_id)

	def get_user_jobs(self, user_id: str, limit: int = 50) -> List[CVGeneration]:
		"""Lấy tất cả jobs của user"""
		return self.dal.get_by_user_id(user_id, limit)

	def start_processing(self, job_id: str) -> Optional[CVGeneration]:
		"""Đánh dấu job bắt đầu processing"""
		return self.dal.update_status(job_id, 'processing', progress=10.0)

	def update_progress(self, job_id: str, progress: float, message: Optional[str] = None) -> Optional[CVGeneration]:
		"""Cập nhật progress của job"""
		return self.dal.update_status(job_id, 'processing', progress=progress, error_message=message)

	def complete_job(
		self,
		job_id: str,
		latex_source: str,
		pdf_file_path: Optional[str] = None,
		pdf_file_url: Optional[str] = None,
		file_size: Optional[int] = None,
		generation_time: Optional[float] = None,
		llm_usage: Optional[Dict[str, Any]] = None,
	) -> Optional[CVGeneration]:
		"""Hoàn thành job thành công"""
		# Update result
		job = self.dal.update_generation_result(
			job_id=job_id,
			latex_source=latex_source,
			pdf_file_path=pdf_file_path,
			pdf_file_url=pdf_file_url,
			file_size=file_size,
			generation_time=generation_time,
		)

		# Update LLM usage if provided
		if llm_usage and job:
			self.dal.update_llm_usage(
				job_id=job_id,
				model_used=llm_usage.get('model_used'),
				input_tokens=llm_usage.get('input_tokens'),
				output_tokens=llm_usage.get('output_tokens'),
				total_tokens=llm_usage.get('total_tokens'),
				cost_usd=llm_usage.get('cost_usd'),
			)

		# Mark as completed
		return self.dal.update_status(job_id, 'completed')

	def fail_job(self, job_id: str, error_message: str) -> Optional[CVGeneration]:
		"""Đánh dấu job thất bại"""
		return self.dal.update_status(job_id, 'failed', error_message=error_message)

	def get_pending_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs đang pending"""
		return self.dal.get_pending_jobs(limit)

	def get_processing_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs đang processing"""
		return self.dal.get_processing_jobs(limit)

	def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
		"""Lấy thống kê của user"""
		return self.dal.get_user_stats(user_id)

	def get_recent_jobs(self, hours: int = 24) -> List[CVGeneration]:
		"""Lấy jobs gần đây"""
		return self.dal.get_recent_jobs(hours)

	def search_jobs(
		self,
		user_id: Optional[str] = None,
		status: Optional[str] = None,
		template_type: Optional[str] = None,
		date_from: Optional[datetime] = None,
		date_to: Optional[datetime] = None,
		limit: int = 50,
	) -> List[CVGeneration]:
		"""Tìm kiếm jobs"""
		return self.dal.search_jobs(
			user_id=user_id,
			status=status,
			template_type=template_type,
			date_from=date_from,
			date_to=date_to,
			limit=limit,
		)

	def cleanup_old_jobs(self, days: int = 30) -> int:
		"""Cleanup jobs cũ"""
		return self.dal.cleanup_old_jobs(days)
