"""Rank DAL"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.subscription.models.rank import Rank
from app.enums.subscription_enums import RankEnum
from ...users.models.users import User


class RankDAL(BaseDAL[Rank]):
    """Data Access Layer for Rank"""

    def __init__(self, db: Session):
        super().__init__(db, Rank)

    def get_by_name(self, name: RankEnum) -> Optional[Rank]:
        """Get rank by name"""
        return self.db.query(self.model).filter(self.model.name == name).first()

    def get_all_ranks(self) -> List[Rank]:
        """Get all ranks"""
        return self.db.query(self.model).all()

    def get_by_user_id(self, user_id: str) -> Optional[Rank]:
        """
        Get the Rank associated with a user by user_id.
        Assumes User.rank is an Enum field referencing RankEnum.
        """

        user = self.db.query(User).filter(User.id == user_id).first()
        if user and user.rank:
            return self.get_by_name(user.rank)
        return None