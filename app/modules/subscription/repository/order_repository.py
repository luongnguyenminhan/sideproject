"""Order Repository"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session

from app.core.base_repo import BaseRepo
from app.modules.subscription.dal.order_dal import OrderDAL
from app.modules.subscription.models.order import Order
from app.enums.subscription_enums import OrderStatusEnum, RankEnum
from app.modules.users.models.users import User


class OrderRepository(BaseRepo):
    """Repository for Order operations"""

    def __init__(self, db: Session):
        self.db = db
        self.dal = OrderDAL(db)

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        return self.dal.get_by_id(order_id)

    def get_by_order_code(self, order_code: str) -> Optional[Order]:
        """Get order by order code"""
        return self.dal.get_by_order_code(order_code)
    
    def get_by_payment_link_id(self, payment_link_id: str) -> Optional[Order]:
        """Get order by payment link ID"""
        return self.dal.get_by_payment_link_id(payment_link_id)

    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get all orders for a specific user"""
        return self.dal.get_user_orders(user_id)
    
    def get_user_active_order(self, user_id: str) -> Optional[Order]:
        """Get the user's active subscription order"""
        return self.dal.get_user_active_order(user_id)

    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return self.dal.get_pending_orders()
    
    def get_expired_pending_orders(self) -> List[Order]:
        """Get all pending orders that have passed their expiration date"""
        return self.dal.get_expired_pending_orders()

    def count_completed_orders(self, user_id: str = None, filters: dict = None) -> int:
        """
        Count total number of completed orders with optional filters and user restriction
        
        Args:
            user_id (str): Optional user ID to filter orders for specific user
            filters (dict): Optional filters to apply when counting orders
            
        Returns:
            int: Total count of completed orders matching the criteria
        """
        try:
            params = filters or {}
            result = self.dal.count_completed_orders(user_id, params)
            return result
        except Exception as ex:
            raise ex

    def create_order(self, order_code: int, user_id: str, rank_type: RankEnum, amount: float, payment_data: Dict[str, Any]) -> Order:
        """Create a new order"""
        # Generate a unique order code
        
        # Set expiration time for the payment link (15 minutes)
        expired_at = datetime.now() + timedelta(minutes=15)
        
        order_data = {
            "user_id": user_id,
            "order_code": str(order_code),
            "rank_type": rank_type,
            "amount": amount,
            "status": OrderStatusEnum.PENDING,
            "payment_link_id": payment_data.get("paymentLinkId"),
            "checkout_url": payment_data.get("checkoutUrl"),
            "expired_at": expired_at
        }
        
        return self.dal.create(order_data)

    def update_order_status(self, order_id: str, status: OrderStatusEnum, additional_data: Optional[Dict[str, Any]] = None) -> Optional[Order]:
        """Update order status and additional fields"""
        update_data = {"status": status}
        
        if additional_data:
            update_data.update(additional_data)
            
        return self.dal.update(order_id, update_data)
    
    def mark_order_as_completed(self, order: Order, transaction_id: str) -> Order:
        """Mark an order as completed and update relevant fields"""
        # Set activation and expiration dates for subscription
        activated_at = datetime.now()
        expired_subscription_at = activated_at + timedelta(days=30)  # 1 month subscription
        
        update_data = {
            "status": OrderStatusEnum.COMPLETED,
            "transaction_id": transaction_id,
            "activated_at": activated_at,
            "expired_subscription_at": expired_subscription_at
        }
        
        return self.dal.update(order.id, update_data)
    
    def mark_order_as_canceled(self, order: Order, reason: str = "Order expired") -> Order:
        """Mark an order as canceled"""
        update_data = {
            "status": OrderStatusEnum.CANCELED,
            "cancel_reason": reason
        }
        
        return self.dal.update(order.id, update_data)
    
    def update_user_rank(self, user: User, order: Order) -> User:
        """Update user's rank based on completed order"""
        update_data = {
            "rank": order.rank_type,
            "rank_activated_at": order.activated_at,
            "rank_expired_at": order.expired_subscription_at
        }
        
        # Update user fields
        for key, value in update_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
