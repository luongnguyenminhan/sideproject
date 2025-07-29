"""Subscription schemas"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Union

from pydantic import BaseModel, Field

from app.core.base_model import RequestSchema, ResponseSchema
from app.enums.subscription_enums import RankEnum, OrderStatusEnum


class RankBase(BaseModel):
    """Base Rank schema"""
    name: RankEnum
    description: str
    benefits: Dict[str, Any]
    price: str


class RankCreate(RankBase):
    """Schema for creating a Rank"""
    pass


class RankResponse(RankBase, ResponseSchema):
    """Schema for Rank response"""
    id: str


class UserRankResponse(ResponseSchema):
    """Schema for User's current rank"""
    rank: RankEnum
    description: str
    benefits: Dict[str, Any]
    activated_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    is_active: bool


class OrderBase(BaseModel):
    """Base Order schema"""
    rank_type: RankEnum
    amount: float
    status: OrderStatusEnum


class OrderCreate(RequestSchema):
    """Schema for creating an Order"""
    rank_type: RankEnum = Field(..., description="The subscription rank to purchase")


class UserInfo(BaseModel):
    """Schema for User info in order response"""
    id: str
    profile_picture: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    locale: Optional[str] = None
    google_id: Optional[str] = None
    role: Optional[str] = None
    confirmed: Optional[bool] = None
    fcm_token: Optional[str] = None
    last_login_at: Optional[datetime] = None
    rank: Optional[str] = None
    rank_activated_at: Optional[datetime] = None
    rank_expired_at: Optional[datetime] = None
    create_date: Optional[datetime] = None
    update_date: Optional[datetime] = None
    is_deleted: Optional[bool] = None

class OrderResponse(OrderBase, ResponseSchema):
    """Schema for Order response"""
    id: str
    order_code: str
    user_id: str
    payment_link_id: Optional[str] = None
    checkout_url: Optional[str] = None
    created_at: datetime
    expired_at: datetime
    activated_at: Optional[datetime] = None
    expired_subscription_at: Optional[datetime] = None
    user: Optional[UserInfo] = None




# Response schema for a list of orders
class OrderListResponse(ResponseSchema):
    """Schema for response containing a list of orders (with user info)"""
    orders: List[OrderResponse]


class CountCompletedOrdersResponse(ResponseSchema):
    """Count completed orders response model"""
    
    total_count: int = Field(..., description='Total number of completed orders', examples=[42])


class CreatePaymentResponse(ResponseSchema):
    """Schema for payment link creation response"""
    checkout_url: str
    order_code: str
    expired_at: datetime


class PayOSWebhookRequest(BaseModel):
    """Schema for PayOS webhook request"""
    code: str
    desc: str
    success: bool
    data: Dict[str, Any]
    signature: str
