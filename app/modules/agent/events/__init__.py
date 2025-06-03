"""Agent event handlers initialization"""

from app.core.events import EventHooks
from app.modules.agent.events.user_events import handle_user_created_event
import logging

logger = logging.getLogger(__name__)


def register_agent_event_handlers():
	"""Register all agent-related event handlers"""
	logger.info('Registering agent event handlers')

	event_hooks = EventHooks()

	# Register user creation handler
	event_hooks.register('user_created', handle_user_created_event)

	logger.info('Agent event handlers registered successfully')


__all__ = ['register_agent_event_handlers']
