"""Event handlers for user-related events in the agent module"""

import logging
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.agent.dal.agent_dal import AgentDAL
from app.modules.agent.models.agent import ModelProvider

logger = logging.getLogger(__name__)


def handle_user_created_event(user_id: str, email: str, username: str, **kwargs):
	"""
	Handle user creation event by creating a default agent for the new user

	Args:
	    user_id (str): ID of the newly created user
	    email (str): User's email address
	    username (str): User's username
	    **kwargs: Additional event data
	"""
	logger.info(f'Handling user_created event for user {user_id}')

	db = None
	try:
		# Get database session
		db = next(get_db())
		agent_dal = AgentDAL(db)

		# Create default agent for the new user
		default_agent_data = {
			'name': f"{username}'s Personal Assistant",
			'description': 'Your personal AI assistant',
			'user_id': user_id,  # Associate agent with user
			'is_active': True,
			'model_provider': ModelProvider.GOOGLE,
			'model_name': 'gemini-2.0-flash',
			'temperature': 0.7,
			'max_tokens': 2048,
			'default_system_prompt': """You are CGSEM Bot, the official AI assistant for CLB Truyền thông và Sự Kiện trường THPT Cần Giuộc (CGSEM). You represent a non-profit media and events organization established on December 14, 2020, dedicated to providing healthy recreational activities and diverse professional experiences.

Your identity is rooted in CGSEM's core principles:
- **Cụ thể (Specific)**: Focus on practical, real-world experiences tied to career guidance and personal interests
- **Đa dạng (Diverse)**: Embrace creativity and variety in all activities and thinking
- **Văn minh (Civilized)**: Prioritize human values and safe, healthy social development
- **Công bằng (Fair)**: Maintain independence and provide equal opportunities for all

You embody the spirit of pioneering youth who maximize their potential for community and society. You are knowledgeable about CGSEM's achievements, including recognition from local government and partnerships with youth events in Long An province.

Respond in a friendly, professional manner that reflects the organization's innovative, responsible, and creative values. Always maintain the motto: "tiên quyết, tiên phong, sáng tạo" (prerequisite, pioneering, creative).""",
			'tools_config': {
				'web_search': False,
				'memory_retrieval': True,
				'custom_tools': [],
			},
			'api_provider': 'google',
			'api_key': None,  # User will set this later
		}

		# Create the agent in a separate transaction
		with agent_dal.transaction():
			agent = agent_dal.create(default_agent_data)
			db.commit()

		logger.info(f'Successfully created default agent {agent.id} for user {user_id}')

	except Exception as e:
		logger.error(f'Failed to create default agent for user {user_id}: {e}')
		# Don't raise the exception - user creation should not fail due to agent creation issues
		if db:
			try:
				db.rollback()
			except:
				pass

	finally:
		if db:
			try:
				db.close()
			except:
				pass
