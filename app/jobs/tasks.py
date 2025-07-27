import asyncio
import json
import logging
import os
from datetime import datetime

from celery import Task, schedules
from celery.schedules import crontab
from pytz import timezone

from app.core.database import SessionLocal
from app.enums.meeting_enums import TokenOperationTypeEnum
from app.jobs.celery_worker import celery_app  # Import celery app directly
from app.modules.users.dal.user_logs_dal import UserLogDAL
from app.utils.agent_open_ai_api import AgentMicroService
from app.modules.subscription.jobs.check_orders import check_pending_orders

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

# Define the periodic task schedule
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    # Check pending orders every 5 minutes
    sender.add_periodic_task(
        300.0,  # 300 seconds = 5 minutes
        check_subscription_orders.s(),
        name='check-subscription-orders-every-5-minutes'
    )


@celery_app.task(bind=True, base=CallbackTask)
def check_subscription_orders(self):
    """Task to check pending subscription orders"""
    logger.info("Starting scheduled task: check_subscription_orders")
    try:
        check_pending_orders()
        return "Successfully checked pending subscription orders"
    except Exception as e:
        logger.error(f"Error in check_subscription_orders task: {str(e)}", exc_info=True)
        return f"Error checking pending orders: {str(e)}"
