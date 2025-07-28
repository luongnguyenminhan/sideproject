# Payment Repository
"""
Repository layer for Payment module that coordinates between service and DAL.
"""
from typing import Dict, Any, Optional, Union, List
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.core.database import get_db
from app.modules.payment.dal.payment_dal import PaymentDAL
from app.modules.payment.services.payment_service import PaymentService
from app.modules.payment.schemas.payment_schemas import (
    CreatePaymentRequest,
    WebhookVerifyRequest,
    WebhookData,
)
from app.modules.payment.models.payment import Payment, PaymentStatus


class PaymentRepo(BaseRepo):
    """Repository for payment operations"""
    
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.dal = PaymentDAL(db)
        self.service = PaymentService(db)
    
    def create_payment_link(self, request: CreatePaymentRequest, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a payment link"""
        return self.service.create_payment_link(
            order_code=request.order_code,
            amount=request.amount,
            description=request.description,
            items=request.items,
            cancel_url=request.cancel_url,
            return_url=request.return_url,
            user_id=user_id
        )
    
    def get_payment_information(self, order_id: Union[str, int]) -> Dict[str, Any]:
        """Get payment information"""
        return self.service.get_payment_link_information(order_id)
    
    def cancel_payment(self, order_id: Union[str, int], cancellation_reason: str) -> Dict[str, Any]:
        """Cancel a payment"""
        return self.service.cancel_payment_link(order_id, cancellation_reason)
    
    def confirm_webhook_url(self, request: WebhookVerifyRequest) -> str:
        """Confirm a webhook URL"""
        return self.service.confirm_webhook(request.webhook_url)
    
    def verify_payment_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify payment webhook data"""
        return self.service.verify_payment_webhook(webhook_data)
    
    def get_user_payments(self, user_id: str, limit: int = 10, offset: int = 0) -> List[Payment]:
        """Get payments for a specific user"""
        return self.db.query(Payment).filter(Payment.user_id == user_id).order_by(
            Payment.created_at.desc()
        ).limit(limit).offset(offset).all()
    
    def get_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get a payment by ID"""
        return self.dal.get_by_id(payment_id)
    
    def get_payment_by_order_code(self, order_code: int) -> Optional[Payment]:
        """Get a payment by order code"""
        return self.dal.get_payment_by_order_code(order_code)
    
    def get_payment_by_payment_link_id(self, payment_link_id: str) -> Optional[Payment]:
        """Get a payment by payment link ID"""
        return self.dal.get_payment_by_payment_link_id(payment_link_id)
