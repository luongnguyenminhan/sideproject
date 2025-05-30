from typing import Dict, Any, List, TYPE_CHECKING
from app.modules.agent.models.agent import Agent, AgentType
from app.modules.agent.models.agent_config import AgentConfig, ModelProvider
from app.exceptions.exception import ValidationException
from app.middleware.translation_manager import _
import logging

logger = logging.getLogger(__name__)
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
		logger.debug('\033[92m[DEBUG] AgentFactory.create_default_agent() - ENTRY\033[0m')
		logger.debug(f'\033[94m[DEBUG] Parameters: agent_type={agent_type}, user_id={user_id}, custom_name={custom_name}\033[0m')

		if agent_type not in cls.DEFAULT_CONFIGS:
			logger.debug(f'\033[91m[DEBUG] ERROR: Unsupported agent type: {agent_type}\033[0m')
			raise ValidationException(_('unsupported_agent_type'))

		logger.debug(f'\033[93m[DEBUG] Agent type {agent_type} found in DEFAULT_CONFIGS\033[0m')

		# Get default config for agent type
		default_config = cls.DEFAULT_CONFIGS[agent_type].copy()
		logger.debug(f'\033[96m[DEBUG] Retrieved default config: {default_config["name"]}\033[0m')

		# Use custom name if provided
		if custom_name:
			logger.debug(f'\033[95m[DEBUG] Using custom name: {custom_name}\033[0m')
			default_config['name'] = custom_name
		else:
			logger.debug(f'\033[95m[DEBUG] No custom name provided, using default: {default_config["name"]}\033[0m')

		# Create or get existing default config
		logger.debug('\033[93m[DEBUG] Calling _get_or_create_default_config()\033[0m')
		config = cls._get_or_create_default_config(agent_type, default_config, agent_repo)
		logger.debug(f'\033[92m[DEBUG] Config created/retrieved with ID: {config.id}\033[0m')

		# Create agent
		agent_name = custom_name or f'{default_config["name"]} - {user_id[:8]}'
		logger.debug(f'\033[94m[DEBUG] Final agent name: {agent_name}\033[0m')
		logger.debug(f'\033[94m[DEBUG] Agent description: {default_config["description"]}\033[0m')

		logger.debug('\033[93m[DEBUG] Calling agent_repo.create_agent()\033[0m')
		agent = agent_repo.create_agent(user_id=user_id, name=agent_name, agent_type=agent_type, config_id=config.id, description=default_config['description'])
		logger.debug(f'\033[92m[DEBUG] Agent created successfully with ID: {agent.id}\033[0m')
		logger.debug('\033[92m[DEBUG] AgentFactory.create_default_agent() - EXIT\033[0m')

		return agent

	@classmethod
	def create_custom_agent(cls, agent_type: AgentType, user_id: str, agent_repo: 'AgentRepo', custom_config: Dict[str, Any], agent_name: str) -> Agent:
		"""Create agent with custom configuration"""
		logger.debug('\033[92m[DEBUG] AgentFactory.create_custom_agent() - ENTRY\033[0m')
		logger.debug(f'\033[94m[DEBUG] Parameters: agent_type={agent_type}, user_id={user_id}, agent_name={agent_name}\033[0m')
		logger.debug(f'\033[94m[DEBUG] Custom config keys: {list(custom_config.keys())}\033[0m')

		# Validate custom config
		logger.debug('\033[93m[DEBUG] Validating custom config\033[0m')
		validated_config = cls._validate_custom_config(agent_type, custom_config)
		logger.debug('\033[92m[DEBUG] Custom config validation passed\033[0m')

		# Create custom config
		logger.debug('\033[93m[DEBUG] Creating custom config\033[0m')
		config = cls._create_custom_config(agent_type, validated_config, agent_repo)
		logger.debug(f'\033[92m[DEBUG] Custom config created with ID: {config.id}\033[0m')

		# Create agent
		description = custom_config.get('description', f'Custom {agent_type.value} agent')
		logger.debug(f'\033[94m[DEBUG] Agent description: {description}\033[0m')

		logger.debug('\033[93m[DEBUG] Calling agent_repo.create_agent() for custom agent\033[0m')
		agent = agent_repo.create_agent(user_id=user_id, name=agent_name, agent_type=agent_type, config_id=config.id, description=description)
		logger.debug(f'\033[92m[DEBUG] Custom agent created successfully with ID: {agent.id}\033[0m')
		logger.debug('\033[92m[DEBUG] AgentFactory.create_custom_agent() - EXIT\033[0m')

		return agent

	@classmethod
	def get_default_config_template(cls, agent_type: AgentType) -> Dict[str, Any]:
		"""Get default configuration template for agent type"""
		logger.debug(f'\033[92m[DEBUG] AgentFactory.get_default_config_template() - agent_type={agent_type}\033[0m')

		if agent_type not in cls.DEFAULT_CONFIGS:
			logger.debug(f'\033[91m[DEBUG] ERROR: Unsupported agent type in template: {agent_type}\033[0m')
			raise ValidationException(_('unsupported_agent_type'))

		template = cls.DEFAULT_CONFIGS[agent_type].copy()
		logger.debug(f'\033[94m[DEBUG] Returning template for {agent_type}: {template["name"]}\033[0m')
		return template

	@classmethod
	def list_available_models(cls) -> Dict[str, List[str]]:
		"""List available models by provider"""
		logger.debug('\033[92m[DEBUG] AgentFactory.list_available_models() - ENTRY\033[0m')
		models = {
			ModelProvider.GOOGLE.value: ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-flash'],
		}
		logger.debug(f'\033[94m[DEBUG] Available models: {models}\033[0m')
		return models

	@classmethod
	def validate_model_compatibility(cls, provider: ModelProvider, model_name: str) -> bool:
		"""Validate if model is compatible with provider"""
		logger.debug(f'\033[92m[DEBUG] AgentFactory.validate_model_compatibility() - provider={provider}, model={model_name}\033[0m')

		available_models = cls.list_available_models()
		compatible = model_name in available_models.get(provider.value, [])

		logger.debug(f'\033[94m[DEBUG] Model compatibility result: {compatible}\033[0m')
		return compatible

	@classmethod
	def _get_or_create_default_config(cls, agent_type: AgentType, default_config: Dict[str, Any], agent_repo: 'AgentRepo') -> AgentConfig:
		"""Get existing default config or create new one"""
		logger.debug('\033[92m[DEBUG] AgentFactory._get_or_create_default_config() - ENTRY\033[0m')
		logger.debug(f'\033[94m[DEBUG] Looking for config: default_{agent_type.value}_config\033[0m')

		try:
			# Try to find existing default config
			config_name = f'default_{agent_type.value}_config'
			logger.debug(f'\033[93m[DEBUG] Searching for existing config: {config_name}\033[0m')

			existing_config = agent_repo.config_dal.get_config_by_name(config_name)

			if existing_config:
				logger.debug(f'\033[92m[DEBUG] Found existing config with ID: {existing_config.id}\033[0m')
				return existing_config

			logger.debug('\033[93m[DEBUG] No existing config found, creating new default config\033[0m')

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

			logger.debug(f'\033[96m[DEBUG] Config data prepared: name={config_data["name"]}, provider={config_data["model_provider"]}, model={config_data["model_name"]}\033[0m')
			logger.debug(f'\033[96m[DEBUG] Temperature: {config_data["temperature"]}, Max tokens: {config_data["max_tokens"]}\033[0m')

			logger.debug('\033[93m[DEBUG] Calling agent_repo.config_dal.create()\033[0m')
			created_config = agent_repo.config_dal.create(config_data)

			if not created_config:
				logger.debug('\033[91m[DEBUG] ERROR: Failed to create default config - config_dal.create() returned None\033[0m')
				raise ValidationException(_('failed_to_create_default_config'))

			logger.debug(f'\033[92m[DEBUG] Default config created successfully with ID: {created_config.id}\033[0m')
			logger.debug('\033[92m[DEBUG] AgentFactory._get_or_create_default_config() - EXIT\033[0m')
			return created_config

		except Exception as e:
			logger.debug(f'\033[91m[DEBUG] ERROR in _get_or_create_default_config(): {str(e)}\033[0m')
			logger.debug(f'\033[91m[DEBUG] Exception type: {type(e).__name__}\033[0m')
			raise ValidationException(f'{_("error_creating_default_config")}: {str(e)}')

	@classmethod
	def _create_custom_config(cls, agent_type: AgentType, custom_config: Dict[str, Any], agent_repo: 'AgentRepo') -> AgentConfig:
		"""Create custom configuration"""
		logger.debug('\033[92m[DEBUG] AgentFactory._create_custom_config() - ENTRY\033[0m')
		logger.debug(f'\033[94m[DEBUG] Agent type: {agent_type}\033[0m')

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

		logger.debug(f'\033[96m[DEBUG] Custom config data: name={config_data["name"]}, provider={config_data["model_provider"]}\033[0m')
		logger.debug(f'\033[96m[DEBUG] Model: {config_data["model_name"]}, Temperature: {config_data["temperature"]}\033[0m')

		logger.debug('\033[93m[DEBUG] Calling agent_repo.config_dal.create() for custom config\033[0m')
		config = agent_repo.config_dal.create(config_data)
		logger.debug(f'\033[92m[DEBUG] Custom config created with ID: {config.id}\033[0m')
		logger.debug('\033[92m[DEBUG] AgentFactory._create_custom_config() - EXIT\033[0m')

		return config

	@classmethod
	def _validate_custom_config(cls, agent_type: AgentType, custom_config: Dict[str, Any]) -> Dict[str, Any]:
		"""Validate custom configuration"""
		logger.debug('\033[92m[DEBUG] AgentFactory._validate_custom_config() - ENTRY\033[0m')
		logger.debug(f'\033[94m[DEBUG] Validating config for agent type: {agent_type}\033[0m')
		logger.debug(f'\033[94m[DEBUG] Config keys to validate: {list(custom_config.keys())}\033[0m')

		# Required fields
		required_fields = ['model_provider', 'model_name']
		logger.debug(f'\033[93m[DEBUG] Checking required fields: {required_fields}\033[0m')

		for field in required_fields:
			if field not in custom_config:
				logger.debug(f'\033[91m[DEBUG] ERROR: Missing required field: {field}\033[0m')
				raise ValidationException(f'{_("missing_required_field")}: {field}')
			logger.debug(f"\033[96m[DEBUG] Required field '{field}' found: {custom_config[field]}\033[0m")

		# Validate model provider
		logger.debug(f'\033[93m[DEBUG] Validating model provider: {custom_config["model_provider"]}\033[0m')
		try:
			provider = ModelProvider(custom_config['model_provider'])
			logger.debug(f'\033[92m[DEBUG] Model provider validation passed: {provider}\033[0m')
		except ValueError:
			logger.debug(f'\033[91m[DEBUG] ERROR: Invalid model provider: {custom_config["model_provider"]}\033[0m')
			raise ValidationException(_('invalid_model_provider'))

		# Validate model compatibility
		logger.debug(f'\033[93m[DEBUG] Validating model compatibility: {custom_config["model_name"]}\033[0m')
		if not cls.validate_model_compatibility(provider, custom_config['model_name']):
			logger.debug(f'\033[91m[DEBUG] ERROR: Invalid model for provider: {custom_config["model_name"]}\033[0m')
			raise ValidationException(_('invalid_model_for_provider'))
		logger.debug('\033[92m[DEBUG] Model compatibility validation passed\033[0m')

		# Validate temperature
		temperature = custom_config.get('temperature', 0.7)
		logger.debug(f'\033[93m[DEBUG] Validating temperature: {temperature}\033[0m')
		if not 0 <= temperature <= 2:
			logger.debug(f'\033[91m[DEBUG] ERROR: Invalid temperature range: {temperature}\033[0m')
			raise ValidationException(_('invalid_temperature_range'))
		logger.debug('\033[92m[DEBUG] Temperature validation passed\033[0m')

		# Validate max_tokens
		max_tokens = custom_config.get('max_tokens', 2048)
		logger.debug(f'\033[93m[DEBUG] Validating max_tokens: {max_tokens}\033[0m')
		if not 1 <= max_tokens <= 32000:
			logger.debug(f'\033[91m[DEBUG] ERROR: Invalid max_tokens range: {max_tokens}\033[0m')
			raise ValidationException(_('invalid_max_tokens_range'))
		logger.debug('\033[92m[DEBUG] Max tokens validation passed\033[0m')

		logger.debug('\033[92m[DEBUG] All validations passed successfully\033[0m')
		logger.debug('\033[92m[DEBUG] AgentFactory._validate_custom_config() - EXIT\033[0m')
		return custom_config
