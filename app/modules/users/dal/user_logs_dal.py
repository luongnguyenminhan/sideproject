"""User logs data access layer"""

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.users.models.user_logs import UserLog


class UserLogDAL(BaseDAL[UserLog]):
	"""UserLogDAL for database operations on user logs"""

	def __init__(self, db: Session):
		"""Initialize the UserLogDAL

		Args:
		    db (Session): Database session
		"""
		super().__init__(db, UserLog)

	def get_user_logs(self, user_id: str):
		"""Get all logs for a user

		Args:
		    user_id (str): User ID

		Returns:
		    List[UserLog]: List of user logs
		"""
		return self.db.query(UserLog).filter(and_(UserLog.user_id == user_id, UserLog.is_deleted == False)).order_by(UserLog.create_date.desc()).all()

	def get_user_logs_by_action(self, user_id: str, action: str):
		"""Get user logs by action

		Args:
		    user_id (str): User ID
		    action (str): Action name

		Returns:
		    List[UserLog]: List of user logs
		"""
		return (
			self.db.query(UserLog)
			.filter(
				and_(
					UserLog.user_id == user_id,
					UserLog.action == action,
					UserLog.is_deleted == False,
				)
			)
			.order_by(UserLog.create_date.desc())
			.all()
		)
