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
from app.modules.cv_extraction.repository.cv_repo import CVRepo
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.exceptions.exception import ValidationException

logger = logging.getLogger(__name__)


def get_cv_profile_tool(db_session: Session):
	"""Factory function to create CV profile tool"""
	conversation_dal = ConversationDAL(db_session)
	cv_repo = CVRepo(db_session)

	@tool(return_direct=True)
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
				return 'Conversation not found'  # Update extra_metadata with CV data
			cv_analysis_data = result.data.cv_analysis_result
			if hasattr(cv_analysis_data, 'model_dump'):
				cv_analysis_dict = cv_analysis_data.model_dump()
			elif hasattr(cv_analysis_data, 'dict'):
				cv_analysis_dict = cv_analysis_data.dict()
			else:
				cv_analysis_dict = cv_analysis_data

			cv_data = {
				'cv_profile': {
					'cv_file_url': cv_file_url,
					'analysis_result': cv_analysis_dict,
					'updated_at': str(datetime.now()),
				}
			}

			# Merge with existing metadata
			existing_metadata = {}
			if conversation.extra_metadata:
				existing_metadata = json.loads(conversation.extra_metadata)

			existing_metadata.update(cv_data)

			# Update conversation
			conversation.extra_metadata = json.dumps(existing_metadata)
			db_session.commit()

			return 'CV profile updated successfully in conversation metadata'

		except ValidationException as e:
			logger.error(f'Validation error updating CV profile: {e}')
			return f'Validation error: {str(e)}'
		except json.JSONDecodeError as e:
			logger.error(f'JSON decode error updating CV profile: {e}')
			return f'Error parsing conversation metadata: {str(e)}'
		except Exception as e:
			logger.error(f'Error updating CV profile: {e}')
			return f'Error updating CV profile: {str(e)}'

	return update_cv_profile
