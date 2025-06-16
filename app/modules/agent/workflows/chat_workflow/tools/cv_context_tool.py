"""
CV Context Tool for Chat Agent
Provide CV information as context to the agent
"""

import logging
import json
from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CVContextInput(BaseModel):
	"""Input schema for CV Context tool"""

	conversation_id: str = Field(description='ID của conversation')
	user_id: str = Field(description='ID của user')


class CVContextTool(BaseTool):
	"""Tool để get CV context for conversation"""

	name: str = 'cv_context'
	description: str = """
    Lấy thông tin CV của user từ conversation context.
    Sử dụng khi cần hiểu về background, kỹ năng, kinh nghiệm của user để tư vấn phù hợp.
    Input: conversation_id và user_id
    """

	db_session: Session = Field(exclude=True)

	def __init__(self, db_session: Session, **kwargs):
		super().__init__(db_session=db_session, **kwargs)

	def _run(self, conversation_id: str, user_id: str) -> str:
		"""
		Get CV context từ conversation metadata

		Args:
		    conversation_id: ID của conversation
		    user_id: ID của user

		Returns:
		    String context về CV information
		"""
		try:
			logger.info(f'[CVContextTool] Getting CV context for conversation: {conversation_id}')

			# Import here to avoid circular import
			from app.modules.chat.repository.chat_repo import ChatRepo

			chat_repo = ChatRepo(self.db_session)

			# Get conversation
			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)

			if not conversation or not conversation.metadata:
				return 'Không có thông tin CV được upload trong cuộc trò chuyện này.'

			metadata = json.loads(conversation.metadata)
			cv_context = metadata.get('cv_context')

			if not cv_context or not cv_context.get('cv_uploaded'):
				return 'User chưa upload CV trong cuộc trò chuyện này.'

			# Get full CV analysis for detailed context
			full_cv_analysis = cv_context.get('full_cv_analysis', {})

			# Format comprehensive CV information
			context_parts = []

			# Personal info
			personal_info = cv_context.get('personal_info', {})
			if personal_info:
				context_parts.append('=== THÔNG TIN CÁ NHÂN ===')
				if personal_info.get('full_name'):
					context_parts.append(f'Tên: {personal_info["full_name"]}')
				if personal_info.get('email'):
					context_parts.append(f'Email: {personal_info["email"]}')
				if personal_info.get('phone'):
					context_parts.append(f'Điện thoại: {personal_info["phone"]}')
				if personal_info.get('location'):
					context_parts.append(f'Địa chỉ: {personal_info["location"]}')
				context_parts.append('')

			# CV Summary
			cv_summary = cv_context.get('cv_summary', '')
			if cv_summary:
				context_parts.append('=== TÓM TẮT CV ===')
				context_parts.append(cv_summary)
				context_parts.append('')

			# Skills
			skills = cv_context.get('skills', [])
			if skills:
				context_parts.append('=== KỸ NĂNG ===')
				context_parts.append(f'Các kỹ năng chính: {", ".join(skills[:15])}')
				context_parts.append('')

			# Experience
			exp_count = cv_context.get('experience_count', 0)
			if exp_count > 0:
				context_parts.append('=== KINH NGHIỆM LÀM VIỆC ===')
				context_parts.append(f'Có {exp_count} vị trí/công ty đã làm việc')

				# Get detailed experience from full analysis
				work_exp = full_cv_analysis.get('work_experience_history', {}).get('items', [])
				for i, exp in enumerate(work_exp[:3]):  # Top 3 experiences
					if exp.get('company_name') and exp.get('job_title'):
						context_parts.append(f'{i + 1}. {exp["job_title"]} tại {exp["company_name"]}')
						if exp.get('duration'):
							context_parts.append(f'   Thời gian: {exp["duration"]}')
						if exp.get('key_responsibilities'):
							context_parts.append(f'   Trách nhiệm: {exp["key_responsibilities"][:200]}...')
				context_parts.append('')

			# Education
			edu_count = cv_context.get('education_count', 0)
			if edu_count > 0:
				context_parts.append('=== HỌC VẤN ===')
				context_parts.append(f'Có {edu_count} bằng cấp/khóa học')

				# Get detailed education from full analysis
				education = full_cv_analysis.get('education_history', {}).get('items', [])
				for i, edu in enumerate(education[:2]):  # Top 2 education
					if edu.get('institution_name') and edu.get('degree'):
						context_parts.append(f'{i + 1}. {edu["degree"]} - {edu["institution_name"]}')
						if edu.get('graduation_year'):
							context_parts.append(f'   Năm tốt nghiệp: {edu["graduation_year"]}')
				context_parts.append('')

			# Projects
			projects = full_cv_analysis.get('projects_showcase', {}).get('items', [])
			if projects:
				context_parts.append('=== DỰ ÁN NỔI BẬT ===')
				for i, project in enumerate(projects[:2]):  # Top 2 projects
					if project.get('project_name'):
						context_parts.append(f'{i + 1}. {project["project_name"]}')
						if project.get('description'):
							context_parts.append(f'   Mô tả: {project["description"][:150]}...')
				context_parts.append('')

			# Certificates
			certs = full_cv_analysis.get('certificates_and_courses', {}).get('items', [])
			if certs:
				context_parts.append('=== CHỨNG CHỈ & KHÓA HỌC ===')
				cert_names = [cert.get('certificate_name', '') for cert in certs[:5]]
				context_parts.append(f'Các chứng chỉ: {", ".join(cert_names)}')
				context_parts.append('')

			if context_parts:
				final_context = '\n'.join(context_parts)
				final_context += '\n=== HƯỚNG DẪN SỬ DỤNG CV ===\n'
				final_context += 'Sử dụng thông tin trên để:\n'
				final_context += '- Tư vấn cơ hội việc làm phù hợp\n'
				final_context += '- Đề xuất kỹ năng cần phát triển\n'
				final_context += '- Gợi ý khóa học/chứng chỉ\n'
				final_context += '- Tư vấn định hướng nghề nghiệp\n'

				logger.info(f'[CVContextTool] CV context retrieved successfully: {len(final_context)} chars')
				return final_context
			else:
				return 'CV đã được upload nhưng không có thông tin chi tiết.'

		except Exception as e:
			logger.error(f'[CVContextTool] Error getting CV context: {str(e)}')
			return f'Lỗi khi lấy thông tin CV: {str(e)}'

	async def _arun(self, conversation_id: str, user_id: str) -> str:
		"""Async version"""
		return self._run(conversation_id, user_id)
