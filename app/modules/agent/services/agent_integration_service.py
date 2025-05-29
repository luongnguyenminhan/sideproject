from typing import Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from app.modules.agent.repository.agent_repo import AgentRepo
from app.modules.agent.repository.agent_workflow_repo import AgentWorkflowRepo
from app.modules.agent.services.workflow_manager import WorkflowManager
from app.modules.agent.models.agent import Agent, AgentType
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
import time
import json


class AgentIntegrationService:
	"""Service to integrate agents with existing chat system"""

	def __init__(self, db: Session):
		self.db = db
		self.agent_repo = AgentRepo(db)
		self.workflow_repo = AgentWorkflowRepo(db)
		self.workflow_manager = WorkflowManager()

	async def get_ai_response(self, conversation_id: str, user_message: str, user_id: str, api_key: str = None) -> Dict[str, Any]:
		"""Get AI response using agent system (non-streaming)"""

		# Get or create default agent for user
		agent = self.agent_repo.get_or_create_default_agent(user_id)

		# Execute workflow
		result = await self.workflow_repo.execute_chat_workflow(agent_id=agent.id, user_id=user_id, conversation_id=conversation_id, user_message=user_message, api_key=api_key)

		return {
			'content': result['content'],
			'model_used': result['metadata'].get('model_used', 'agent-system'),
			'usage': {
				'total_tokens': result['metadata'].get('tokens_used', 0),
				'prompt_tokens': 0,  # Not tracked separately yet
				'completion_tokens': result['metadata'].get('tokens_used', 0),
			},
			'response_time_ms': result['metadata'].get('execution_time_ms', 0),
			'agent_id': agent.id,
			'agent_name': agent.name,
		}

	async def get_ai_response_streaming(self, conversation_id: str, user_message: str, user_id: str, api_key: str = None, websocket_manager=None) -> Dict[str, Any]:
		"""Get AI response using agent system with streaming"""

		# Get or create default agent for user
		agent = self.agent_repo.get_or_create_default_agent(user_id)

		start_time = time.time()
		full_content = ''
		total_tokens = 0

		try:
			# Execute streaming workflow
			async for chunk in self.workflow_repo.execute_streaming_workflow(agent_id=agent.id, user_id=user_id, conversation_id=conversation_id, user_message=user_message, api_key=api_key):
				if chunk.get('type') == 'content':
					content_chunk = chunk.get('content', '')
					full_content += content_chunk

					# Send streaming chunk via WebSocket
					if websocket_manager and user_id:
						await websocket_manager.send_message(user_id, {'type': 'assistant_message_chunk', 'content': content_chunk, 'full_content': full_content, 'agent_id': agent.id})

				elif chunk.get('type') == 'metadata':
					metadata = chunk.get('data', {})
					total_tokens = metadata.get('tokens_used', 0)

				elif chunk.get('type') == 'error':
					# Send error via WebSocket
					if websocket_manager and user_id:
						await websocket_manager.send_message(user_id, {'type': 'error', 'message': chunk.get('message', 'Workflow execution failed')})
					raise ValidationException(chunk.get('message', 'Workflow execution failed'))

			response_time = int((time.time() - start_time) * 1000)

			return {
				'content': full_content,
				'model_used': f'agent-{agent.agent_type.value}',
				'usage': {'total_tokens': total_tokens, 'prompt_tokens': 0, 'completion_tokens': total_tokens},
				'response_time_ms': response_time,
				'agent_id': agent.id,
				'agent_name': agent.name,
			}

		except Exception as e:
			# Send error via WebSocket if available
			if websocket_manager and user_id:
				await websocket_manager.send_message(user_id, {'type': 'error', 'message': f'Agent error: {str(e)}'})
			raise

	def get_user_agent(self, user_id: str, agent_id: str = None) -> Agent:
		"""Get specific agent or default agent for user"""
		if agent_id:
			return self.agent_repo.get_agent_by_id(agent_id, user_id)
		else:
			return self.agent_repo.get_or_create_default_agent(user_id)

	def set_user_default_agent(self, user_id: str, agent_id: str) -> Agent:
		"""Set user's default agent"""
		# Verify user owns the agent
		agent = self.agent_repo.get_agent_by_id(agent_id, user_id)

		# For now, we'll just return the agent
		# In the future, we might store this preference in a user settings table
		return agent

	async def test_agent_response(self, agent_id: str, user_id: str, test_message: str, api_key: str = None) -> Dict[str, Any]:
		"""Test agent response without saving to conversation"""

		agent, config = self.agent_repo.get_agent_with_config(agent_id, user_id)

		# Prepare test context
		context = {
			'agent': {'id': agent.id, 'name': agent.name, 'type': agent.agent_type.value},
			'config': {
				'model_provider': config.model_provider.value,
				'model_name': config.model_name,
				'temperature': config.temperature,
				'max_tokens': config.max_tokens,
				'system_prompt': config.system_prompt,
				'tools_config': config.tools_config or {},
				'workflow_config': config.workflow_config or {},
			},
			'user_message': test_message,
			'conversation_history': [],
			'important_context': [],
			'is_test': True,
		}

		# Execute workflow
		result = await self.workflow_manager.execute_workflow(agent=agent, config=config, context=context, api_key=api_key)

		return {
			'content': result['content'],
			'model_used': result['metadata'].get('model_used', 'agent-system'),
			'execution_time_ms': result['metadata'].get('execution_time_ms', 0),
			'tokens_used': result['metadata'].get('tokens_used', 0),
			'agent_id': agent.id,
			'agent_name': agent.name,
			'success': True,
		}

	def get_agent_conversation_context(self, agent_id: str, user_id: str, conversation_id: str) -> Dict[str, Any]:
		"""Get agent's context for a specific conversation"""

		# Verify user owns agent
		agent = self.agent_repo.get_agent_by_id(agent_id, user_id)

		# Get memory context
		context = self.workflow_repo.get_agent_memory_context(agent_id=agent_id, conversation_id=conversation_id)

		return {'agent': {'id': agent.id, 'name': agent.name, 'type': agent.agent_type.value, 'is_active': agent.is_active}, 'memory_context': context, 'conversation_id': conversation_id}

	def clear_agent_conversation_memory(self, agent_id: str, user_id: str, conversation_id: str) -> int:
		"""Clear agent memory for specific conversation"""

		# Verify user owns agent
		self.agent_repo.get_agent_by_id(agent_id, user_id)

		# Clear conversation memories
		return self.workflow_repo.memory_dal.clear_conversation_memories(agent_id, conversation_id)

	def get_agent_statistics(self, agent_id: str, user_id: str) -> Dict[str, Any]:
		"""Get agent usage statistics"""

		# Verify user owns agent
		agent = self.agent_repo.get_agent_by_id(agent_id, user_id)

		# Get memory counts
		memories = self.workflow_repo.memory_dal.get_memories_by_agent(agent_id, limit=1000)

		memory_stats = {
			'total_memories': len(memories),
			'conversation_memories': len([m for m in memories if m.conversation_id]),
			'important_memories': len([m for m in memories if m.importance_score >= 0.7]),
		}

		# Get workflow state
		workflow_memories = self.workflow_repo.memory_dal.get_memories_by_agent(agent_id, memory_type=self.workflow_repo.memory_dal.model.MemoryType.WORKFLOW_STATE, limit=1)

		workflow_state = workflow_memories[0].content if workflow_memories else {}

		return {
			'agent_id': agent.id,
			'agent_name': agent.name,
			'agent_type': agent.agent_type.value,
			'is_active': agent.is_active,
			'memory_statistics': memory_stats,
			'conversation_count': workflow_state.get('conversation_count', 0),
			'last_interaction': workflow_state.get('last_interaction'),
			'created_date': agent.create_date.isoformat() if agent.create_date else None,
			'uptime_days': (agent.update_date - agent.create_date).days if agent.create_date and agent.update_date else 0,
		}
