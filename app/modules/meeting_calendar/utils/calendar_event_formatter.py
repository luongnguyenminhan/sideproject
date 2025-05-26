"""Utility functions for formatting Google Calendar event descriptions"""

import json
import logging
from typing import Dict, List

from sqlalchemy import and_

from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meeting_files.models.meeting_file import MeetingFile
from app.modules.meeting_transcripts.dal.transcript_dal import TranscriptDAL
from app.modules.meeting_transcripts.models.transcript import Transcript
from app.modules.meetings.dal.meeting_note_dal import MeetingNoteDAL
from app.modules.meetings.models.meeting import Meeting
from app.modules.meetings.models.meeting_note import MeetingItem

logger = logging.getLogger(__name__)


def format_event_description(
	meeting: Meeting,
	transcript_dal: TranscriptDAL = None,
	meeting_file_dal: MeetingFileDAL = None,
	meeting_note_dal: MeetingNoteDAL = None,
	db=None,
) -> str:
	"""Format event description with meeting details and links to resources

	Args:
	    meeting (Meeting): Meeting object
	    transcript_dal: Transcript data access layer
	    meeting_file_dal: Meeting file data access layer
	    meeting_note_dal: Meeting note data access layer
	    db: Database session

	Returns:
	    str: Formatted event description
	"""
	# Start with basic description
	description = meeting.description or ''

	# Add separator if needed
	if description and not description.endswith('\n'):
		description += '\n\n'
	elif not description:
		description = ''

	# Add meeting details section
	description += '--- Chi Tiết Cuộc Họp ---\n'
	description += f'Mã Cuộc Họp: {meeting.id}\n'
	if meeting.platform:
		description += f'Nền Tảng: {meeting.platform}\n'
	if meeting.meeting_link:
		description += f'Đường Dẫn Cuộc Họp: {meeting.meeting_link}\n'

	# Add transcript information if available
	description = add_transcript_info(description, meeting, transcript_dal)

	# Add meeting notes information if available
	description = add_meeting_notes(description, meeting, meeting_note_dal, db)

	# Add meeting files information if available
	description = add_meeting_files(description, meeting, meeting_file_dal)

	return description


def add_transcript_info(description: str, meeting: Meeting, transcript_dal: TranscriptDAL) -> str:
	"""Add transcript information to the event description

	Args:
	    description (str): Current event description
	    meeting (Meeting): Meeting object
	    transcript_dal: Transcript data access layer

	Returns:
	    str: Updated event description with transcript information
	"""
	if not transcript_dal:
		return description

	transcripts: List[Transcript] = transcript_dal.get_meeting_transcripts(meeting.id)
	if transcripts:
		description += '\n--- Bản Ghi ---\n'
		for transcript in transcripts:
			# Add link to transcript in the system
			description += f'Bản Ghi: meobeo.ai/transcripts/{transcript.id}\n'
			description += f'Ngôn Ngữ: {transcript.language}\n'
			description += f'Nguồn: {transcript.source}\n'

	return description


def add_meeting_notes(description: str, meeting: Meeting, meeting_note_dal: MeetingNoteDAL, db) -> str:
	"""Add meeting notes information to the event description

	Args:
	    description (str): Current event description
	    meeting (Meeting): Meeting object
	    meeting_note_dal: Meeting note data access layer
	    db: Database session

	Returns:
	    str: Updated event description with meeting notes
	"""
	if not meeting_note_dal:
		return description

	latest_note = meeting_note_dal.get_latest_note(meeting.id)

	if latest_note:
		description += '\n--- Ghi Chú Cuộc Họp ---\n'
		description += f'Ghi Chú Cuộc Họp: meobeo.ai/meeting-notes/{latest_note.id}\n'
		description += f'Phiên Bản: {latest_note.version}\n'

		# Get meeting items (decisions, tasks, questions)
		if db:
			meeting_items: List[MeetingItem] = (
				db.query(MeetingItem)
				.filter(
					and_(
						MeetingItem.meeting_note_id == latest_note.id,
						MeetingItem.is_deleted == False,
					)
				)
				.all()
			)

			if meeting_items:
				# Group items by type
				items_by_type: Dict[str, List[MeetingItem]] = {}
				for item in meeting_items:
					if item.type not in items_by_type:
						items_by_type[item.type] = []
					items_by_type[item.type].append(item)

				# Add details for each type of item
				for item_type, items in items_by_type.items():
					if item_type.lower() == 'action_item':
						description += f'\nNhiệm Vụ ({len(items)}):\n'
					elif item_type.lower() == 'question':
						description += f'\nCâu Hỏi ({len(items)}):\n'
					elif item_type.lower() == 'decision':
						description += f'\nQuyết Định ({len(items)}):\n'
					else:
						description += f'\n{item_type.capitalize()} ({len(items)}):\n'

					# Format each item
					description = format_meeting_items(description, items, item_type)

	return description


def format_meeting_items(description: str, items: List[MeetingItem], item_type: str) -> str:
	"""Format meeting items for the event description

	Args:
	    description (str): Current event description
	    items (List[MeetingItem]): List of meeting items to format
	    item_type (str): Type of meeting items

	Returns:
	    str: Updated event description with formatted items
	"""
	for i, item in enumerate(items, 1):
		try:
			# Parse JSON content
			try:
				content = item.content
				if isinstance(content, str):
					content = json.loads(content)
			except json.JSONDecodeError:
				if isinstance(item.content, dict):
					content = item.content
				else:
					content = {'content': str(item.content)}

			# Handle different item types
			if item_type.lower() == 'action_item':
				description += f'{i}. Nhiệm Vụ: {content.get("task", "N/A")}\n'
				if content.get('assignee'):
					description += f'   Người Được Giao: {content.get("assignee")}\n'
				if content.get('status'):
					description += f'   Trạng Thái: {content.get("status")}\n'
				deadline = content.get('deadline')
				if deadline and isinstance(deadline, str) and deadline.strip():
					description += f'   Hạn Chót: {deadline}\n'

			elif item_type.lower() == 'question':
				description += f'{i}. Hỏi: {content.get("question", "N/A")}\n'
				if content.get('answer'):
					description += f'   Đáp: {content.get("answer", "N/A")[:100]}...\n'
				if content.get('asker'):
					description += f'   Người Hỏi: {content.get("asker")}\n'

			elif item_type.lower() == 'decision':
				description += f'{i}. {content.get("decision", "N/A")}\n'
				if content.get('deciders'):
					description += f'   Người Quyết Định: {content.get("deciders")}\n'

			else:
				# Generic handling for other types
				description += f'{i}. {json.dumps(content, ensure_ascii=False)[:100]}...\n'

		except Exception as e:
			description += f'{i}. [Lỗi phân tích nội dung: {str(e)}]\n'

		# Add separator between items
		if i < len(items):
			description += '\n'

	return description


def add_meeting_files(description: str, meeting: Meeting, meeting_file_dal: MeetingFileDAL) -> str:
	"""Add meeting files information to the event description

	Args:
	    description (str): Current event description
	    meeting (Meeting): Meeting object
	    meeting_file_dal: Meeting file data access layer

	Returns:
	    str: Updated event description with meeting files
	"""
	if not meeting_file_dal:
		return description

	files: List[MeetingFile] = meeting_file_dal.get_meeting_files(meeting.id)
	if files:
		description += '\n--- Tệp Cuộc Họp ---\n'

		# Group files by type
		files_by_type = {}
		for file in files:
			if file.file_type not in files_by_type:
				files_by_type[file.file_type] = []
			files_by_type[file.file_type].append(file)

		# Display files by type
		for file_type, file_list in files_by_type.items():
			if file_type.lower() == 'audio':
				file_type_vi = 'Âm Thanh'
			elif file_type.lower() == 'video':
				file_type_vi = 'Video'
			elif file_type.lower() == 'document':
				file_type_vi = 'Tài Liệu'
			elif file_type.lower() == 'image':
				file_type_vi = 'Hình Ảnh'
			else:
				file_type_vi = file_type.capitalize()

			description += f'Tệp {file_type_vi} ({len(file_list)}):\n'
			for file in file_list:
				if file.object_name:
					# Generate secure public download link
					public_link = meeting_file_dal.generate_public_download_link(file.id)
					file_name = file.object_name.split('/')[-1] if '/' in file.object_name else file.object_name
					description += f'- {file_name}: {public_link}\n'

					if file.file_size_bytes:
						size_in_mb = file.file_size_bytes / (1024 * 1024)
						description += f'  Kích Thước: {size_in_mb:.2f} MB\n'
					if file.duration_seconds and file.file_type == 'AUDIO':
						minutes = file.duration_seconds // 60
						seconds = file.duration_seconds % 60
						description += f'  Thời Lượng: {minutes} phút {seconds} giây\n'

	return description
