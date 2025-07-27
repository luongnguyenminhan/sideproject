"""Subscription related enums"""

from enum import Enum


class RankEnum(str, Enum):
    """User rank enumeration"""
    BASIC = "basic"  # Default rank for all users
    PRO = "enterviu_pro"
    ULTRA = "enterviu_ultra"


class OrderStatusEnum(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"  # Order created, waiting for payment
    COMPLETED = "completed"  # Payment successful
    CANCELED = "canceled"  # Order canceled or payment failed/expired
    EXPIRED = "expired"  # Order link expired
