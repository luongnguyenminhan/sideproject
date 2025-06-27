"""
CV Integration Service for Chat System
Tích hợp CV extraction vào chat workflow sử dụng N8N API Client
"""

import logging
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.modules.chat.models.conversation import Conversation
from app.utils.minio.minio_handler import minio_handler
from app.utils.n8n_api_client import n8n_client
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _

logger = logging.getLogger(__name__)


class CVIntegrationService:
    """
    Service để integrate CV extraction vào chat system using N8N API client.
    Follows 3-layer architecture - service layer for business orchestration.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session
        logger.info("[CVIntegrationService] Initialized with database session")

    async def extract_cv_information(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Extract thông tin từ CV file using N8N API client

        Args:
            file_path: Path của file trong MinIO
            file_name: Tên file gốc

        Returns:
            Dict chứa thông tin extracted từ CV

        Raises:
            ValidationException: Nếu file_path hoặc file_name không hợp lệ
        """
        if not file_path or not file_name:
            raise ValidationException(_("invalid_file_path_or_name"))

        try:
            logger.info(f"[CVIntegrationService] Extracting CV information from: {file_name} at path: {file_path}")

            # Download file content từ MinIO
            file_content = minio_handler.get_file_content(file_path)
            if not file_content:
                raise ValidationException(_("failed_to_get_file_content"))
                
            logger.info(f"[CVIntegrationService] Downloaded file content from MinIO: {file_path}")

            # Call N8N API using unified client
            result = await n8n_client.analyze_cv(file_content, file_name)
            logger.info(f"[CVIntegrationService] CV analysis completed for: {file_name}")

            return result

        except Exception as e:
            logger.error(f"[CVIntegrationService] Error extracting CV: {str(e)}")
            raise

    def _build_cv_context(self, cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build CV context dictionary from N8N API response
        
        Args:
            cv_analysis: Raw CV analysis from N8N API
            
        Returns:
            Structured CV context dictionary
        """
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

        return cv_context

    async def store_cv_context(self, conversation_id: str, user_id: str, cv_analysis: Dict[str, Any]):
        """
        Store CV context trong conversation metadata

        Args:
            conversation_id: ID của conversation
            user_id: ID của user
            cv_analysis: Kết quả phân tích CV từ N8N API

        Raises:
            NotFoundException: Nếu conversation không tồn tại
            ValidationException: Nếu input parameters không hợp lệ
        """
        if not conversation_id or not user_id:
            raise ValidationException(_("invalid_conversation_or_user_id"))

        if not cv_analysis:
            raise ValidationException(_("invalid_cv_analysis_data"))

        try:
            logger.info(f"[CVIntegrationService] Storing CV context for conversation: {conversation_id}")

            # Import here to avoid circular import
            from app.modules.chat.repository.chat_repo import ChatRepo

            chat_repo = ChatRepo(self.db_session)
            logger.debug("[CVIntegrationService] Initialized ChatRepo")

            # Get conversation
            conversation: Conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
            if not conversation:
                raise NotFoundException(_("conversation_not_found"))
                
            logger.debug(f"[CVIntegrationService] Retrieved conversation: {conversation.id}")

            # Build CV context from N8N API response
            cv_context = self._build_cv_context(cv_analysis)
            logger.debug(f"[CVIntegrationService] Built CV context with {len(cv_context)} fields")

            # Update conversation extra_metadata
            existing_metadata = json.loads(conversation.extra_metadata or '{}')
            existing_metadata['cv_context'] = cv_context

            conversation.extra_metadata = json.dumps(existing_metadata)
            self.db_session.commit()
            logger.info("[CVIntegrationService] CV context stored successfully")

        except Exception as e:
            logger.error(f"[CVIntegrationService] Error storing CV context: {str(e)}")
            self.db_session.rollback()
            raise

    def get_cv_context_for_prompt(self, conversation_id: str, user_id: str) -> Optional[str]:
        """
        Get CV information để add vào chat prompt

        Args:
            conversation_id: ID của conversation
            user_id: ID của user

        Returns:
            String context về CV information hoặc None nếu không có CV
        """
        if not conversation_id or not user_id:
            logger.warning("[CVIntegrationService] Missing conversation_id or user_id")
            return None

        try:
            logger.debug(f"[CVIntegrationService] Getting CV context for conversation: {conversation_id}")

            # Import here to avoid circular import
            from app.modules.chat.repository.chat_repo import ChatRepo

            chat_repo = ChatRepo(self.db_session)
            conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)

            if not conversation or not conversation.extra_metadata:
                logger.debug("[CVIntegrationService] No conversation or extra_metadata found")
                return None

            metadata = json.loads(conversation.extra_metadata)
            cv_context = metadata.get('cv_context')

            if not cv_context or not cv_context.get('cv_uploaded'):
                logger.debug("[CVIntegrationService] No CV context or CV not uploaded")
                return None

            # Format CV info cho prompt
            context_parts = self._build_context_parts(cv_context)

            if context_parts:
                logger.debug(f"[CVIntegrationService] Generated {len(context_parts)} context parts")
                return f'THÔNG TIN CV CỦA NGƯỜI DÙNG:\n{chr(10).join(context_parts)}\n---'

            logger.debug("[CVIntegrationService] No context parts generated")
            return None

        except Exception as e:
            logger.error(f"[CVIntegrationService] Error getting CV context: {str(e)}")
            return None

    def _build_context_parts(self, cv_context: Dict[str, Any]) -> List[str]:
        """
        Build context parts from CV context for prompt formatting
        
        Args:
            cv_context: CV context dictionary
            
        Returns:
            List of formatted context strings
        """
        context_parts = []

        # Personal info
        personal_info = cv_context.get('personal_info', {})
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
        if isinstance(skills, list) and skills:
            skills_text = ', '.join(skills[:10])  # Top 10 skills
            context_parts.append(f'Kỹ năng chính: {skills_text}')

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

        # Full analysis additional info
        full_analysis = cv_context.get('full_cv_analysis', {})
        if isinstance(full_analysis, dict):
            # Try to get summary from various possible keys
            summary_keys = ['summary', 'profile', 'objective', 'about']
            for key in summary_keys:
                if key in full_analysis and full_analysis[key]:
                    context_parts.append(f'Mô tả bản thân: {full_analysis[key]}')
                    break

        return context_parts