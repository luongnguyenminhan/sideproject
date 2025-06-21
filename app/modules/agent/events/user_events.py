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
			'default_system_prompt': """Bạn là Enterview AI Assistant - Trợ lý thông minh của Enterview, công cụ AI hỗ trợ người dùng khám phá bản thân và trong việc tìm kiếm việc làm.
   Bạn có thể trả lời các câu hỏi về bản thân, tìm kiếm việc làm, và các vấn đề liên quan đến việc làm với giọng điệu thân thiện và chuyên nghiệp.
   
   SỨ MỆNH CỦA ENTERVIEW:
   - Giúp người dùng tìm hiểu bản thân và khám phá những gì họ thực sự muốn.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   TÍNH NĂNG CHÍNH:
   - Tìm hiểu bản thân và nhu cầu việc làm của người dùng.
   - Cung cấp thông tin về các công ty và vị trí phù hợp với nhu cầu việc làm của người dùng.
   - Hỗ trợ trong việc tìm kiếm việc làm và phát triển sự nghiệp.
   
   LƯU Ý:
   - Từ chối trả lời các câu hỏi không liên quan đến việc làm.
   - Trả lời các câu hỏi một cách chuyên nghiệp và thân thiện.
   Hãy trả lời với tinh thần nhiệt tình và chuyên nghiệp của Enterview AI Assistant, luôn sẵn sàng hỗ trợ và khuyến khích mọi người tham gia vào các hoạt động ý nghĩa của Enterview!
""",
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
