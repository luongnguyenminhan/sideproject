from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.agent.dal.agent_config_dal import AgentConfigDAL
from app.modules.agent.dal.agent_dal import AgentDAL
from app.modules.agent.models.agent_config import AgentConfig, ModelProvider
from app.modules.agent.models.agent import AgentType
from app.exceptions.exception import (
	NotFoundException,
	ValidationException,
	ForbiddenException,
)
from app.middleware.translation_manager import _
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AgentConfigRepo:
	"""Repository for Agent Configuration business logic and orchestration"""

	def __init__(self, db: Session = Depends(get_db)):
		logger.info('\033[92m[DEBUG] AgentConfigRepo.__init__() - ENTRY\033[0m')
		self.db = db
		self.config_dal = AgentConfigDAL(db)
		self.agent_dal = AgentDAL(db)
		logger.info('\033[92m[DEBUG] AgentConfigRepo.__init__() - EXIT\033[0m')

	def create_config(self, config_data: Dict[str, Any]) -> AgentConfig:
		"""Create new agent configuration with validation"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.create_config() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Config data: {config_data.get("name", "Unknown")}\033[0m')

		# Validate model compatibility
		logger.info('\033[93m[DEBUG] Validating model compatibility\033[0m')
		model_provider = config_data.get('model_provider')
		model_name = config_data.get('model_name')

		if model_provider and model_name:
			from app.modules.agent.services.agent_factory import AgentFactory

			is_compatible = AgentFactory.validate_model_compatibility(model_provider, model_name)
			if not is_compatible:
				logger.info(f'\033[91m[DEBUG] Model incompatibility: {model_provider} - {model_name}\033[0m')
				raise ValidationException(_('model_provider_incompatible'))

		logger.info('\033[96m[DEBUG] Model compatibility validated\033[0m')

		# Check for duplicate name
		logger.info('\033[93m[DEBUG] Checking for duplicate config name\033[0m')
		existing_config = self.config_dal.get_config_by_name(config_data.get('name', ''))
		if existing_config:
			logger.info('\033[91m[DEBUG] Config name already exists\033[0m')
			raise ValidationException(_('config_name_already_exists'))

		logger.info('\033[93m[DEBUG] Calling config_dal.create()\033[0m')
		config = self.config_dal.create(config_data)
		self.db.commit()
		self.db.refresh(config)
		logger.info(f'\033[96m[DEBUG] Config created with ID: {config.id}\033[0m')

		logger.info('\033[92m[DEBUG] AgentConfigRepo.create_config() - EXIT\033[0m')
		return config

	def get_config_by_id(self, config_id: str) -> AgentConfig:
		"""Get configuration by ID"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_config_by_id() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Config ID: {config_id}\033[0m')

		config = self.config_dal.get_by_id(config_id)
		if not config:
			logger.info('\033[91m[DEBUG] Config not found\033[0m')
			raise NotFoundException(_('agent_config_not_found'))

		logger.info(f'\033[96m[DEBUG] Config found: {config.name}\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_config_by_id() - EXIT\033[0m')
		return config

	def get_configs_by_type(self, agent_type: str, page: Optional[int] = None, page_size: Optional[int] = None) -> List[AgentConfig]:
		"""Get configurations by agent type"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_configs_by_type() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Agent type: {agent_type}, page: {page}, page_size: {page_size}\033[0m')

		configs = self.config_dal.get_configs_by_type(agent_type)

		if page and page_size:
			start = (page - 1) * page_size
			end = start + page_size
			configs = configs[start:end]

		logger.info(f'\033[96m[DEBUG] Found {len(configs)} configs\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_configs_by_type() - EXIT\033[0m')
		return configs

	def get_all_configs(self, page: int, page_size: int) -> List[AgentConfig]:
		"""Get all configurations"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_all_configs() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Page: {page}, Page Size: {page_size}\033[0m')

		configs = self.config_dal.get_all()

		if page and page_size:
			start = (page - 1) * page_size
			end = start + page_size
			configs = configs[start:end]

		logger.info(f'\033[96m[DEBUG] Found {len(configs)} configs\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_all_configs() - EXIT\033[0m')
		return configs

	def update_config(self, config_id: str, update_data: Dict[str, Any]) -> AgentConfig:
		"""Update configuration with validation"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.update_config() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Config ID: {config_id}, updates: {list(update_data.keys())}\033[0m')

		# Verify config exists
		logger.info('\033[93m[DEBUG] Verifying config exists\033[0m')
		existing_config = self.get_config_by_id(config_id)
		logger.info(f'\033[96m[DEBUG] Config found: {existing_config.name}\033[0m')

		# Validate model compatibility if model details are being updated
		if 'model_provider' in update_data or 'model_name' in update_data:
			logger.info('\033[93m[DEBUG] Validating model compatibility for update\033[0m')
			provider = update_data.get('model_provider', existing_config.model_provider)
			model = update_data.get('model_name', existing_config.model_name)

			from app.modules.agent.services.agent_factory import AgentFactory

			is_compatible = AgentFactory.validate_model_compatibility(provider, model)
			if not is_compatible:
				logger.info(f'\033[91m[DEBUG] Model incompatibility: {provider} - {model}\033[0m')
				raise ValidationException(_('model_provider_incompatible'))

			logger.info('\033[96m[DEBUG] Model compatibility validated\033[0m')

		# Check for duplicate name if name is being updated
		if 'name' in update_data and update_data['name'] != existing_config.name:
			logger.info('\033[93m[DEBUG] Checking for duplicate config name\033[0m')
			duplicate_config = self.config_dal.get_config_by_name(update_data['name'])
			if duplicate_config and duplicate_config.id != config_id:
				logger.info('\033[91m[DEBUG] Config name already exists\033[0m')
				raise ValidationException(_('config_name_already_exists'))

		logger.info('\033[93m[DEBUG] Calling config_dal.update()\033[0m')
		updated_config = self.config_dal.update(config_id, update_data)
		logger.info(f'\033[96m[DEBUG] Config updated successfully\033[0m')

		logger.info('\033[92m[DEBUG] AgentConfigRepo.update_config() - EXIT\033[0m')
		return updated_config

	def delete_config(self, config_id: str, force: bool = False) -> bool:
		"""Delete configuration with validation"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.delete_config() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Config ID: {config_id}, force: {force}\033[0m')

		# Verify config exists
		logger.info('\033[93m[DEBUG] Verifying config exists\033[0m')
		existing_config = self.get_config_by_id(config_id)
		logger.info(f'\033[96m[DEBUG] Config found: {existing_config.name}\033[0m')

		# Check if config is being used by any agents (unless force delete)
		if not force:
			logger.info('\033[93m[DEBUG] Checking if config is in use\033[0m')
			agents_using_config = self.agent_dal.get_agents_by_config_id(config_id)
			if agents_using_config:
				logger.info(f'\033[91m[DEBUG] Config is used by {len(agents_using_config)} agents\033[0m')
				raise ValidationException(_('config_in_use_cannot_delete'))
			logger.info('\033[96m[DEBUG] Config is not in use\033[0m')

		logger.info('\033[93m[DEBUG] Calling config_dal.delete()\033[0m')
		success = self.config_dal.delete(config_id)

		if not success:
			logger.info('\033[91m[DEBUG] Failed to delete config\033[0m')
			raise ValidationException(_('failed_to_delete_config'))

		logger.info(f'\033[96m[DEBUG] Config deleted successfully\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.delete_config() - EXIT\033[0m')
		return success

	def get_config_usage_stats(self, config_id: str) -> Dict[str, Any]:
		"""Get usage statistics for a configuration"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_config_usage_stats() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Config ID: {config_id}\033[0m')

		# Verify config exists
		config = self.get_config_by_id(config_id)

		# Get agents using this config
		logger.info('\033[93m[DEBUG] Getting agents using this config\033[0m')
		agents_using_config = self.agent_dal.get_agents_by_config_id(config_id)

		active_agents = [agent for agent in agents_using_config if agent.is_active]
		inactive_agents = [agent for agent in agents_using_config if not agent.is_active]

		stats = {
			'config_id': config_id,
			'config_name': config.name,
			'total_agents': len(agents_using_config),
			'active_agents': len(active_agents),
			'inactive_agents': len(inactive_agents),
			'agent_ids': [agent.id for agent in agents_using_config],
			'can_delete': len(agents_using_config) == 0,
		}

		logger.info(f'\033[96m[DEBUG] Usage stats: {stats["total_agents"]} total agents\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_config_usage_stats() - EXIT\033[0m')
		return stats

	def get_configs_by_provider(self, provider: ModelProvider) -> List[AgentConfig]:
		"""Get configurations by model provider"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_configs_by_provider() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Provider: {provider.value}\033[0m')

		configs = self.config_dal.get_configs_by_provider(provider)

		logger.info(f'\033[96m[DEBUG] Found {len(configs)} configs for provider\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.get_configs_by_provider() - EXIT\033[0m')
		return configs

	def search_configs(
		self,
		search_term: Optional[str] = None,
		agent_type: Optional[str] = None,
		provider: Optional[ModelProvider] = None,
		limit: Optional[int] = None,
	) -> List[AgentConfig]:
		"""Search configurations with multiple filters"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.search_configs() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Search: {search_term}, type: {agent_type}, provider: {provider}\033[0m')

		# Start with all configs
		configs = self.config_dal.get_all()

		# Apply filters
		if search_term:
			search_term = search_term.lower()
			configs = [config for config in configs if (search_term in config.name.lower() or (config.description and search_term in config.description.lower()))]

		if agent_type:
			configs = [config for config in configs if config.agent_type == agent_type]

		if provider:
			configs = [config for config in configs if config.model_provider == provider]

		# Apply limit
		if limit and limit > 0:
			configs = configs[:limit]

		logger.info(f'\033[96m[DEBUG] Found {len(configs)} matching configs\033[0m')
		logger.info('\033[92m[DEBUG] AgentConfigRepo.search_configs() - EXIT\033[0m')
		return configs

	def duplicate_config(self, config_id: str, new_name: str, description: Optional[str] = None) -> AgentConfig:
		"""Duplicate an existing configuration with a new name"""
		logger.info('\033[92m[DEBUG] AgentConfigRepo.duplicate_config() - ENTRY\033[0m')
		logger.info(f'\033[94m[DEBUG] Source config: {config_id}, new name: {new_name}\033[0m')

		# Get source config
		source_config = self.get_config_by_id(config_id)
		logger.info(f'\033[96m[DEBUG] Source config found: {source_config.name}\033[0m')

		# Check for duplicate name
		logger.info('\033[93m[DEBUG] Checking for duplicate config name\033[0m')
		existing_config = self.config_dal.get_config_by_name(new_name)
		if existing_config:
			logger.info('\033[91m[DEBUG] Config name already exists\033[0m')
			raise ValidationException(_('config_name_already_exists'))

		# Prepare new config data
		new_config_data = {
			'name': new_name,
			'description': description or f'Copy of {source_config.description or source_config.name}',
			'agent_type': source_config.agent_type,
			'model_provider': source_config.model_provider,
			'model_name': source_config.model_name,
			'temperature': source_config.temperature,
			'max_tokens': source_config.max_tokens,
			'system_prompt': source_config.system_prompt,
			'tools_config': source_config.tools_config,
			'workflow_config': source_config.workflow_config,
			'memory_config': source_config.memory_config,
		}

		logger.info('\033[93m[DEBUG] Creating duplicate config\033[0m')
		new_config = self.config_dal.create(new_config_data)
		logger.info(f'\033[96m[DEBUG] Duplicate config created: {new_config.id}\033[0m')

		logger.info('\033[92m[DEBUG] AgentConfigRepo.duplicate_config() - EXIT\033[0m')
		return new_config
