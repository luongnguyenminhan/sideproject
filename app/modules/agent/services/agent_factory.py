from typing import Dict, Any, List, TYPE_CHECKING
from app.modules.agent.models.agent import Agent, AgentType
from app.modules.agent.models.agent_config import AgentConfig, ModelProvider
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _

if TYPE_CHECKING:
	from app.modules.agent.repository.agent_repo import AgentRepo


class AgentFactory:
	"""Factory for creating and configuring agents with default settings"""

	DEFAULT_CONFIGS = {
		AgentType.CHAT: {
			'name': 'Default Chat Agent',
			'description': 'General-purpose conversational AI assistant',
			'model_provider': ModelProvider.GOOGLE,
			'model_name': 'gemini-2.0-flash',
			'temperature': 0.7,
			'max_tokens': 2048,
			'system_prompt': """You are a helpful AI assistant. You provide accurate, helpful, and friendly responses to user questions. 
You maintain context throughout the conversation and adapt your responses to the user's needs.""",
			'tools_config': {'web_search': False, 'memory_retrieval': True, 'custom_tools': []},
			'workflow_config': {'type': 'conversational', 'memory_enabled': True, 'context_window': 10},
		},
		AgentType.ANALYSIS: {
			'name': 'Data Analysis Agent',
			'description': 'Specialized AI for data analysis and insights',
			'model_provider': ModelProvider.GOOGLE,
			'model_name': 'gemini-2.0-flash',
			'temperature': 0.3,
			'max_tokens': 4096,
			'system_prompt': """You are a data analysis specialist. You help users understand data, create insights, 
and provide analytical recommendations. You focus on accuracy and clarity in your explanations.""",
			'tools_config': {'web_search': True, 'memory_retrieval': True, 'custom_tools': ['data_visualization', 'statistical_analysis']},
			'workflow_config': {'type': 'analytical', 'memory_enabled': True, 'context_window': 20},
		},
		AgentType.TASK: {
			'name': 'Task Assistant Agent',
			'description': 'AI assistant for task management and productivity',
			'model_provider': ModelProvider.GOOGLE,
			'model_name': 'gemini-2.0-flash',
			'temperature': 0.5,
			'max_tokens': 2048,
			'system_prompt': """You are a task management assistant. You help users organize, prioritize, 
and complete tasks efficiently. You provide structured and actionable guidance.""",
			'tools_config': {'web_search': False, 'memory_retrieval': True, 'custom_tools': ['task_scheduling', 'reminder_setting']},
			'workflow_config': {'type': 'task_oriented', 'memory_enabled': True, 'context_window': 15},
		},
	}

	@classmethod
	def create_default_agent(cls, agent_type: AgentType, user_id: str, agent_repo: 'AgentRepo', custom_name: str = None) -> Agent:
		"""Create agent with default configuration for specified type"""

		if agent_type not in cls.DEFAULT_CONFIGS:
			raise ValidationException(_('unsupported_agent_type'))


		# Get default config for agent type
		default_config = cls.DEFAULT_CONFIGS[agent_type].copy()

		# Use custom name if provided
		if custom_name:
			default_config['name'] = custom_name
		else:
			pass
		# Create or get existing default config
		config = cls._get_or_create_default_config(agent_type, default_config, agent_repo)

		# Create agent
		agent_name = custom_name or f'{default_config["name"]} - {user_id[:8]}'

		agent = agent_repo.create_agent(user_id=user_id, name=agent_name, agent_type=agent_type, config_id=config.id, description=default_config['description'])

		return agent

	@classmethod
	def create_custom_agent(cls, agent_type: AgentType, user_id: str, agent_repo: 'AgentRepo', custom_config: Dict[str, Any], agent_name: str) -> Agent:
		"""Create agent with custom configuration"""

		# Validate custom config
		validated_config = cls._validate_custom_config(agent_type, custom_config)

		# Create custom config
		config = cls._create_custom_config(agent_type, validated_config, agent_repo)

		# Create agent
		description = custom_config.get('description', f'Custom {agent_type.value} agent')

		agent = agent_repo.create_agent(user_id=user_id, name=agent_name, agent_type=agent_type, config_id=config.id, description=description)

		return agent

	@classmethod
	def get_default_config_template(cls, agent_type: AgentType) -> Dict[str, Any]:
		"""Get default configuration template for agent type"""

		if agent_type not in cls.DEFAULT_CONFIGS:
			raise ValidationException(_('unsupported_agent_type'))

		template = cls.DEFAULT_CONFIGS[agent_type].copy()
		return template

	@classmethod
	def list_available_models(cls) -> Dict[str, List[str]]:
		"""List available models by provider"""
		models = {
			ModelProvider.GOOGLE.value: ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash'],
		}
		return models

	@classmethod
	def validate_model_compatibility(cls, provider: ModelProvider, model_name: str) -> bool:
		"""Validate if model is compatible with provider"""

		available_models = cls.list_available_models()
		compatible = model_name in available_models.get(provider.value, [])

		return compatible

	@classmethod
	def _get_or_create_default_config(cls, agent_type: AgentType, default_config: Dict[str, Any], agent_repo: 'AgentRepo') -> AgentConfig:
		"""Get existing default config or create new one"""

		try:
			# Try to find existing default config
			config_name = f'default_{agent_type.value}_config'

			existing_config = agent_repo.config_dal.get_config_by_name(config_name)

			if existing_config:
				return existing_config


			# Create new default config
			config_data = {
				'name': f'default_{agent_type.value}_config',
				'description': f'Default configuration for {agent_type.value} agents',
				'agent_type': agent_type.value,
				'model_provider': default_config['model_provider'],
				'model_name': default_config['model_name'],
				'temperature': default_config['temperature'],
				'max_tokens': default_config['max_tokens'],
				'system_prompt': default_config['system_prompt'],
				'tools_config': default_config['tools_config'],
				'workflow_config': default_config['workflow_config'],
				'memory_config': {'short_term_limit': 100, 'long_term_limit': 500, 'importance_threshold': 0.7},
			}


			created_config = agent_repo.config_dal.create(config_data)

			if not created_config:
				raise ValidationException(_('failed_to_create_default_config'))

			return created_config

		except Exception as e:
			raise ValidationException(f'{_("error_creating_default_config")}: {str(e)}')

	@classmethod
	def _create_custom_config(cls, agent_type: AgentType, custom_config: Dict[str, Any], agent_repo: 'AgentRepo') -> AgentConfig:
		"""Create custom configuration"""

		config_data = {
			'name': custom_config.get('name', f'custom_{agent_type.value}_config'),
			'description': custom_config.get('description', f'Custom {agent_type.value} configuration'),
			'agent_type': agent_type.value,
			'model_provider': custom_config['model_provider'],
			'model_name': custom_config['model_name'],
			'temperature': custom_config.get('temperature', 0.7),
			'max_tokens': custom_config.get('max_tokens', 2048),
			'system_prompt': custom_config.get('system_prompt', ''),
			'tools_config': custom_config.get('tools_config', {}),
			'workflow_config': custom_config.get('workflow_config', {}),
			'memory_config': custom_config.get('memory_config', {'short_term_limit': 100, 'long_term_limit': 500, 'importance_threshold': 0.7}),
		}


		config = agent_repo.config_dal.create(config_data)

		return config

	@classmethod
	def _validate_custom_config(cls, agent_type: AgentType, custom_config: Dict[str, Any]) -> Dict[str, Any]:
		"""Validate custom configuration"""

		# Required fields
		required_fields = ['model_provider', 'model_name']

		for field in required_fields:
			if field not in custom_config:
				raise ValidationException(f'{_("missing_required_field")}: {field}')
			print(f"\033[96m[DEBUG] Required field '{field}' found: {custom_config[field]}\033[0m")

		# Validate model provider
		try:
			provider = ModelProvider(custom_config['model_provider'])
		except ValueError:
			raise ValidationException(_('invalid_model_provider'))

		# Validate model compatibility
		if not cls.validate_model_compatibility(provider, custom_config['model_name']):
			raise ValidationException(_('invalid_model_for_provider'))

		# Validate temperature
		temperature = custom_config.get('temperature', 0.7)
		if not 0 <= temperature <= 2:
			raise ValidationException(_('invalid_temperature_range'))

		# Validate max_tokens
		max_tokens = custom_config.get('max_tokens', 2048)
		if not 1 <= max_tokens <= 32000:
			raise ValidationException(_('invalid_max_tokens_range'))

		return custom_config
