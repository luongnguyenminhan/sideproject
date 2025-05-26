import asyncio
import json
import logging
import os
from datetime import datetime

from celery import Task
from pytz import timezone

from app.core.database import SessionLocal
from app.enums.meeting_enums import TokenOperationTypeEnum
from app.jobs.celery_worker import celery_app  # Import celery app directly
from app.modules.meeting_calendar.repository.calendar_event_repo import (
	CalendarEventRepo,
)
from app.modules.meeting_files.dal.meeting_file_dal import MeetingFileDAL
from app.modules.meeting_transcripts.dal.transcript_dal import TranscriptDAL
from app.modules.meetings.dal.meeting_dal import MeetingDAL
from app.modules.meetings.dal.token_usage_dal import TokenUsageDAL
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.utils.agent_open_ai_api import AgentMicroService

logger = logging.getLogger(__name__)


class CallbackTask(Task):
	def on_success(self, retval, task_id, args, kwargs):
		"""
		retval – The return value of the task.
		task_id – Unique id of the executed task.
		args – Original arguments for the executed task.
		kwargs – Original keyword arguments for the executed task.
		"""
		logger.debug(f'Task {task_id} succeeded with result: {retval}')
		pass

	def on_failure(self, exc, task_id, args, kwargs, einfo):
		"""
		exc – The exception raised by the task.
		task_id – Unique id of the failed task.
		args – Original arguments for the task that failed.
		kwargs – Original keyword arguments for the task that failed.
		"""
		logger.debug(f'Task {task_id} failed with exception: {exc}')
		pass


@celery_app.task(
	bind=True,
	base=CallbackTask,
	autoretry_for=(Exception,),
	retry_backoff=True,
	retry_kwargs={'max_retries': 1},
)
def process_audio_task(
	self,
	audio_file_path: str,
	transcript_id: str,
	meeting_id: str,
	user_id: str,
	file_id: str,
):
	"""Xử lý file âm thanh để chuyển thành văn bản trong background task

	Args:
	    audio_file_path (str): Đường dẫn đến file âm thanh
	    transcript_id (str): ID của bản ghi transcript
	    meeting_id (str): ID cuộc họp
	    user_id (str): ID người dùng
	    file_id (str): ID của file âm thanh

	Returns:
	    dict: Kết quả xử lý gồm transcript_id, kết quả văn bản và thông tin token
	"""
	try:
		# Verify the audio file exists before processing
		if not os.path.exists(audio_file_path):
			logger.error(f'Audio file not found at path: {audio_file_path}')
			result = {
				'status': 'failed',
				'transcript_id': transcript_id,
				'meeting_id': meeting_id,
				'user_id': user_id,
				'file_id': file_id,
				'error': f'Audio file not found at path: {audio_file_path}',
			}
			update_transcript_from_result.apply_async(
				args=[json.dumps(result)],
				retry=True,
				retry_policy={
					'max_retries': 3,
					'interval_start': 60,
					'interval_step': 60,
					'interval_max': 300,
				},
			)
			return result

		# Check file size to ensure it's a valid audio file
		file_size = os.path.getsize(audio_file_path)
		if file_size == 0:
			logger.error(f'Audio file is empty: {audio_file_path}')
			result = {
				'status': 'failed',
				'transcript_id': transcript_id,
				'meeting_id': meeting_id,
				'user_id': user_id,
				'file_id': file_id,
				'error': 'Audio file is empty or corrupted',
			}
			update_transcript_from_result.apply_async(
				args=[json.dumps(result)],
				retry=True,
				retry_policy={
					'max_retries': 3,
					'interval_start': 60,
					'interval_step': 60,
					'interval_max': 300,
				},
			)
			return result

		# Log that we've confirmed the file exists
		logger.info(f'Audio file confirmed at path: {audio_file_path} (Size: {file_size} bytes)')

		# Khởi tạo dịch vụ speech-to-text
		agent_service = AgentMicroService()
		logger.debug(f'Processing audio file: {audio_file_path}')
		# Xử lý file âm thanh (quá trình này có thể mất nhiều thời gian)
		audio_result = asyncio.run(agent_service.process_audio(audio_path=audio_file_path))
		logger.debug(f'Audio processing result: {audio_result}')
		if not audio_result:
			logger.error(f'Failed to process audio file: {audio_file_path}')
			result = {
				'status': 'failed',
				'transcript_id': transcript_id,
				'meeting_id': meeting_id,
				'user_id': user_id,
				'file_id': file_id,
				'error': 'Audio processing failed',
			}
		else:
			# Trích xuất nội dung và thông tin token
			transcript_content = audio_result['transcript']
			token_data = audio_result['tokens']

			# Chuẩn bị kết quả để đưa vào hàng đợi
			result = {
				'status': 'success',
				'transcript_id': transcript_id,
				'meeting_id': meeting_id,
				'user_id': user_id,
				'file_id': file_id,
				'transcript_content': transcript_content,
				'token_usage': {
					'input_tokens': (token_data if not isinstance(token_data, dict) else token_data.get('input_tokens', 0)),
					'output_tokens': (0 if not isinstance(token_data, dict) else token_data.get('output_tokens', 0)),
					'context_tokens': (0 if not isinstance(token_data, dict) else token_data.get('context_tokens', 0)),
					'price_vnd': 0,
				},
			}
			print(f'Result: {json.dumps(result, indent=4)}')

		# Đưa kết quả vào hàng đợi để worker cập nhật database
		# Chúng ta có thể sử dụng Redis pub/sub hoặc hàng đợi Celery khác
		# Trong trường hợp này, sẽ sử dụng một task Celery khác
		# Apply async task with retry policy
		update_transcript_from_result.apply_async(
			args=[json.dumps(result)],
			retry=True,
			retry_policy={
				'max_retries': 3,
				'interval_start': 60,
				'interval_step': 60,
				'interval_max': 300,
			},
		)
		return result

	except Exception as ex:
		logger.error(f'Background audio processing failed: {ex}')
		result = {
			'status': 'failed',
			'transcript_id': transcript_id,
			'meeting_id': meeting_id,
			'user_id': user_id,
			'error': str(ex),
		}
		update_transcript_from_result.apply_async(
			args=[json.dumps(result)],
			retry=True,
			retry_policy={
				'max_retries': 3,
				'interval_start': 60,
				'interval_step': 60,
				'interval_max': 300,
			},
		)
		return result


@celery_app.task(
	bind=True,
	base=CallbackTask,
	autoretry_for=(Exception,),
	retry_backoff=True,
	retry_kwargs={'max_retries': 1},
)
def update_transcript_from_result(self, result_json: str):
	"""Cập nhật kết quả xử lý âm thanh vào database

	Args:
	    result_json (str): Chuỗi JSON chứa kết quả xử lý âm thanh
	"""

	try:
		# Parse JSON result
		result = json.loads(result_json)

		# Tạo session database mới
		db = SessionLocal()
		transcript_dal = TranscriptDAL(db)
		token_usage_dal = TokenUsageDAL(db)
		user_logs_dal = UserLogDAL(db)
		meeting_file_dal = MeetingFileDAL(db)

		transcript_id = result.get('transcript_id')
		meeting_id = result.get('meeting_id')
		user_id = result.get('user_id')
		status = result.get('status')
		file_id = result.get('file_id')
		# Kiểm tra trạng thái của transcript

		if status == 'success':
			# Cập nhật nội dung transcript
			transcript_content = {'text': result.get('transcript_content')}
			transcript_dal.update(
				transcript_id,
				{'content': {'text': transcript_content}, 'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh'))},
			)
			logger.debug(f'Transcript updated successfully for ID: {transcript_id}')

			meeting_file_dal.update(
				file_id,
				{'processing_status': 'completed', 'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh'))},
			)
			logger.debug(f'Meeting file updated successfully for ID: {file_id}')

			# update meeting status
			meeting_dal = MeetingDAL(db)
			meeting_dal.update(
				meeting_id,
				{'status': 'completed', 'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh'))},
			)
			logger.debug(f'Meeting updated successfully for ID: {meeting_id}')

			# Tạo bản ghi sử dụng token
			token_usage = result.get('token_usage')
			token_usage_data = {
				'user_id': user_id,
				'meeting_id': meeting_id,
				'operation_type': TokenOperationTypeEnum.TRANSCRIPTION.value,
				'input_tokens': token_usage.get('input_tokens', 0),
				'output_tokens': token_usage.get('output_tokens', 0),
				'context_tokens': token_usage.get('context_tokens', 0),
				'price_vnd': token_usage.get('price_vnd', 0),
			}
			token_usage_dal.create(token_usage_data)
			logger.debug(f'Token usage recorded successfully for user ID: {user_id}')

			# Log thông tin hoàn thành
			user_logs_dal.create({
				'user_id': user_id,
				'action': 'transcript_creation_completed',
				'details': f'Successfully transcribed audio for meeting {meeting_id}',
			})
			db.commit()

		else:
			# Cập nhật transcript với trạng thái lỗi
			error_msg = result.get('error', 'Unknown error')
			transcript_dal.update(
				transcript_id,
				{
					'content': {
						'text': """LỖI [00/00/0000 00:00:00] \n
					Không thể tạo bản ghi âm thanh từ file này. Vui lòng kiểm tra lại file âm thanh hoặc thử lại sau."""
					},
					'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				},
			)

			meeting_file_dal.update(
				file_id,
				{
					'processing_status': 'failed',
					'processing_error': error_msg,
					'update_date': datetime.now(timezone('Asia/Ho_Chi_Minh')),
				},
			)

			# Log thông tin lỗi
			user_logs_dal.create({
				'user_id': user_id,
				'action': 'transcript_creation_failed',
				'details': f'Failed to transcribe audio: {error_msg}',
			})
			db.commit()
		# Commit các thay đổi
		logger.debug(f'Database changes committed successfully for transcript ID: {transcript_id}')
		calendar_repo = CalendarEventRepo(db)
		result = calendar_repo.sync_meeting_to_calendar(meeting_id)
		logger.debug(f'Calendar sync result: {result}')
		db.commit()

	except Exception as ex:
		logger.error(f'Failed to update transcript from result: {ex}')
		# Đảm bảo session được đóng trong trường hợp lỗi
		if 'db' in locals():
			db.close()
	finally:
		# Đóng session
		if 'db' in locals():
			db.close()
