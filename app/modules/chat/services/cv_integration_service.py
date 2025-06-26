"""
CV Integration Service for Chat System
Tích hợp CV extraction vào chat workflow
"""

import logging
import json
import aiohttp
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.modules.chat.models.conversation import Conversation
from app.utils.minio.minio_handler import minio_handler

logger = logging.getLogger(__name__)


class CVIntegrationService:
	"""Service để integrate CV extraction vào chat system"""

	def __init__(self, db_session: Session):
		self.db_session = db_session
		print(f'[CVIntegrationService] Initialized with db_session: {db_session}')

	async def extract_cv_information(self, file_path: str, file_name: str) -> Dict[str, Any]:
		"""
		Extract thông tin từ CV file using internal CV extraction API

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

			# Call internal CV extraction API
			result = await self._call_cv_extraction_api(file_content, file_name)
			print(f'[CVIntegrationService] CV extraction completed for: {file_name} with result: {result}')

			return result

		except Exception as e:
			logger.error(f'[CVIntegrationService] Error extracting CV: {str(e)}')
			raise

	async def _call_cv_extraction_api(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
		"""
		Call N8N CV extraction API directly

		Args:
		    file_content: Binary content of the file
		    file_name: Original filename

		Returns:
		    Dict containing CV analysis result
		"""
		try:
			# Call N8N API directly
			api_url = 'https://n8n.wc504.io.vn/webhook/888a07e8-25d6-4671-a36c-939a52740f31'
			headers = {'X-Header-Authentication': 'n8ncvextraction'}

			# Determine content type based on file extension
			file_extension = file_name.split('.')[-1].lower()
			content_type_map = {
				'pdf': 'application/pdf',
				'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
				'txt': 'text/plain',
			}
			content_type = content_type_map.get(file_extension, 'application/octet-stream')

			# Create form data
			data = aiohttp.FormData()
			data.add_field('file', file_content, filename=file_name, content_type=content_type)

			async with aiohttp.ClientSession() as session:
				async with session.post(api_url, headers=headers, data=data, ssl=False) as response:
					if response.status == 200:
						result = await response.json()[0]
						return result
					else:
						logger.error(f'N8N API HTTP error: {response.status}')
						raise Exception(f'N8N API error: HTTP {response.status}')

		except Exception as e:
			logger.error(f'Error calling N8N CV extraction API: {str(e)}')
			raise

	def _get_content_type(self, filename: str) -> str:
		"""Get content type based on file extension"""
		extension = filename.lower().split('.')[-1]
		content_type_map = {
			'pdf': 'application/pdf',
			'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
			'txt': 'text/plain',
		}
		return content_type_map.get(extension, 'application/octet-stream')

	async def store_cv_context(self, conversation_id: str, user_id: str, cv_analysis: Dict[str, Any]):
		"""
		Store CV context trong conversation metadata

		Args:
		    conversation_id: ID của conversation
		    user_id: ID của user
		    cv_analysis: Kết quả phân tích CV từ N8N API
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

			# Store CV analysis data from N8N API response
			cv_context = {
				'cv_uploaded': True,
				'full_cv_analysis': cv_analysis,  # Store complete JSON output from N8N
			}

			# Extract specific fields if available in the response
			# Since the structure may vary, we'll use .get() to safely access fields
			if isinstance(cv_analysis, dict):
				cv_context.update({
					'cv_summary': cv_analysis.get('cv_summary', ''),
					'personal_info': cv_analysis.get('personal_information', {}),
					'skills': cv_analysis.get('skills', []),
					'experience': cv_analysis.get('experience', []),
					'education': cv_analysis.get('education', []),
				})

				# Count items if they are lists
				if isinstance(cv_context['experience'], list):
					cv_context['experience_count'] = len(cv_context['experience'])
				if isinstance(cv_context['education'], list):
					cv_context['education_count'] = len(cv_context['education'])

			print(f'[CVIntegrationService] Created CV context: {cv_context}')

			# Update conversation extra_metadata
			existing_metadata = json.loads(conversation.extra_metadata or '{}')
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
			if personal_info:
				if isinstance(personal_info, dict):
					name = personal_info.get('full_name') or personal_info.get('name')
					if name:
						context_parts.append(f'Tên: {name}')

					email = personal_info.get('email')
					if email:
						context_parts.append(f'Email: {email}')

					phone = personal_info.get('phone')
					if phone:
						context_parts.append(f'Điện thoại: {phone}')

			# Skills
			skills = cv_context.get('skills', [])
			if skills:
				if isinstance(skills, list):
					skills_text = ', '.join(skills[:10])  # Top 10 skills
					context_parts.append(f'Kỹ năng chính: {skills_text}')

			# Experience
			experience = cv_context.get('experience', [])
			exp_count = cv_context.get(
				'experience_count',
				len(experience) if isinstance(experience, list) else 0,
			)
			if exp_count > 0:
				context_parts.append(f'Có {exp_count} kinh nghiệm làm việc')

			# Education
			education = cv_context.get('education', [])
			edu_count = cv_context.get('education_count', len(education) if isinstance(education, list) else 0)
			if edu_count > 0:
				context_parts.append(f'Có {edu_count} bằng cấp/học vấn')

			# CV Summary
			cv_summary = cv_context.get('cv_summary', '')
			if cv_summary:
				context_parts.append(f'Tóm tắt CV: {cv_summary}')

			# If we have full analysis, try to extract more detailed info
			full_analysis = cv_context.get('full_cv_analysis', {})
			if full_analysis and isinstance(full_analysis, dict):
				# Try to get summary from various possible keys
				summary_keys = ['summary', 'profile', 'objective', 'about']
				for key in summary_keys:
					if key in full_analysis and full_analysis[key]:
						context_parts.append(f'Mô tả bản thân: {full_analysis[key]}')
						break

			if context_parts:
				print(f'[CVIntegrationService] Generated context parts: {context_parts}')
				return f'THÔNG TIN CV CỦA NGƯỜI DÙNG:\n{chr(10).join(context_parts)}\n---'

			print(f'[CVIntegrationService] No context parts generated')
			return None

		except Exception as e:
			logger.error(f'[CVIntegrationService] Error getting CV context: {str(e)}')
			return None
