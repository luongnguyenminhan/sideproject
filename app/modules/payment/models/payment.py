# Payment Module Models
"""
Database models for the Payment module.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.core.base_model import BaseModel


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration"""
    CREATED = "created"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Payment(BaseModel):
    """Payment model for storing payment information"""
    __tablename__ = "payments"

    order_code = Column(Integer, nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    payment_link_id = Column(String(255), nullable=True, index=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.CREATED)
    checkout_url = Column(Text, nullable=True)
    qr_code = Column(Text, nullable=True)
    currency = Column(String(10), default="VND")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Payment transaction information after successful payment
    reference = Column(String(255), nullable=True)
    transaction_date_time = Column(DateTime, nullable=True)
    counter_account_bank_id = Column(String(255), nullable=True)
    counter_account_bank_name = Column(String(255), nullable=True)
    counter_account_name = Column(String(255), nullable=True)
    counter_account_number = Column(String(255), nullable=True)
    
    # Payment timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
