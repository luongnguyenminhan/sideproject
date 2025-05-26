"""Utility functions for meeting notes"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, List

from app.enums.meeting_enums import TokenOperationTypeEnum, NotificationTypeEnum, MeetingItemTypeEnum
from app.modules.meetings.dal.token_usage_dal import TokenUsageDAL
from app.modules.meetings.dal.notification_dal import NotificationDAL
from app.middleware.translation_manager import _

logger = logging.getLogger(__name__)


def create_token_usage(
	token_usage_dal: TokenUsageDAL,
	meeting_id: str,
	user_id: str,
	operation_type: str,
	token_usage: Dict[str, Any],
) -> None:
	"""Create a token usage record

	Args:
	    token_usage_dal: Token usage data access layer
	    meeting_id (str): Meeting ID
	    user_id (str): User ID
	    operation_type (str): Operation type
	    token_usage (Dict[str, Any]): Token usage data
	"""
	token_usage_data = {
		'user_id': user_id,
		'meeting_id': meeting_id,
		'operation_type': operation_type,
		'input_tokens': token_usage.get('input_tokens', 0),
		'output_tokens': token_usage.get('output_tokens', 0),
		'context_tokens': token_usage.get('context_tokens', 0),
		'price_vnd': token_usage.get('price_vnd', 0),
	}

	token_usage_dal.create(token_usage_data)


def create_note_generated_notification(notification_dal: NotificationDAL, meeting_id: str, user_id: str) -> None:
	"""Create a notification for meeting note generation

	Args:
	    notification_dal: Notification data access layer
	    meeting_id (str): Meeting ID
	    user_id (str): User ID
	"""
	notification_data = {
		'user_id': user_id,
		'meeting_id': meeting_id,
		'type': NotificationTypeEnum.NOTE_GENERATED.value,
		'content': _('meeting_note_generated'),
		'is_read': False,
	}

	notification_dal.create(notification_data)


def extract_title_from_note_content(content: str) -> str:
	"""Extract title from meeting note content

	Args:
	    content (str): Meeting note content

	Returns:
	    str: Extracted title or default title
	"""
	title = 'Generated Meeting Note'
	meeting_note_lines = content.split('\n')
	if meeting_note_lines and meeting_note_lines[0].startswith('# '):
		title = meeting_note_lines[0].replace('# ', '').strip()
	return title


def process_response_items(response: Dict[str, Any], current_time: datetime) -> List[Dict[str, Any]]:
	"""Process response items from API and convert to meeting items

	Args:
	    response (Dict[str, Any]): API response
	    current_time (datetime): Current timestamp

	Returns:
	    List[Dict[str, Any]]: List of meeting items ready for database insertion
	"""
	meeting_items = []

	# Process task items
	if 'task_items' in response and response['task_items']:
		for task_item in response['task_items']:
			if 'tasks' in task_item:
				for task in task_item['tasks']:
					meeting_items.append({
						'type': MeetingItemTypeEnum.ACTION_ITEM.value,
						'content': {
							'assignee': task.get('assignee', 'Unassigned'),
							'task': task.get('description', ''),
							'deadline': task.get('deadline', ''),
							'topic': task.get('related_topic', []),
							'status': task.get('status', ''),
							'priority': task.get('priority', ''),
							'dependencies': task.get('dependencies', []),
							'notes': task.get('notes', ''),
						},
						'create_date': current_time,
						'update_date': current_time,
					})

	# Process decisions
	# if 'decision_items' in response and response['decision_items']:
	# 	for decision_item in response['decision_items']:
	# 		if 'decisions' in decision_item:
	# 			for decision in decision_item['decisions']:
	# 				if decision:  # Check if not empty
	# 					meeting_items.append({
	# 						'type': MeetingItemTypeEnum.DECISION.value,
	# 						'content': {
	# 							'topic': decision.get('topic', []),
	# 							'decision': decision.get('description', '') or decision.get('decision', ''),
	# 							'impact': decision.get('impact', ''),
	# 							'stakeholders': decision.get('stakeholders', []),
	# 							'next_steps': decision.get('next_steps', []),
	# 							'context': decision.get('context', ''),
	# 							'timeline': decision.get('timeline', ''),
	# 						},
	# 						'create_date': current_time,
	# 						'update_date': current_time,
	# 					})

	# Process questions
	if 'question_items' in response and response['question_items']:
		for question_item in response['question_items']:
			if 'questions' in question_item:
				for question in question_item['questions']:
					meeting_items.append({
						'type': MeetingItemTypeEnum.QUESTION.value,
						'content': {
							'question': question.get('question', ''),
							'asker': question.get('asker', ''),
							'answer': question.get('answer', ''),
							'answered': question.get('answered', False),
							'topic': question.get('topic', []),
							'context': question.get('context', ''),
						},
						'create_date': current_time,
						'update_date': current_time,
					})

	return meeting_items


def parse_conversation_summary(conversation_summary: str) -> tuple:
	"""Extract title and tags from conversation summary

	Args:
	    conversation_summary (str): Conversation summary text

	Returns:
	    tuple: (title, tags) where title is a string and tags is a list of dictionaries
	"""
	# Extract title - get the first line before "## I."
	title = conversation_summary.split('## I.')[0].strip().split('\n')[0]
	title = re.sub(r'[!@#$%^&*().,<>/?":;\[\]{}\\|`~\-=_+]', '', title).strip()

	# Extract tags from section V.
	extracted = conversation_summary.split('V.')[-1].split('\n')[1:]
	tags = []
	for item in extracted:
		row = re.sub(r'[0-9!@#$%^&*().,<>/?";\[\]{}\\|`~\-=_+]', '', item).strip()
		tag_parts = row.split(':')
		if len(tag_parts) >= 2:
			tag = tag_parts[0].strip()
			value = ':'.join(tag_parts[1:]).strip()
			if value and tag:
				tags.append({'type': tag, 'tag': value})

	return title, tags
