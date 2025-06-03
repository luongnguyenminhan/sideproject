"""
Colorful logging utility for Chat Workflow
Enhanced logging with ANSI colors for better debugging experience
"""

import logging
import time
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

	# Background colors
	BG_BLACK = '\033[40m'
	BG_RED = '\033[41m'
	BG_GREEN = '\033[42m'
	BG_YELLOW = '\033[43m'
	BG_BLUE = '\033[44m'
	BG_MAGENTA = '\033[45m'
	BG_CYAN = '\033[46m'
	BG_WHITE = '\033[47m'

	# Styles
	BOLD = '\033[1m'
	DIM = '\033[2m'
	UNDERLINE = '\033[4m'
	BLINK = '\033[5m'
	REVERSE = '\033[7m'


class ColorLogger:
	"""Enhanced colorful logger for Chat Workflow"""

	def __init__(self, name: str):
		self.logger = logging.getLogger(name)
		self.start_time = time.time()

	def info(self, message: str, color: str = Colors.BRIGHT_CYAN, **kwargs):
		"""Enhanced info logging with color and context"""
		elapsed = time.time() - self.start_time
		colored_message = f'{color}[{elapsed:.3f}s] {message}{Colors.RESET}'

		if kwargs:
			context_info = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
			colored_message += f' {Colors.DIM}({context_info}){Colors.RESET}'

		self.logger.info(colored_message)

	def success(self, message: str, **kwargs):
		"""Success logging in green"""
		self.info(f'✅ {message}', Colors.BRIGHT_GREEN, **kwargs)

	def warning(self, message: str, **kwargs):
		"""Warning logging in yellow"""
		elapsed = time.time() - self.start_time
		colored_message = f'{Colors.BRIGHT_YELLOW}[{elapsed:.3f}s] ⚠️ {message}{Colors.RESET}'

		if kwargs:
			context_info = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
			colored_message += f' {Colors.DIM}({context_info}){Colors.RESET}'

		self.logger.warning(colored_message)

	def error(self, message: str, **kwargs):
		"""Error logging in red"""
		elapsed = time.time() - self.start_time
		colored_message = f'{Colors.BRIGHT_RED}[{elapsed:.3f}s] ❌ {message}{Colors.RESET}'

		if kwargs:
			context_info = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
			colored_message += f' {Colors.DIM}({context_info}){Colors.RESET}'

		self.logger.error(colored_message)

	def debug(self, message: str, **kwargs):
		"""Debug logging in dim color"""
		elapsed = time.time() - self.start_time
		colored_message = f'{Colors.DIM}[{elapsed:.3f}s] 🔍 {message}{Colors.RESET}'

		if kwargs:
			context_info = ' | '.join([f'{k}={v}' for k, v in kwargs.items()])
			colored_message += f' {Colors.DIM}({context_info}){Colors.RESET}'

		self.logger.debug(colored_message)

	def workflow_start(self, workflow_name: str, **kwargs):
		"""Start workflow logging"""
		self.info(
			f'🚀 {Colors.BOLD}STARTING{Colors.RESET}{Colors.BRIGHT_CYAN} {workflow_name}',
			Colors.BRIGHT_CYAN,
			**kwargs,
		)

	def workflow_complete(self, workflow_name: str, duration: float, **kwargs):
		"""Complete workflow logging"""
		self.success(
			f'🎉 {Colors.BOLD}COMPLETED{Colors.RESET}{Colors.BRIGHT_GREEN} {workflow_name} in {duration:.3f}s',
			**kwargs,
		)

	def rag_decision(self, decision: bool, factors: Dict[str, Any], **kwargs):
		"""RAG decision logging"""
		decision_icon = '🔍' if decision else '⏭️'
		decision_text = 'USE_RAG' if decision else 'SKIP_RAG'
		color = Colors.BRIGHT_BLUE if decision else Colors.BRIGHT_YELLOW

		self.info(
			f'{decision_icon} {Colors.BOLD}RAG_DECISION:{Colors.RESET}{color} {decision_text}',
			color,
			factors_count=len(factors),
			**kwargs,
		)

	def query_optimization(self, original: str, optimized_count: int, **kwargs):
		"""Query optimization logging"""
		self.info(
			f"🔧 {Colors.BOLD}QUERY_OPT:{Colors.RESET}{Colors.BRIGHT_MAGENTA} '{original[:30]}...' → {optimized_count} queries",
			Colors.BRIGHT_MAGENTA,
			**kwargs,
		)

	def knowledge_retrieval(self, query_count: int, doc_count: int, avg_score: float, **kwargs):
		"""Knowledge retrieval logging"""
		self.info(
			f'📚 {Colors.BOLD}RETRIEVAL:{Colors.RESET}{Colors.CYAN} {query_count} queries → {doc_count} docs (avg_score: {avg_score:.3f})',
			Colors.CYAN,
			**kwargs,
		)

	def model_invocation(self, model_name: str, token_count: int, **kwargs):
		"""Model invocation logging"""
		self.info(
			f'🤖 {Colors.BOLD}MODEL_CALL:{Colors.RESET}{Colors.BRIGHT_BLUE} {model_name} (~{token_count} tokens)',
			Colors.BRIGHT_BLUE,
			**kwargs,
		)

	def tool_execution(self, tool_names: list, execution_time: float, **kwargs):
		"""Tool execution logging"""
		tools_str = ', '.join(tool_names)
		self.info(
			f'🔧 {Colors.BOLD}TOOLS:{Colors.RESET}{Colors.YELLOW} [{tools_str}] in {execution_time:.3f}s',
			Colors.YELLOW,
			**kwargs,
		)

	def performance_metric(self, metric_name: str, value: Any, unit: str = '', **kwargs):
		"""Performance metric logging"""
		self.info(
			f'📊 {Colors.BOLD}METRIC:{Colors.RESET}{Colors.BRIGHT_WHITE} {metric_name} = {value}{unit}',
			Colors.BRIGHT_WHITE,
			**kwargs,
		)

	def state_transition(self, from_node: str, to_node: str, **kwargs):
		"""State transition logging"""
		self.info(
			f'🔄 {Colors.BOLD}TRANSITION:{Colors.RESET}{Colors.MAGENTA} {from_node} → {to_node}',
			Colors.MAGENTA,
			**kwargs,
		)

	def health_check(self, component: str, status: str, **kwargs):
		"""Health check logging"""
		status_icon = '✅' if status == 'healthy' else '❌' if status == 'unhealthy' else '⚠️'
		status_color = Colors.BRIGHT_GREEN if status == 'healthy' else Colors.BRIGHT_RED if status == 'unhealthy' else Colors.BRIGHT_YELLOW

		self.info(
			f'{status_icon} {Colors.BOLD}HEALTH:{Colors.RESET}{status_color} {component} = {status.upper()}',
			status_color,
			**kwargs,
		)


def get_color_logger(name: str) -> ColorLogger:
	"""Factory function to create ColorLogger instance"""
	return ColorLogger(name)
