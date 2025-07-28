# Payment Module Models
"""
Database models for the Payment module.
"""
import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.core.base_model import BaseEntity

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""

    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(BaseEntity):
    """Payment model for storing payment information"""

    __tablename__ = "payments"

    order_code: int = Column(Integer, nullable=False, index=True)
    amount: int = Column(Integer, nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    payment_link_id: Optional[str] = Column(String(255), nullable=True, index=True)
    status: PaymentStatus = Column(Enum(PaymentStatus), default=PaymentStatus.CREATED)
    checkout_url: Optional[str] = Column(Text, nullable=True)
    qr_code: Optional[str] = Column(Text, nullable=True)
    currency: str = Column(String(10), default="VND")
    user_id: Optional[str] = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Payment transaction information after successful payment
    reference: Optional[str] = Column(String(255), nullable=True)
    transaction_date_time: Optional[datetime] = Column(DateTime, nullable=True)
    counter_account_bank_id: Optional[str] = Column(String(255), nullable=True)
    counter_account_bank_name: Optional[str] = Column(String(255), nullable=True)
    counter_account_name: Optional[str] = Column(String(255), nullable=True)
    counter_account_number: Optional[str] = Column(String(255), nullable=True)

    # Payment timestamps
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Optional[datetime] = Column(DateTime, nullable=True)
    cancelled_at: Optional[datetime] = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="payments")
