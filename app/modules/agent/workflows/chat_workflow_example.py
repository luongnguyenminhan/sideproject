"""
Example usage của modular Chat Workflow
Demonstration của QdrantService integration và advanced features
"""

import asyncio
import logging
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.agent.workflows.chat_workflow import ChatWorkflow, WorkflowConfig, create_chat_workflow

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
	"""Basic usage example"""

	# Get database session
	db = next(get_db())

	try:
		# Create workflow với default config
		workflow = create_chat_workflow(db_session=db)

		# Process a financial question
		result = await workflow.process_message(user_message='Lãi suất tiết kiệm ngân hàng hiện tại như thế nào?', user_id='user_123', session_id='session_456')

		print('Response:', result['response'])
		print('Metadata:', result['metadata'])

	finally:
		db.close()


async def example_custom_config():
	"""Example với custom configuration"""

	# Create custom config
	config = WorkflowConfig(model_name='gemini-2.0-flash', temperature=0.1, rag_enabled=True, similarity_threshold=0.8, max_retrieved_docs=3, collection_name='financial_knowledge')

	db = next(get_db())

	try:
		# Create workflow với custom config
		workflow = ChatWorkflow(db_session=db, config=config)

		# Process investment question
		result = await workflow.process_message(user_message='So sánh đầu tư cổ phiếu và trái phiếu ở Việt Nam', config_override={'use_rag': True, 'max_retrieved_docs': 5})

		print('Response:', result['response'])
		print('RAG used:', result['metadata']['rag_used'])
		print('Documents retrieved:', result['metadata']['documents_retrieved'])

	finally:
		db.close()


async def example_health_monitoring():
	"""Example health monitoring"""

	db = next(get_db())

	try:
		workflow = create_chat_workflow(db_session=db)

		# Check health
		health = await workflow.health_check()
		print('Health Status:', health['status'])

		# Get workflow info
		info = workflow.get_workflow_info()
		print('Workflow Info:', info['name'], info['version'])

	finally:
		db.close()


async def example_conversation_flow():
	"""Example conversation flow"""

	db = next(get_db())

	try:
		workflow = create_chat_workflow(db_session=db)

		# Multi-turn conversation
		messages = ['Tôi muốn tìm hiểu về đầu tư', 'Cổ phiếu có rủi ro gì?', 'Làm sao để giảm thiểu rủi ro?']

		session_id = 'conversation_example'

		for i, message in enumerate(messages):
			print(f'\n--- Turn {i + 1} ---')
			print(f'User: {message}')

			result = await workflow.process_message(user_message=message, user_id='demo_user', session_id=session_id)

			print(f'Assistant: {result["response"]}')
			print(f'Processing time: {result["metadata"]["processing_time"]:.2f}s')

	finally:
		db.close()


async def example_error_handling():
	"""Example error handling"""

	db = next(get_db())

	try:
		# Invalid config để test error handling
		config = WorkflowConfig(
			api_key='invalid_key',  # This will cause errors
			model_name='invalid_model',
		)

		workflow = ChatWorkflow(db_session=db, config=config)

		# This should handle errors gracefully
		result = await workflow.process_message(user_message='Test error handling')

		print('Response:', result['response'])
		print('Error occurred:', result.get('metadata', {}).get('error_occurred', False))

	finally:
		db.close()


def run_examples():
	"""Run all examples"""

	print('🚀 Running Chat Workflow Examples\n')

	examples = [
		('Basic Usage', example_basic_usage),
		('Custom Config', example_custom_config),
		('Health Monitoring', example_health_monitoring),
		('Conversation Flow', example_conversation_flow),
		('Error Handling', example_error_handling),
	]

	for name, example_func in examples:
		print(f'\n{"=" * 50}')
		print(f'📝 Example: {name}')
		print('=' * 50)

		try:
			asyncio.run(example_func())
			print(f'✅ {name} completed successfully')

		except Exception as e:
			print(f'❌ {name} failed: {str(e)}')


if __name__ == '__main__':
	run_examples()
