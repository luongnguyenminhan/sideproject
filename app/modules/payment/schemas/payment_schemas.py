# Payment Module Schemas
"""
Request and response schemas for the Payment module.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ItemData(BaseModel):
    """Item data for payment"""
    name: str
    quantity: int
    price: int


class CreatePaymentRequest(BaseModel):
    """Request schema for creating a payment"""
    order_code: int
    amount: int
    description: str
    items: List[ItemData]
    cancel_url: str = Field(..., description="URL to redirect to when payment is cancelled")
    return_url: str = Field(..., description="URL to redirect to when payment is completed")


class PaymentResponse(BaseModel):
    """Response schema for payment information"""
    id: str
    order_code: int
    amount: int
    description: Optional[str] = None
    status: str
    payment_link_id: Optional[str] = None
    checkout_url: Optional[str] = None
    qr_code: Optional[str] = None
    currency: str = "VND"
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class WebhookVerifyRequest(BaseModel):
    """Request schema for webhook verification"""
    webhook_url: str = Field(..., description="URL to verify for webhook")


class TransactionData(BaseModel):
    """Transaction data from webhook"""
    reference: str
    amount: int
    description: str
    transaction_date_time: str
    counter_account_bank_id: Optional[str] = None
    counter_account_bank_name: Optional[str] = None
    counter_account_name: Optional[str] = None
    counter_account_number: Optional[str] = None
    virtual_account_name: Optional[str] = None
    virtual_account_number: Optional[str] = None
    order_code: int
    currency: str
    payment_link_id: str
    code: str
    desc: str


class WebhookData(BaseModel):
    """Webhook data schema"""
    code: str
    desc: str
    success: bool
    data: TransactionData
    signature: str
