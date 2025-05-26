"""Event hooks system for inter-module communication"""

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class EventHooks:
	"""Simple event hooks system that enables loosely coupled inter-module communication"""

	_instance = None
	_hooks: Dict[str, List[Callable]] = {}

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(EventHooks, cls).__new__(cls)
			cls._instance._hooks = {}
		return cls._instance

	def register(self, event_name: str, callback: Callable) -> None:
		"""Register a callback for an event

		Args:
		    event_name (str): Name of the event to subscribe to
		    callback (Callable): Function to call when event is triggered
		"""
		if event_name not in self._hooks:
			self._hooks[event_name] = []

		if callback not in self._hooks[event_name]:
			self._hooks[event_name].append(callback)
			logger.debug(f'Registered callback for event: {event_name}')

	def unregister(self, event_name: str, callback: Callable) -> None:
		"""Unregister a callback for an event

		Args:
		    event_name (str): Name of the event
		    callback (Callable): Function to remove from callbacks
		"""
		if event_name in self._hooks and callback in self._hooks[event_name]:
			self._hooks[event_name].remove(callback)
			logger.debug(f'Unregistered callback for event: {event_name}')

	def trigger(self, event_name: str, *args, **kwargs) -> None:
		"""Trigger an event and call all registered callbacks

		Args:
		    event_name (str): Name of the event to trigger
		    *args, **kwargs: Arguments to pass to the callbacks
		"""
		if event_name in self._hooks:
			logger.debug(f'Triggering event: {event_name}')
			for callback in self._hooks[event_name]:
				try:
					callback(*args, **kwargs)
				except Exception as e:
					logger.error(f'Error in event callback for {event_name}: {e}')
		else:
			logger.debug(f'No callbacks registered for event: {event_name}')
