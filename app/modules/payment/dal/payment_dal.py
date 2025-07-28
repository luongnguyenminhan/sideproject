# Payment Data Access Layer
"""
Data access layer for Payment module.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.payment.models.payment import Payment, PaymentStatus


class PaymentDAL(BaseDAL):
    """Data Access Layer for Payment operations"""
    def __init__(self, db: Session):
        super().__init__(db, Payment)
    
    def create_payment(self, payment_data: dict) -> Payment:
        """Create a new payment record"""
        payment = Payment(**payment_data)
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def get_payment_by_order_code(self, order_code: int) -> Payment:
        """Get payment by order code"""
        return self.db.query(Payment).filter(Payment.order_code == order_code).first()
    
    def get_payment_by_payment_link_id(self, payment_link_id: str) -> Payment:
        """Get payment by PayOS payment link ID"""
        return self.db.query(Payment).filter(Payment.payment_link_id == payment_link_id).first()
    
    def update_payment_status(self, payment_id: str, status: PaymentStatus, **kwargs) -> Payment:
        """Update payment status and related fields"""
        payment = self.get_by_id(payment_id)
        if not payment:
            return None
        
        payment.status = status
        
        # Update timestamp based on status
        if status == PaymentStatus.COMPLETED:
            payment.completed_at = datetime.utcnow()
        elif status == PaymentStatus.CANCELLED:
            payment.cancelled_at = datetime.utcnow()
        
        # Update any additional fields passed as kwargs
        for key, value in kwargs.items():
            if hasattr(payment, key):
                setattr(payment, key, value)
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def update_payment_from_webhook(self, payment_link_id: str, webhook_data: dict) -> Payment:
        """Update payment with webhook data after successful payment"""
        payment = self.get_payment_by_payment_link_id(payment_link_id)
        if not payment:
            return None
        
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        
        # Update with transaction details
        payment.reference = webhook_data.get("reference")
        payment.transaction_date_time = datetime.fromisoformat(webhook_data.get("transactionDateTime").replace(" ", "T"))
        payment.counter_account_bank_id = webhook_data.get("counterAccountBankId")
        payment.counter_account_bank_name = webhook_data.get("counterAccountBankName")
        payment.counter_account_name = webhook_data.get("counterAccountName")
        payment.counter_account_number = webhook_data.get("counterAccountNumber")
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
