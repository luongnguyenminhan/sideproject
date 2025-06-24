"""
Example: Sử dụng Chat Workflow với User Context
Demonstrates how to pass user_id through the workflow to tools
"""

import asyncio
from typing import Optional
from sqlalchemy.orm import Session

from app.modules.agent.workflows.chat_workflow.workflow import Workflow
from app.modules.agent.workflows.chat_workflow.config.workflow_config import (
	WorkflowConfig,
)
from app.core.database import get_db


async def example_chat_with_user_context():
	"""Example sử dụng workflow với user context"""

	# Mock database session (replace with real one)
	db_session = next(get_db())  # Or your database session

	# Initialize workflow
	config = WorkflowConfig.from_env()
	workflow = Workflow(db_session=db_session, config=config)

	# Example 1: Basic chat với user_id
	print('🧑‍💼 Example 1: Basic chat with user context')
	user_id = 'user_123'
	conversation_id = 'conv_456'
	user_message = 'Tôi muốn tìm việc làm về AI'

	result = await workflow.process_message(
		user_message=user_message,
		user_id=user_id,
		conversation_id=conversation_id,
		timeout=30.0,
	)

	print(f'✅ Response: {result["response"]}')
	print(f'📊 Metadata: User ID = {result["metadata"]["user_id"]}')
	print(f'📊 Metadata: Conversation ID = {result["metadata"]["conversation_id"]}')

	# Example 2: CV analysis với user context
	print('\n📋 Example 2: CV analysis with user context')
	cv_message = 'Hãy phân tích CV của tôi và đưa ra câu hỏi phỏng vấn'

	result = await workflow.process_message(
		user_message=cv_message,
		user_id=user_id,
		conversation_id=conversation_id,
		timeout=30.0,
	)

	print(f'✅ Response: {result["response"]}')
	print(f'🔧 Tools used: {result["metadata"].get("features_used", {})}')

	# Example 3: RAG search với user context
	print('\n🔍 Example 3: RAG search with user context')
	rag_message = 'Enterview là gì? Có những tính năng gì?'

	result = await workflow.process_message(
		user_message=rag_message,
		user_id=user_id,
		conversation_id=conversation_id,
		timeout=30.0,
	)

	print(f'✅ Response: {result["response"]}')
	print(f'📚 RAG used: {result["metadata"]["rag_used"]}')

	db_session.close()


def example_state_user_context():
	"""Example sử dụng StateManager với user context"""
	from app.modules.agent.workflows.chat_workflow.state.workflow_state import (
		StateManager,
	)

	print('🏗️ Example: StateManager with user context')

	# Create initial state với user context
	state = StateManager.create_initial_state(
		user_message='Hello, I need help with job search',
		user_id='user_789',
		conversation_id='conv_101',
	)

	print(f'📊 State summary: {StateManager.get_state_summary(state)}')

	# Extract user context
	user_context = StateManager.get_user_context_for_tools(state)
	print(f'🧑‍💼 User context for tools: {user_context}')

	# Update user context
	updated_state = StateManager.update_user_context(state, user_id='updated_user_999', conversation_id='updated_conv_202')

	updated_context = StateManager.get_user_context_for_tools(updated_state)
	print(f'🔄 Updated user context: {updated_context}')


def example_socket_integration():
	"""Example integration với socket/API endpoint"""

	print('🔌 Example: Socket/API Integration Pattern')

	# Simulate socket message với user_id
	socket_data = {
		'message': 'Tôi cần tìm hiểu về kỹ năng phỏng vấn',
		'user_id': 'socket_user_123',
		'conversation_id': 'socket_conv_456',
		'session_id': 'socket_session_789',
	}

	print(f'📨 Received socket data: {socket_data}')

	# Example API handler pattern
	async def handle_socket_message(data):
		"""Example socket message handler"""
		try:
			# Extract user context
			user_id = data.get('user_id')
			conversation_id = data.get('conversation_id') or data.get('session_id')
			message = data.get('message')

			# Initialize workflow (would be done once, not per message)
			db_session = next(get_db())  # Your database session
			config = WorkflowConfig.from_env()
			workflow = Workflow(db_session=db_session, config=config)

			# Process message với user context
			result = await workflow.process_message(
				user_message=message,
				user_id=user_id,
				conversation_id=conversation_id,
				timeout=30.0,
			)

			# Prepare response for socket
			socket_response = {
				'response': result['response'],
				'user_id': user_id,
				'conversation_id': conversation_id,
				'metadata': {
					'processing_time': result['metadata']['processing_time'],
					'tools_used': result['metadata'].get('features_used', {}),
					'rag_used': result['metadata']['rag_used'],
				},
			}

			db_session.close()
			return socket_response

		except Exception as e:
			return {
				'error': str(e),
				'user_id': data.get('user_id'),
				'conversation_id': data.get('conversation_id'),
			}

	# Simulate handling
	async def simulate_handler():
		response = await handle_socket_message(socket_data)
		print(f'📤 Socket response: {response}')

	return simulate_handler


if __name__ == '__main__':
	print('🚀 Chat Workflow User Context Examples')
	print('=' * 50)

	# Run state example (synchronous)
	example_state_user_context()
	print()

	# Run socket integration example
	socket_handler = example_socket_integration()
	print()

	# Run async examples
	async def run_examples():
		await example_chat_with_user_context()
		print()
		await socket_handler()

	# asyncio.run(run_examples())
	print('✅ Examples completed! Uncomment the last line to run async examples.')
