"""Rank Repository"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.modules.subscription.dal.rank_dal import RankDAL
from app.modules.subscription.models.rank import Rank
from app.enums.subscription_enums import RankEnum
from app.modules.subscription.schemas.subscription_schemas import RankCreate


class RankRepository(BaseRepo):
    """Repository for Rank operations"""

    def __init__(self, db: Session):
        self.db = db
        self.dal = RankDAL(db)

    def get_by_id(self, rank_id: str) -> Optional[Rank]:
        """Get rank by ID"""
        return self.dal.get_by_id(rank_id)

    def get_by_name(self, name: RankEnum) -> Optional[Rank]:
        """Get rank by name"""
        return self.dal.get_by_name(name)

    def get_all_ranks(self) -> List[Rank]:
        """Get all ranks"""
        return self.dal.get_all_ranks()

    def create_rank(self, rank_data: RankCreate) -> Rank:
        """Create a new rank"""
        return self.dal.create(rank_data.model_dump())

    def update_rank(self, rank_id: str, rank_data: dict) -> Optional[Rank]:
        """Update a rank"""
        return self.dal.update(rank_id, rank_data)
