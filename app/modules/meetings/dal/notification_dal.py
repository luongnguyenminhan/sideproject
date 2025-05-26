"""Notification data access layer"""

from typing import List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.meetings.models.notification import Notification


class NotificationDAL(BaseDAL[Notification]):
	"""NotificationDAL for database operations on notifications"""

	def __init__(self, db: Session):
		"""Initialize the NotificationDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, Notification)

	def get_user_notifications(self, user_id: str, include_read: bool = False) -> List[Notification]:
		"""Get all notifications for a user

		Args:
		    user_id (str): User ID
		    include_read (bool): Whether to include read notifications

		Returns:
		    List[Notification]: List of notifications
		"""
		query = self.db.query(Notification).filter(and_(Notification.user_id == user_id, Notification.is_deleted == False))

		if not include_read:
			query = query.filter(not Notification.is_read)

		return query.order_by(Notification.create_date.desc()).all()

	def get_meeting_notifications(self, meeting_id: str) -> List[Notification]:
		"""Get all notifications for a meeting

		Args:
		    meeting_id (str): Meeting ID

		Returns:
		    List[Notification]: List of notifications
		"""
		return (
			self.db.query(Notification)
			.filter(
				and_(
					Notification.meeting_id == meeting_id,
					Notification.is_deleted == False,
				)
			)
			.order_by(Notification.create_date.desc())
			.all()
		)

	def mark_as_read(self, notification_id: str) -> Notification | None:
		"""Mark a notification as read

		Args:
		    notification_id (str): Notification ID

		Returns:
		    Optional[Notification]: Updated notification if found, None otherwise
		"""
		return self.update(notification_id, {'is_read': True})

	def mark_all_as_read(self, user_id: str) -> int:
		"""Mark all notifications for a user as read

		Args:
		    user_id (str): User ID

		Returns:
		    int: Number of notifications marked as read
		"""
		unread_notifications = (
			self.db.query(Notification)
			.filter(
				and_(
					Notification.user_id == user_id,
					not Notification.is_read,
					Notification.is_deleted == False,
				)
			)
			.all()
		)

		count = 0
		for notification in unread_notifications:
			self.update(notification.id, {'is_read': True})
			count += 1

		return count
