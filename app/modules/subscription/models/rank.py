"""Rank model"""

from sqlalchemy import Column, String, JSON, Enum
from app.core.base_model import BaseEntity
from app.enums.subscription_enums import RankEnum


class Rank(BaseEntity):
    """Rank model representing subscription tiers"""
    
    __tablename__ = "ranks"
    
    name = Column(Enum(RankEnum), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=False)
    benefits = Column(JSON, nullable=False)  # Store benefits as JSON
    price = Column(String(20), nullable=False)  # Store as string to handle currency formatting
