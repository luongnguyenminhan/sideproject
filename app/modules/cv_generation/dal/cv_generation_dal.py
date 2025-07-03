from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta

from app.core.base_dal import BaseDAL
from app.modules.cv_generation.models.cv_generation import CVGeneration


class CVGenerationDAL(BaseDAL[CVGeneration]):
	"""Data Access Layer cho CV Generation"""

	def __init__(self, db: Session):
		super().__init__(db, CVGeneration)

	def create_generation_job(
		self,
		job_id: str,
		template_type: str = 'modern',
		color_theme: str = 'blue',
		user_id: Optional[str] = None,
		cv_extraction_id: Optional[str] = None,
		custom_prompt: Optional[str] = None,
		generation_config: Optional[Dict[str, Any]] = None,
		cv_data_snapshot: Optional[Dict[str, Any]] = None,
	) -> CVGeneration:
		"""Tạo CV generation job mới"""
		job_data = {
			'job_id': job_id,
			'user_id': user_id,
			'cv_extraction_id': cv_extraction_id,
			'template_type': template_type,
			'color_theme': color_theme,
			'custom_prompt': custom_prompt,
			'status': 'pending',
			'progress': 0.0,
			'generation_config': generation_config,
			'cv_data_snapshot': cv_data_snapshot,
			'started_at': datetime.utcnow(),
		}
		return self.create(job_data)

	def get_by_job_id(self, job_id: str) -> Optional[CVGeneration]:
		"""Lấy CV generation job theo job_id"""
		return self.db.query(CVGeneration).filter(CVGeneration.job_id == job_id).first()

	def get_by_user_id(self, user_id: str, limit: int = 50) -> List[CVGeneration]:
		"""Lấy tất cả CV generation jobs của user"""
		return self.db.query(CVGeneration).filter(CVGeneration.user_id == user_id).order_by(desc(CVGeneration.created_at)).limit(limit).all()

	def update_status(
		self,
		job_id: str,
		status: str,
		progress: Optional[float] = None,
		error_message: Optional[str] = None,
	) -> Optional[CVGeneration]:
		"""Cập nhật status của generation job"""
		job = self.get_by_job_id(job_id)
		if not job:
			return None

		update_data = {'status': status}

		if progress is not None:
			update_data['progress'] = progress

		if error_message is not None:
			update_data['error_message'] = error_message

		if status == 'completed':
			update_data['completed_at'] = datetime.utcnow()
			update_data['progress'] = 100.0

		for key, value in update_data.items():
			setattr(job, key, value)

		self.db.commit()
		self.db.refresh(job)
		return job

	def update_generation_result(
		self,
		job_id: str,
		latex_source: Optional[str] = None,
		pdf_file_path: Optional[str] = None,
		pdf_file_url: Optional[str] = None,
		file_size: Optional[int] = None,
		generation_time: Optional[float] = None,
	) -> Optional[CVGeneration]:
		"""Cập nhật kết quả generation"""
		job = self.get_by_job_id(job_id)
		if not job:
			return None

		update_data = {}

		if latex_source is not None:
			update_data['latex_source'] = latex_source

		if pdf_file_path is not None:
			update_data['pdf_file_path'] = pdf_file_path

		if pdf_file_url is not None:
			update_data['pdf_file_url'] = pdf_file_url

		if file_size is not None:
			update_data['file_size'] = file_size

		if generation_time is not None:
			update_data['generation_time'] = generation_time

		for key, value in update_data.items():
			setattr(job, key, value)

		self.db.commit()
		self.db.refresh(job)
		return job

	def update_llm_usage(
		self,
		job_id: str,
		model_used: Optional[str] = None,
		input_tokens: Optional[int] = None,
		output_tokens: Optional[int] = None,
		total_tokens: Optional[int] = None,
		cost_usd: Optional[float] = None,
	) -> Optional[CVGeneration]:
		"""Cập nhật thông tin LLM usage"""
		job = self.get_by_job_id(job_id)
		if not job:
			return None

		update_data = {}

		if model_used is not None:
			update_data['llm_model_used'] = model_used

		if input_tokens is not None:
			update_data['llm_input_tokens'] = input_tokens

		if output_tokens is not None:
			update_data['llm_output_tokens'] = output_tokens

		if total_tokens is not None:
			update_data['llm_total_tokens'] = total_tokens

		if cost_usd is not None:
			update_data['llm_cost_usd'] = cost_usd

		for key, value in update_data.items():
			setattr(job, key, value)

		self.db.commit()
		self.db.refresh(job)
		return job

	def get_by_status(self, status: str, limit: int = 100) -> List[CVGeneration]:
		"""Lấy jobs theo status"""
		return self.db.query(CVGeneration).filter(CVGeneration.status == status).order_by(desc(CVGeneration.created_at)).limit(limit).all()

	def get_pending_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs đang pending"""
		return self.get_by_status('pending', limit)

	def get_processing_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs đang processing"""
		return self.get_by_status('processing', limit)

	def get_failed_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs failed"""
		return self.get_by_status('failed', limit)

	def get_completed_jobs(self, limit: int = 50) -> List[CVGeneration]:
		"""Lấy jobs completed"""
		return self.get_by_status('completed', limit)

	def get_recent_jobs(self, hours: int = 24, limit: int = 100) -> List[CVGeneration]:
		"""Lấy jobs trong khoảng thời gian gần đây"""
		since = datetime.utcnow() - timedelta(hours=hours)
		return self.db.query(CVGeneration).filter(CVGeneration.created_at >= since).order_by(desc(CVGeneration.created_at)).limit(limit).all()

	def get_user_stats(self, user_id: str) -> Dict[str, Any]:
		"""Lấy thống kê CV generation của user"""
		jobs = self.get_by_user_id(user_id, limit=1000)  # Lấy nhiều để tính stats

		total_jobs = len(jobs)
		completed_jobs = len([j for j in jobs if j.status == 'completed'])
		failed_jobs = len([j for j in jobs if j.status == 'failed'])
		pending_jobs = len([j for j in jobs if j.status == 'pending'])
		processing_jobs = len([j for j in jobs if j.status == 'processing'])

		total_tokens = sum([j.llm_total_tokens or 0 for j in jobs])
		total_cost = sum([j.llm_cost_usd or 0 for j in jobs])

		avg_generation_time = None
		completed_with_time = [j for j in jobs if j.status == 'completed' and j.generation_time]
		if completed_with_time:
			avg_generation_time = sum([j.generation_time for j in completed_with_time]) / len(completed_with_time)

		return {
			'total_jobs': total_jobs,
			'completed_jobs': completed_jobs,
			'failed_jobs': failed_jobs,
			'pending_jobs': pending_jobs,
			'processing_jobs': processing_jobs,
			'success_rate': completed_jobs / total_jobs if total_jobs > 0 else 0,
			'total_tokens_used': total_tokens,
			'total_cost_usd': round(total_cost, 4),
			'avg_generation_time_seconds': (round(avg_generation_time, 2) if avg_generation_time else None),
		}

	def cleanup_old_jobs(self, days: int = 30) -> int:
		"""Cleanup jobs cũ hơn N ngày"""
		cutoff_date = datetime.utcnow() - timedelta(days=days)

		old_jobs = self.db.query(CVGeneration).filter(CVGeneration.created_at < cutoff_date).all()

		count = len(old_jobs)

		for job in old_jobs:
			self.db.delete(job)

		self.db.commit()
		return count

	def search_jobs(
		self,
		user_id: Optional[str] = None,
		status: Optional[str] = None,
		template_type: Optional[str] = None,
		date_from: Optional[datetime] = None,
		date_to: Optional[datetime] = None,
		limit: int = 50,
	) -> List[CVGeneration]:
		"""Tìm kiếm jobs với filters"""
		query = self.db.query(CVGeneration)

		if user_id:
			query = query.filter(CVGeneration.user_id == user_id)

		if status:
			query = query.filter(CVGeneration.status == status)

		if template_type:
			query = query.filter(CVGeneration.template_type == template_type)

		if date_from:
			query = query.filter(CVGeneration.created_at >= date_from)

		if date_to:
			query = query.filter(CVGeneration.created_at <= date_to)

		return query.order_by(desc(CVGeneration.created_at)).limit(limit).all()
