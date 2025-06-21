"""
CV Profile update tool for chat workflow
"""

import json
import logging
import asyncio
from datetime import datetime
from langchain_core.tools import tool
from sqlalchemy.orm import Session
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.cv_extraction.repository.cv_repo import CVRepository
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest

logger = logging.getLogger(__name__)


def get_cv_profile_tool(db_session: Session):
	"""Factory function to create CV profile tool"""
	conversation_dal = ConversationDAL(db_session)
	cv_repo = CVRepository()

	@tool(return_direct=False)
	def update_cv_profile(conversation_id: str, cv_file_url: str) -> str:
		"""Update user CV profile in conversation metadata by processing CV file."""
		try:
			# Process CV file using asyncio
			request = ProcessCVRequest(cv_file_url=cv_file_url)
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			result = loop.run_until_complete(cv_repo.process_cv(request))
			loop.close()

			if result.error_code != 0:
				return f'Failed to process CV: {result.message}'

			# Get conversation
			conversation = conversation_dal.get_by_id(conversation_id)
			if not conversation:
				return 'Conversation not found'

			# Update extra_metadata with CV data
			cv_data = {
				'cv_profile': {
					'cv_file_url': cv_file_url,
					'extracted_text': result.data.get('extracted_text', ''),
					'analysis_result': result.data.get('cv_analysis_result', {}),
					'updated_at': str(datetime.now()),
				}
			}

			# Merge with existing metadata
			existing_metadata = {}
			if conversation.extra_metadata:
				try:
					existing_metadata = json.loads(conversation.extra_metadata)
				except json.JSONDecodeError:
					existing_metadata = {}

			existing_metadata.update(cv_data)

			# Update conversation
			conversation.extra_metadata = json.dumps(existing_metadata)
			db_session.commit()

			return 'CV profile updated successfully in conversation metadata'

		except Exception as e:
			logger.error(f'Error updating CV profile: {e}')
			return f'Error updating CV profile: {str(e)}'

	return update_cv_profile
