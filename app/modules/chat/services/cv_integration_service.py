"""
CV Integration Service for Chat System
Tích hợp CV extraction vào chat workflow
"""

import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.modules.chat.models.conversation import Conversation
from app.utils.minio.minio_handler import minio_handler
from app.modules.cv_extraction.repository.cv_agent.cv_processor import (
	CVProcessorWorkflow,
)

# Remove circular import - will use dependency injection instead

logger = logging.getLogger(__name__)


class CVIntegrationService:
	"""Service để integrate CV extraction vào chat system"""

	def __init__(self, db_session: Session):
		self.db_session = db_session
		print(f'[CVIntegrationService] Initialized with db_session: {db_session}')

	async def extract_cv_information(self, file_path: str, file_name: str) -> Dict[str, Any]:
		"""
		Extract thông tin từ CV file

		Args:
		    file_path: Path của file trong MinIO
		    file_name: Tên file gốc

		Returns:
		    Dict chứa thông tin extracted từ CV
		"""
		try:
			print(f'[CVIntegrationService] Extracting CV information from: {file_name} at path: {file_path}')

			# Download file content từ MinIO
			file_content = minio_handler.get_file_content(file_path)
			print(f'[CVIntegrationService] Downloaded file content from MinIO: {file_path}')

			# Initialize CV processor workflow
			cv_processor = CVProcessorWorkflow()
			print(f'[CVIntegrationService] Initialized CV processor workflow')

			# Process CV using LangGraph workflow
			result = await cv_processor.process_cv_content(
				raw_cv_content=file_content.decode('utf-8', errors='ignore'),
				file_name=file_name,
			)
			print(f'[CVIntegrationService] CV extraction completed for: {file_name} with result: {result}')

			return result

		except Exception as e:
			logger.error(f'[CVIntegrationService] Error extracting CV: {str(e)}')
			raise

	async def store_cv_context(self, conversation_id: str, user_id: str, cv_analysis: Dict[str, Any]):
		"""
		Store CV context trong conversation metadata

		Args:
		    conversation_id: ID của conversation
		    user_id: ID của user
		    cv_analysis: Kết quả phân tích CV
		"""
		try:
			print(f'[CVIntegrationService] Storing CV context for conversation: {conversation_id} and user: {user_id}')

			# Import here to avoid circular import
			from app.modules.chat.repository.chat_repo import ChatRepo

			chat_repo = ChatRepo(self.db_session)
			print(f'[CVIntegrationService] Initialized ChatRepo with db_session: {self.db_session}')

			# Get conversation
			conversation: Conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
			print(f'[CVIntegrationService] Retrieved conversation: {conversation}')

			# Store FULL CV analysis data as requested
			cv_context = {
				'cv_uploaded': True,
				'full_cv_analysis': cv_analysis,  # Store complete JSON output
				'cv_summary': cv_analysis.cv_summary,
				'personal_info': cv_analysis.personal_information,
				'skills': [skill.skill_name for skill in cv_analysis.skills_summary.items],
				'experience_count': len(cv_analysis.work_experience_history.items),
				'education_count': len(cv_analysis.education_history.items),
			}
			print(f'[CVIntegrationService] Created CV context: {cv_context}')

			# Update conversation extra_metadata
			existing_metadata = json.loads(conversation.extra_metadata or '{}')

			# Convert cv_analysis to dict trước khi lưu
			cv_context['full_cv_analysis'] = cv_analysis.model_dump()
			print('Debug: ', cv_context['full_cv_analysis'])
			cv_context['cv_summary'] = cv_analysis.cv_summary
			print('Debug: ', cv_context['cv_summary'])
			cv_context['personal_info'] = cv_analysis.personal_information.model_dump()
			print('Debug: ', cv_context['personal_info'])
			existing_metadata['cv_context'] = cv_context
			print(f'[CVIntegrationService] Updated conversation extra_metadata: {existing_metadata}')

			conversation.extra_metadata = json.dumps(existing_metadata)
			self.db_session.commit()
			print(f'[CVIntegrationService] Committed changes to database')

		except Exception as e:
			print(f'[CVIntegrationService] Error storing CV context: {str(e)}')
			raise

	def get_cv_context_for_prompt(self, conversation_id: str, user_id: str) -> Optional[str]:
		"""
		Get CV information để add vào chat prompt

		Args:
		    conversation_id: ID của conversation
		    user_id: ID của user

		Returns:
		    String context về CV information
		"""
		try:
			print(f'[CVIntegrationService] Getting CV context for conversation: {conversation_id} and user: {user_id}')

			# Import here to avoid circular import
			from app.modules.chat.repository.chat_repo import ChatRepo

			chat_repo = ChatRepo(self.db_session)
			print(f'[CVIntegrationService] Initialized ChatRepo with db_session: {self.db_session}')

			conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
			print(f'[CVIntegrationService] Retrieved conversation: {conversation}')

			if not conversation or not conversation.extra_metadata:
				print(f'[CVIntegrationService] No conversation or extra_metadata found')
				return None

			metadata = json.loads(conversation.extra_metadata)
			cv_context = metadata.get('cv_context')
			print(f'[CVIntegrationService] Retrieved CV context: {cv_context}')

			if not cv_context or not cv_context.get('cv_uploaded'):
				print(f'[CVIntegrationService] No CV context or CV not uploaded')
				return None

			# Format CV info cho prompt
			context_parts = []

			# Personal info
			personal_info = cv_context.get('personal_info', {})
			if personal_info.get('full_name'):
				context_parts.append(f'Tên: {personal_info["full_name"]}')

			# Skills
			skills = cv_context.get('skills', [])
			if skills:
				context_parts.append(f'Kỹ năng chính: {", ".join(skills[:10])}')  # Top 10 skills

			# Experience
			exp_count = cv_context.get('experience_count', 0)
			if exp_count > 0:
				context_parts.append(f'Có {exp_count} kinh nghiệm làm việc')

			# Education
			edu_count = cv_context.get('education_count', 0)
			if edu_count > 0:
				context_parts.append(f'Có {edu_count} bằng cấp/học vấn')

			# CV Summary
			cv_summary = cv_context.get('cv_summary', '')
			if cv_summary:
				context_parts.append(f'Tóm tắt CV: {cv_summary}')

			if context_parts:
				print(f'[CVIntegrationService] Generated context parts: {context_parts}')
				return f'THÔNG TIN CV CỦA NGƯỜI DÙNG:\n{chr(10).join(context_parts)}\n---'

			print(f'[CVIntegrationService] No context parts generated')
			return None

		except Exception as e:
			logger.error(f'[CVIntegrationService] Error getting CV context: {str(e)}')
			return None
