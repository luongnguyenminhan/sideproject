"""Order model for subscription payments"""

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.base_model import BaseEntity
from app.enums.subscription_enums import OrderStatusEnum, RankEnum


class Order(BaseEntity):
    """Order model for subscription payments"""
    
    __tablename__ = "subscription_orders"
    
    # Link to user who created the order
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="subscription_orders")
    
    # Order details
    order_code = Column(String(50), nullable=False, unique=True, index=True)
    rank_type = Column(Enum(RankEnum), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.PENDING)
    
    # PayOS related fields
    payment_link_id = Column(String(100), nullable=True)
    checkout_url = Column(String(500), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    expired_at = Column(DateTime, nullable=False)  # When the payment link expires
    activated_at = Column(DateTime, nullable=True)  # When the subscription starts
    expired_subscription_at = Column(DateTime, nullable=True)  # When the subscription ends
    
    # Cancel reason if applicable
    cancel_reason = Column(String(255), nullable=True)
