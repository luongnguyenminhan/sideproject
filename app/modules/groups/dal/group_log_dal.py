"""Data Access Layer for GroupLog operations"""

from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.modules.groups.models.group_log import GroupLog


class GroupLogDAL(BaseDAL[GroupLog]):
	"""GroupLogDAL for interacting with group_logs table"""

	def __init__(self, db_session: Session):
		super().__init__(GroupLog, db_session)
