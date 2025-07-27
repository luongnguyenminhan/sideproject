"""Rank DAL"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.subscription.models.rank import Rank
from app.enums.subscription_enums import RankEnum


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
