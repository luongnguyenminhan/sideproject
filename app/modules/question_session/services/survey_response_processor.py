"""
Survey Response Processing Service
Processes survey responses and formats them for AI integration
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ...agent.services.langgraph_service import LangGraphService
from ...chat.dal.conversation_dal import ConversationDAL
from ..repository.question_session_repo import QuestionSessionRepo
from ..schemas.question_session_request import ParseSurveyResponseRequest

logger = logging.getLogger(__name__)


class SurveyResponseProcessor:
	"""Service to process survey responses and integrate with AI workflow"""

	def __init__(self, db: Session):
		print(f'🏗️ [SurveyProcessor.__init__] Initializing SurveyResponseProcessor service')
		self.db = db
		self.question_session_repo = QuestionSessionRepo(db)
		self.conversation_dal = ConversationDAL(db)
		self.langgraph_service = LangGraphService(db)
		print(f'✅ [SurveyProcessor.__init__] SurveyResponseProcessor initialized successfully')

	async def process_survey_response_for_ai(
		self,
		request: ParseSurveyResponseRequest,
		user_id: str,
		agent_instance: Optional[Any] = None,
	) -> Dict[str, Any]:
		"""
		Complete survey response processing pipeline:
		1. Store survey responses in database
		2. Convert responses to human-readable text
		3. Send to AI agent for processing
		4. Return formatted result

		Args:
		    request: Survey response data from frontend
		    user_id: User ID
		    agent_instance: Optional agent instance for AI processing

		Returns:
		    Dictionary with processed response and AI feedback
		"""
		print(f'🔄 [SurveyProcessor] Starting survey response processing for user {user_id}')
		print(f'📝 [SurveyProcessor] Request data: conversation_id={request.conversation_id}, answers_count={len(request.answers)}')
		logger.info(f'Processing survey response for user {user_id}, conversation {request.conversation_id}')

		try:
			# Step 1: Store survey responses in database
			print(f'💾 [SurveyProcessor] Step 1: Storing survey responses in database...')
			parsed_response = self.question_session_repo.parse_survey_response(request, user_id)
			print(f'✅ [SurveyProcessor] Survey response stored successfully: session_id={parsed_response.session_id}')
			logger.info(f'Survey response stored successfully: {parsed_response.session_id}')

			# Step 2: Convert survey responses to human-readable text
			print(f'🔤 [SurveyProcessor] Step 2: Converting responses to human-readable text...')
			human_text = self._convert_responses_to_human_text(request.answers, request.conversation_id, user_id)
			print(f'✅ [SurveyProcessor] Human text generated: {len(human_text)} characters')
			print(f'📄 [SurveyProcessor] Human text preview: {human_text[:200]}...')
			logger.info(f'Survey responses converted to human text: {len(human_text)} characters')

			# Step 3: Get conversation context for AI processing
			print(f'🔍 [SurveyProcessor] Step 3: Getting conversation context...')
			conversation = self.conversation_dal.get_user_conversation_by_id(request.conversation_id, user_id)
			if not conversation:
				print(f'❌ [SurveyProcessor] Conversation {request.conversation_id} not found')
				raise ValueError(f'Conversation {request.conversation_id} not found')
			print(f'✅ [SurveyProcessor] Conversation found: {conversation.id}')

			# Step 4: Process with AI agent
			print(f'🤖 [SurveyProcessor] Step 4: Processing with AI agent...')
			ai_response = None
			if agent_instance:
				print(f'🚀 [SurveyProcessor] AI agent available, starting processing...')
				try:
					# Get conversation history
					conversation_history = self._get_conversation_history(request.conversation_id, user_id)
					print(f'📚 [SurveyProcessor] Retrieved conversation history: {len(conversation_history)} messages')

					# Process with AI
					print(f'⚡ [SurveyProcessor] Executing AI conversation workflow...')
					ai_result = await self.langgraph_service.execute_conversation(
						agent=agent_instance,
						conversation_id=request.conversation_id,
						user_message=human_text,
						conversation_system_prompt=getattr(agent_instance, 'default_system_prompt', None),
						conversation_history=conversation_history,
						user_id=user_id,
					)

					ai_response = ai_result.get('content', 'AI processing completed successfully')
					print(f'✅ [SurveyProcessor] AI processing completed successfully')
					print(f'🎯 [SurveyProcessor] AI response preview: {ai_response[:200]}...')
					logger.info(f'AI processing completed for survey response')

				except Exception as e:
					print(f'❌ [SurveyProcessor] AI processing failed: {str(e)}')
					logger.error(f'AI processing failed: {e}')
					ai_response = f'Survey responses have been recorded. AI processing encountered an issue: {str(e)}'
			else:
				print(f'⚠️ [SurveyProcessor] No AI agent instance provided, skipping AI processing')

			# Step 5: Prepare comprehensive response
			print(f'📦 [SurveyProcessor] Step 5: Preparing comprehensive response...')
			result = {
				'survey_processing': {
					'session_id': parsed_response.session_id,
					'conversation_id': parsed_response.conversation_id,
					'total_answers': parsed_response.total_answers,
					'answers_processed': parsed_response.answers_processed,
					'session_status': parsed_response.session_status,
					'completion_date': (parsed_response.completion_date.isoformat() if parsed_response.completion_date else None),
				},
				'human_readable_response': human_text,
				'ai_response': ai_response,
				'processing_metadata': {
					'processed_at': datetime.now().isoformat(),
					'user_id': user_id,
					'ai_processing_enabled': agent_instance is not None,
					'response_length': len(human_text),
					'success': True,
				},
			}

			print(f'🎉 [SurveyProcessor] Survey response processing completed successfully!')
			print(f'📊 [SurveyProcessor] Result summary: session_id={parsed_response.session_id}, ai_enabled={agent_instance is not None}')
			logger.info(f'Survey response processing completed successfully for session {parsed_response.session_id}')
			return result

		except Exception as e:
			print(f'💥 [SurveyProcessor] Error processing survey response: {str(e)}')
			logger.error(f'Error processing survey response: {e}')
			# Return error response with partial data if available
			error_result = {
				'survey_processing': None,
				'human_readable_response': None,
				'ai_response': f'Error processing survey responses: {str(e)}',
				'processing_metadata': {
					'processed_at': datetime.now().isoformat(),
					'user_id': user_id,
					'ai_processing_enabled': agent_instance is not None,
					'success': False,
					'error': str(e),
				},
			}
			print(f'🔄 [SurveyProcessor] Returning error response: {error_result["processing_metadata"]}')
			return error_result

	def _convert_responses_to_human_text(self, answers: Dict[str, Any], conversation_id: str, user_id: str) -> str:
		"""
		Convert survey answers to human-readable text format

		Args:
		    answers: Raw survey answers from frontend
		    conversation_id: Conversation ID
		    user_id: User ID

		Returns:
		    Human-readable text representation of survey responses
		"""
		print(f'🔤 [SurveyProcessor._convert_responses_to_human_text] Converting {len(answers)} survey answers to human text')
		print(f'📋 [SurveyProcessor._convert_responses_to_human_text] Answers structure: {list(answers.keys())}')
		logger.info(f'Converting {len(answers)} survey answers to human text')

		try:
			# Get session details to access questions data
			print(f'🔍 [SurveyProcessor._convert_responses_to_human_text] Getting active sessions for conversation {conversation_id}')
			active_sessions = self.question_session_repo.question_session_dal.get_conversation_sessions(
				conversation_id=conversation_id,
				user_id=user_id,
				session_status='active',
			)

			if not active_sessions:
				print(f'⚠️ [SurveyProcessor._convert_responses_to_human_text] No active sessions found, using fallback formatting')
				return self._format_answers_without_questions(answers)

			session = active_sessions[0]
			questions_data = session.questions_data
			print(f'✅ [SurveyProcessor._convert_responses_to_human_text] Found session: {session.id}, questions_data available: {bool(questions_data)}')

			if not questions_data:
				print(f'⚠️ [SurveyProcessor._convert_responses_to_human_text] No questions data available, using fallback formatting')
				return self._format_answers_without_questions(answers)

			print(f'📝 [SurveyProcessor._convert_responses_to_human_text] Questions data found: {len(questions_data)} questions')

			# Format with question context
			formatted_parts = []
			formatted_parts.append('📝 **Survey Response Summary**')
			formatted_parts.append(f'📅 Completed on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
			formatted_parts.append('')

			print(f'🔄 [SurveyProcessor._convert_responses_to_human_text] Processing {len(answers)} answers...')
			for i, (question_index, answer_value) in enumerate(answers.items()):
				print(f'  📊 [SurveyProcessor._convert_responses_to_human_text] Processing answer {i + 1}/{len(answers)}: question_index={question_index}')
				question_data = self._get_question_by_index(questions_data, question_index)
				formatted_answer = self._format_single_answer_with_mapping(question_data, answer_value, question_index)
				formatted_parts.append(formatted_answer)
				formatted_parts.append('')

			formatted_parts.append('---')
			formatted_parts.append('ℹ️ This survey response has been automatically processed and is ready for AI analysis.')

			result = '\n'.join(formatted_parts)
			print(f'✅ [SurveyProcessor._convert_responses_to_human_text] Successfully converted to human text ({len(result)} characters)')
			logger.info(f'Successfully converted survey answers to human text ({len(result)} characters)')
			return result

		except Exception as e:
			print(f'❌ [SurveyProcessor._convert_responses_to_human_text] Error converting answers: {str(e)}')
			logger.error(f'Error converting answers to human text: {e}')
			return self._format_answers_without_questions(answers)

	def _format_answers_without_questions(self, answers: Dict[str, Any]) -> str:
		"""Format answers when question data is not available"""
		print(f'📄 [SurveyProcessor._format_answers_without_questions] Formatting {len(answers)} answers without question context')
		formatted_parts = []
		formatted_parts.append('📝 **Survey Response Summary**')
		formatted_parts.append(f'📅 Completed on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
		formatted_parts.append('')

		for question_id, answer_value in answers.items():
			# Use the simple formatter since we don't have question data for mapping
			formatted_answer = self._format_single_answer(f'Question {question_id}', answer_value, question_id)
			formatted_parts.append(formatted_answer)
			formatted_parts.append('')

		formatted_parts.append('---')
		formatted_parts.append('ℹ️ Survey responses processed without question context.')

		result = '\n'.join(formatted_parts)
		print(f'✅ [SurveyProcessor._format_answers_without_questions] Generated fallback format ({len(result)} characters)')
		return result

	def _get_question_by_index(self, questions_data: List[Dict[str, Any]], question_index: str) -> Optional[Dict[str, Any]]:
		"""Get question data by index from questions data"""
		try:
			if question_index.isdigit():
				index = int(question_index)
				if 0 <= index < len(questions_data):
					return questions_data[index]

			return None
		except (ValueError, IndexError, KeyError):
			return None

	def _format_single_answer_with_mapping(
		self,
		question_data: Optional[Dict[str, Any]],
		answer_value: Any,
		question_id: str,
	) -> str:
		"""Format a single answer with proper answer ID to label mapping"""
		try:
			# Get question text
			if question_data:
				question_text = question_data.get(
					'Question',
					question_data.get('question', question_data.get('text', f'Question {question_id}')),
				)
				question_type = question_data.get('Type', question_data.get('type', 'unknown'))
				answers_data = question_data.get('Answers', question_data.get('answers', []))
			else:
				question_text = f'Question {question_id}'
				question_type = 'unknown'
				answers_data = []

			# Handle different answer types with ID-to-label mapping
			if isinstance(answer_value, dict):
				# Handle complex answers (like text input with multiple fields)
				if len(answer_value) == 1 and 'value' in answer_value:
					mapped_value = self._map_answer_id_to_label(answer_value['value'], answers_data)
					return f'**Q{question_id}:** {question_text}\n**Answer:** {mapped_value}'
				else:
					answer_parts = []
					for key, value in answer_value.items():
						mapped_value = self._map_answer_id_to_label(value, answers_data)
						answer_parts.append(f'  • {key}: {mapped_value}')
					return f'**Q{question_id}:** {question_text}\n**Answer:**\n' + '\n'.join(answer_parts)

			elif isinstance(answer_value, list):
				# Handle multiple choice answers - map each ID to label
				mapped_answers = []
				for item in answer_value:
					mapped_item = self._map_answer_id_to_label(item, answers_data)
					mapped_answers.append(mapped_item)

				answer_list = '  • ' + '\n  • '.join(mapped_answers)
				return f'**Q{question_id}:** {question_text}\n**Selected options:**\n{answer_list}'

			elif isinstance(answer_value, str):
				# Handle single choice or text answers - try to map ID to label
				mapped_value = self._map_answer_id_to_label(answer_value, answers_data)
				return f'**Q{question_id}:** {question_text}\n**Answer:** {mapped_value}'

			elif isinstance(answer_value, (int, float)):
				# Handle numeric answers (ratings, scales) - check if it's an ID that needs mapping
				mapped_value = self._map_answer_id_to_label(str(answer_value), answers_data)
				if mapped_value != str(answer_value):
					# ID was mapped to a label
					return f'**Q{question_id}:** {question_text}\n**Rating/Value:** {mapped_value}'
				else:
					# It's a numeric value, not an ID
					return f'**Q{question_id}:** {question_text}\n**Rating/Value:** {answer_value}'

			else:
				# Handle any other type
				mapped_value = self._map_answer_id_to_label(str(answer_value), answers_data)
				return f'**Q{question_id}:** {question_text}\n**Answer:** {mapped_value}'

		except Exception as e:
			logger.warning(f'Error formatting answer for question {question_id}: {e}')
			# Fallback to simple formatting
			return self._format_single_answer(
				(question_text if 'question_text' in locals() else f'Question {question_id}'),
				answer_value,
				question_id,
			)

	def _map_answer_id_to_label(self, answer_id: Any, answers_data: List[Dict[str, Any]]) -> str:
		"""
		Map an answer ID to its corresponding label from the question's answers data

		Args:
		    answer_id: The answer ID to map (can be string, int, etc.)
		    answers_data: List of answer options from the question data

		Returns:
		    The mapped label or the original ID if no mapping found
		"""
		try:
			if not answers_data:
				print(f'  🔍 [SurveyProcessor._map_answer_id_to_label] No answers_data provided for ID: {answer_id}')
				return str(answer_id)

			# Convert answer_id to string for comparison
			answer_id_str = str(answer_id)
			print(f"  🔍 [SurveyProcessor._map_answer_id_to_label] Mapping answer_id '{answer_id_str}' from {len(answers_data)} options")

			# Look for the answer in the answers data
			for i, answer in enumerate(answers_data):
				if isinstance(answer, dict):
					# Check different possible ID field names
					answer_option_id = answer.get('ID', answer.get('id', answer.get('value', answer.get('key'))))

					if str(answer_option_id) == answer_id_str:
						# Found matching ID, return the label
						label = answer.get(
							'Label',
							answer.get('label', answer.get('text', answer.get('name'))),
						)
						if label:
							mapped_result = f'{label} (ID: {answer_id})'
							print(f"  ✅ [SurveyProcessor._map_answer_id_to_label] Mapped ID '{answer_id}' to '{mapped_result}'")
							return mapped_result
						else:
							print(f"  ⚠️ [SurveyProcessor._map_answer_id_to_label] Found ID match but no label for '{answer_id}'")
							return str(answer_id)

				elif isinstance(answer, str):
					# Simple string answer
					if answer == answer_id_str:
						print(f"  ✅ [SurveyProcessor._map_answer_id_to_label] Direct string match for '{answer_id}'")
						return answer

			print(f"  ❌ [SurveyProcessor._map_answer_id_to_label] No mapping found for ID '{answer_id}', returning as-is")
			return str(answer_id)
		except Exception as e:
			print(f'  💥 [SurveyProcessor._map_answer_id_to_label] Error mapping answer ID {answer_id}: {e}')
			logger.warning(f'Error mapping answer ID {answer_id}: {e}')
			return str(answer_id)

	def _format_single_answer(self, question_text: str, answer_value: Any, question_id: str) -> str:
		"""Format a single answer based on its type"""
		try:
			if isinstance(answer_value, dict):
				# Handle complex answers (like text input with multiple fields)
				if len(answer_value) == 1 and 'value' in answer_value:
					return f'**Q{question_id}:** {question_text}\n**Answer:** {answer_value["value"]}'
				else:
					answer_parts = []
					for key, value in answer_value.items():
						answer_parts.append(f'  • {key}: {value}')
					return f'**Q{question_id}:** {question_text}\n**Answer:**\n' + '\n'.join(answer_parts)

			elif isinstance(answer_value, list):
				# Handle multiple choice answers
				answer_list = '  • ' + '\n  • '.join(str(item) for item in answer_value)
				return f'**Q{question_id}:** {question_text}\n**Selected options:**\n{answer_list}'

			elif isinstance(answer_value, str):
				# Handle text answers
				return f'**Q{question_id}:** {question_text}\n**Answer:** {answer_value}'

			elif isinstance(answer_value, (int, float)):
				# Handle numeric answers (ratings, scales)
				return f'**Q{question_id}:** {question_text}\n**Rating/Value:** {answer_value}'

			else:
				# Handle any other type
				return f'**Q{question_id}:** {question_text}\n**Answer:** {str(answer_value)}'

		except Exception as e:
			logger.warning(f'Error formatting answer for question {question_id}: {e}')
			return f'**Q{question_id}:** {question_text}\n**Answer:** {str(answer_value)}'

	def _get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
		"""Get recent conversation history for AI context"""
		print(f'📚 [SurveyProcessor._get_conversation_history] Getting conversation history for {conversation_id} (limit: {limit})')
		try:
			# Get conversation messages (implement based on your conversation message structure)
			# This is a placeholder - adjust based on your actual conversation message model
			conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
			if not conversation:
				print(f'❌ [SurveyProcessor._get_conversation_history] Conversation {conversation_id} not found')
				return []

			print(f'✅ [SurveyProcessor._get_conversation_history] Conversation found: {conversation.id}')
			# For now, return empty list - implement based on your message structure
			# You might have a separate message table or field in conversation
			print(f'⚠️ [SurveyProcessor._get_conversation_history] Message history not implemented yet, returning empty list')
			return []

		except Exception as e:
			print(f'❌ [SurveyProcessor._get_conversation_history] Error getting conversation history: {str(e)}')
			logger.error(f'Error getting conversation history: {e}')
			return []

	async def format_survey_response_as_human_message(self, request: ParseSurveyResponseRequest, user_id: str) -> str:
		"""
		Format survey response as a human message for AI processing
		This is a simpler version that just converts to text without AI integration

		Args:
		    request: Survey response data
		    user_id: User ID

		Returns:
		    Formatted human message text
		"""
		print(f'💬 [SurveyProcessor.format_survey_response_as_human_message] Formatting survey as human message for user {user_id}')
		try:
			# Store the survey response first
			print(f'💾 [SurveyProcessor.format_survey_response_as_human_message] Storing survey response...')
			self.question_session_repo.parse_survey_response(request, user_id)

			# Convert to human text
			print(f'🔤 [SurveyProcessor.format_survey_response_as_human_message] Converting to human text...')
			human_text = self._convert_responses_to_human_text(request.answers, request.conversation_id, user_id)

			# Add a friendly introduction
			introduction = f'I have completed a survey. Here are my responses:\n\n'
			result = introduction + human_text

			print(f'✅ [SurveyProcessor.format_survey_response_as_human_message] Formatted message generated ({len(result)} characters)')
			return result

		except Exception as e:
			error_message = f'I completed a survey, but there was an error processing the responses: {str(e)}'
			print(f'❌ [SurveyProcessor.format_survey_response_as_human_message] Error: {str(e)}')
			logger.error(f'Error formatting survey response as human message: {e}')
			return error_message

	async def send_survey_response_to_chat_via_websocket(
		self,
		websocket_connection,
		survey_result: Dict[str, Any],
		conversation_id: str,
		user_id: str,
	) -> bool:
		"""
		Send processed survey response to chat via WebSocket

		Args:
		    websocket_connection: WebSocket connection
		    survey_result: Result from survey processing
		    conversation_id: Conversation ID
		    user_id: User ID

		Returns:
		    Success status
		"""
		print(f'🌐 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Sending survey response to chat via WebSocket')
		print(f'📡 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Conversation: {conversation_id}, User: {user_id}')

		try:
			if not websocket_connection or not hasattr(websocket_connection, 'send_json'):
				print(f'❌ [SurveyProcessor.send_survey_response_to_chat_via_websocket] Invalid WebSocket connection')
				logger.warning('Invalid WebSocket connection for survey response')
				return False

			# Extract human message and AI response
			human_message = survey_result.get('human_readable_response')
			ai_response = survey_result.get('ai_response')

			print(f'📄 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Human message available: {bool(human_message)}')
			print(f'🤖 [SurveyProcessor.send_survey_response_to_chat_via_websocket] AI response available: {bool(ai_response)}')

			if human_message:
				# Send human message first
				human_ws_message = {
					'type': 'chat_message',
					'role': 'user',
					'content': human_message,
					'conversation_id': conversation_id,
					'user_id': user_id,
					'source': 'survey_completion',
					'timestamp': datetime.now().isoformat(),
				}

				print(f'📤 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Sending human message ({len(human_message)} chars)...')
				await websocket_connection.send_json(human_ws_message)
				print(f'✅ [SurveyProcessor.send_survey_response_to_chat_via_websocket] Human message sent successfully')
				logger.info(f'Survey human message sent via WebSocket for conversation {conversation_id}')

			if ai_response:
				# Send AI response after a short delay
				import asyncio

				print(f'⏳ [SurveyProcessor.send_survey_response_to_chat_via_websocket] Waiting 1 second before sending AI response...')
				await asyncio.sleep(1)  # 1 second delay

				ai_ws_message = {
					'type': 'chat_message',
					'role': 'assistant',
					'content': ai_response,
					'conversation_id': conversation_id,
					'user_id': user_id,
					'source': 'survey_analysis',
					'timestamp': datetime.now().isoformat(),
				}

				print(f'📤 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Sending AI response ({len(ai_response)} chars)...')
				await websocket_connection.send_json(ai_ws_message)
				print(f'✅ [SurveyProcessor.send_survey_response_to_chat_via_websocket] AI response sent successfully')
				logger.info(f'Survey AI response sent via WebSocket for conversation {conversation_id}')

			print(f'🎉 [SurveyProcessor.send_survey_response_to_chat_via_websocket] All messages sent successfully!')
			return True

		except Exception as e:
			print(f'💥 [SurveyProcessor.send_survey_response_to_chat_via_websocket] Error: {str(e)}')
			logger.error(f'Error sending survey response via WebSocket: {e}')
			return False
