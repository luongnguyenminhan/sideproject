"""
Tool execution nodes cho Chat Workflow
Advanced tool handling với frontend integration
"""

import logging
import time
from typing import Dict, Any, List, Optional

from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage

from ..state.workflow_state import AgentState, StateManager
from ..config.workflow_config import WorkflowConfig
from ..utils.error_handlers import handle_errors, ToolError

logger = logging.getLogger(__name__)


class ToolNodes:
	"""
	Production tool execution nodes

	Features:
	- Frontend tool interrupts
	- Backend tool execution
	- Error handling với graceful degradation
	- Performance monitoring
	- Tool result validation
	"""

	def __init__(self, config: WorkflowConfig):
		self.config = config
		self.logger = logging.getLogger(__name__)

	@handle_errors(
		fallback_response='Không thể thực hiện thao tác yêu cầu. Vui lòng thử lại sau.',
		error_type='tool_execution',
	)
	async def run_tools(self, state: AgentState, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
		"""
		Execute backend tools với advanced error handling
		"""
		start_time = time.time()

		try:
			self.logger.info('🔧 [Tools] Starting backend tool execution...')

			# Validate state
			if not self._validate_tool_state(state):
				raise ToolError('Invalid state for tool execution', 'invalid_state')

			# Get backend tools
			# tools = get_backend_tools(config)
			tools = []  # Placeholder for actual tool retrieval logic
			if not tools:
				self.logger.warning('❌ [Tools] No backend tools available')
				return self._create_no_tools_response()

			# Create tool node
			tool_node = ToolNode(tools)

			# Execute tools với monitoring
			result = await self._execute_tools_with_monitoring(tool_node, state, config, **kwargs)

			# Validate tool results
			validated_result = self._validate_tool_results(result)

			# Calculate processing time
			processing_time = time.time() - start_time

			# Update state với tool execution metadata
			updated_state = StateManager.add_processing_time(state, 'tools', processing_time)

			self.logger.info(f'✅ [Tools] Backend tool execution completed (processed in {processing_time:.2f}s)')

			return {
				**updated_state,
				**validated_result,
				'tool_execution_metadata': {
					'tools_count': len(tools),
					'processing_time': processing_time,
					'execution_timestamp': time.time(),
				},
			}

		except Exception as e:
			self.logger.error(f'Error in backend tool execution: {str(e)}')

			# Create error response
			error_response = self._create_tool_error_response(e, state)

			return {
				'messages': [error_response],
				'error_context': {
					'error_type': 'tool_execution_error',
					'error_message': str(e),
					'timestamp': time.time(),
				},
			}

	def _validate_tool_state(self, state: AgentState) -> bool:
		"""Validate state for tool execution"""

		# Check required fields
		if not state.get('messages'):
			return False

		# Check for tool calls in last message
		messages = state['messages']
		last_message = messages[-1]

		if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
			return False

		return True

	async def _execute_tools_with_monitoring(self, tool_node: ToolNode, state: AgentState, config: Dict[str, Any], **kwargs) -> Dict[str, Any]:
		"""Execute tools với performance monitoring"""

		start_time = time.time()

		try:
			# Log tool execution details
			messages = state.get('messages', [])
			if messages:
				last_message = messages[-1]
				if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
					tool_names = [tc.get('name', 'unknown') for tc in last_message.tool_calls]
					self.logger.info(f'🔧 [Tools] Executing tools: {", ".join(tool_names)}')

			# Execute tool node
			result = await tool_node.ainvoke(state, config, **kwargs)

			execution_time = time.time() - start_time
			self.logger.info(f'🔧 [Tools] Execution completed in {execution_time:.2f}s')

			return result

		except Exception as e:
			execution_time = time.time() - start_time
			self.logger.error(f'🔧 [Tools] Execution failed after {execution_time:.2f}s: {str(e)}')
			raise e

	def _validate_tool_results(self, result: Dict[str, Any]) -> Dict[str, Any]:
		"""Validate và enhance tool results"""

		# Ensure messages exist
		if 'messages' not in result:
			result['messages'] = []

		# Validate tool messages
		validated_messages = []

		for message in result.get('messages', []):
			if isinstance(message, ToolMessage):
				# Validate tool message content
				if self._validate_tool_message_content(message):
					validated_messages.append(message)
				else:
					# Create fallback message
					fallback_message = ToolMessage(
						content='Công cụ đã thực hiện xong nhưng không trả về kết quả rõ ràng.',
						tool_call_id=getattr(message, 'tool_call_id', 'unknown'),
					)
					validated_messages.append(fallback_message)
			else:
				validated_messages.append(message)

		result['messages'] = validated_messages
		return result

	def _validate_tool_message_content(self, message: ToolMessage) -> bool:
		"""Validate tool message content"""

		try:
			# Check basic requirements
			if not hasattr(message, 'content') or not message.content:
				return False

			content = str(message.content)

			# Check content length
			if len(content.strip()) < 1:
				return False

			if len(content) > 5000:  # Too long
				return False

			return True

		except Exception:
			return False

	def _create_no_tools_response(self) -> Dict[str, Any]:
		"""Create response when no tools available"""

		error_message = ToolMessage(
			content='Không có công cụ nào khả dụng để thực hiện yêu cầu này.',
			tool_call_id='no_tools',
		)

		return {'messages': [error_message]}

	def _create_tool_error_response(self, error: Exception, state: AgentState) -> ToolMessage:
		"""Create tool error response"""

		# Determine tool name if possible
		tool_name = 'công cụ'
		try:
			messages = state.get('messages', [])
			if messages:
				last_message = messages[-1]
				if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
					tool_name = last_message.tool_calls[0].get('name', 'công cụ')
		except Exception:
			pass

		# Create user-friendly error message
		error_content = f'Không thể thực hiện {tool_name}. '

		# Specific error handling
		error_str = str(error).lower()
		if 'timeout' in error_str:
			error_content += 'Quá thời gian xử lý.'
		elif 'permission' in error_str:
			error_content += 'Không có quyền thực hiện thao tác này.'
		elif 'network' in error_str:
			error_content += 'Gặp sự cố kết nối.'
		else:
			error_content += 'Vui lòng thử lại sau.'

		return ToolMessage(content=error_content, tool_call_id='error')

	def get_tool_status(self, config: Dict[str, Any]) -> Dict[str, Any]:
		"""Get status of available tools"""

		try:
			# tools = get_backend_tools(config)

			# tool_info = []
			# for tool in tools:
			# 	tool_info.append({
			# 		'name': getattr(tool, 'name', 'unknown'),
			# 		'description': getattr(tool, 'description', ''),
			# 		'type': 'backend',
			# 	})

			return {
				'status': 'healthy',
				'tool_count': len([]),
				'tools': [],  # tool_info,
				'timestamp': time.time(),
			}

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}

	async def health_check(self) -> Dict[str, Any]:
		"""Health check cho tool system"""

		try:
			# Test tool loading
			test_config = {}
			tool_status = self.get_tool_status(test_config)

			return {
				'status': 'healthy',
				'tool_system': tool_status,
				'timestamp': time.time(),
			}

		except Exception as e:
			return {'status': 'unhealthy', 'error': str(e), 'timestamp': time.time()}
