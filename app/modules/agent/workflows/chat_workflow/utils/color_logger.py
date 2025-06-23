"""
Simple color logger utilities
Self-contained logging utilities for the chat workflow module
"""

import logging
from typing import Any, Dict, Optional


class Colors:
	"""ANSI color codes for terminal output"""

	# Reset
	RESET = '\033[0m'

	# Regular colors
	BLACK = '\033[30m'
	RED = '\033[31m'
	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	BLUE = '\033[34m'
	MAGENTA = '\033[35m'
	CYAN = '\033[36m'
	WHITE = '\033[37m'

	# Bright colors
	BRIGHT_BLACK = '\033[90m'
	BRIGHT_RED = '\033[91m'
	BRIGHT_GREEN = '\033[92m'
	BRIGHT_YELLOW = '\033[93m'
	BRIGHT_BLUE = '\033[94m'
	BRIGHT_MAGENTA = '\033[95m'
	BRIGHT_CYAN = '\033[96m'
	BRIGHT_WHITE = '\033[97m'

	# Styles
	BOLD = '\033[1m'
	DIM = '\033[2m'
	UNDERLINE = '\033[4m'


class SimpleColorLogger:
	"""Simplified color logger for the workflow module"""

	def __init__(self, name: str):
		self.logger = logging.getLogger(name)
		self.name = name

	def _format_message(self, message: str, color: str = Colors.RESET) -> str:
		"""Format message with color"""
		return f'{color}{message}{Colors.RESET}'

	def info(self, message: str, color: str = Colors.CYAN, **kwargs):
		"""Log info message with color"""
		formatted_msg = self._format_message(message, color)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.info(formatted_msg)

	def debug(self, message: str, **kwargs):
		"""Log debug message"""
		formatted_msg = message
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.debug(formatted_msg)

	def warning(self, message: str, **kwargs):
		"""Log warning message"""
		formatted_msg = self._format_message(message, Colors.YELLOW)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.warning(formatted_msg)

	def error(self, message: str, **kwargs):
		"""Log error message"""
		formatted_msg = self._format_message(message, Colors.RED)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.error(formatted_msg)

	def success(self, message: str, **kwargs):
		"""Log success message"""
		formatted_msg = self._format_message(message, Colors.GREEN)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.info(formatted_msg)

	def performance_metric(self, metric_name: str, value: str, unit: str = ''):
		"""Log performance metric"""
		formatted_msg = self._format_message(f'Performance: {metric_name} = {value}{unit}', Colors.MAGENTA)
		self.logger.debug(formatted_msg)

	def workflow_start(self, message: str, color: str = Colors.BLUE, **kwargs):
		"""Log workflow start message"""
		formatted_msg = self._format_message(f'WORKFLOW START: {message}', color)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.info(formatted_msg)

	def tool_start(self, tool_name: str, **kwargs):
		"""Log tool execution start"""
		formatted_msg = self._format_message(f'🔧 TOOL START: {tool_name}', Colors.BRIGHT_YELLOW)
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.info(formatted_msg)

	def tool_success(self, tool_name: str, result: str = None, **kwargs):
		"""Log successful tool execution"""
		formatted_msg = self._format_message(f'✅ TOOL SUCCESS: {tool_name}', Colors.BRIGHT_GREEN)
		if result:
			formatted_msg += f' → {result[:100]}{"..." if len(result) > 100 else ""}'
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.info(formatted_msg)

	def tool_error(self, tool_name: str, error: str, **kwargs):
		"""Log tool execution error"""
		formatted_msg = self._format_message(f'❌ TOOL ERROR: {tool_name}', Colors.BRIGHT_RED)
		formatted_msg += f' → {error}'
		if kwargs:
			formatted_msg += f' - {kwargs}'
		self.logger.error(formatted_msg)

	def tool_input(self, tool_name: str, inputs: Dict[str, Any]):
		"""Log tool input parameters"""
		formatted_msg = self._format_message(f'📥 TOOL INPUT: {tool_name}', Colors.BRIGHT_CYAN)
		formatted_msg += f' → {inputs}'
		self.logger.debug(formatted_msg)

	def tool_output(self, tool_name: str, output: Any):
		"""Log tool output"""
		formatted_msg = self._format_message(f'📤 TOOL OUTPUT: {tool_name}', Colors.BRIGHT_MAGENTA)
		output_str = str(output)[:200] + ('...' if len(str(output)) > 200 else '')
		formatted_msg += f' → {output_str}'
		self.logger.debug(formatted_msg)


def get_color_logger(name: str) -> SimpleColorLogger:
	"""Get a color logger instance"""
	return SimpleColorLogger(name)
