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

