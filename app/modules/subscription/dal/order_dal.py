"""Order DAL"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.subscription.models.order import Order
from app.enums.subscription_enums import OrderStatusEnum, RankEnum
from app.utils.filter_utils import apply_dynamic_filters


class OrderDAL(BaseDAL[Order]):
    """Data Access Layer for Order"""

    def __init__(self, db: Session):
        super().__init__(db, Order)

    def get_by_order_code(self, order_code: str) -> Optional[Order]:
        """Get order by order code"""
        return self.db.query(self.model).filter(self.model.order_code == order_code).first()
    
    def get_by_payment_link_id(self, payment_link_id: str) -> Optional[Order]:
        """Get order by payment link ID"""
        return self.db.query(self.model).filter(self.model.payment_link_id == payment_link_id).first()
    
    def get_user_orders(self, user_id: str) -> List[Order]:
        """Get all orders for a specific user"""
        return (self.db.query(self.model)
                .filter(self.model.user_id == user_id)
                .order_by(self.model.created_at.desc())
                .all())
    
    def get_user_active_order(self, user_id: str) -> Optional[Order]:
        """Get the user's active subscription order"""
        return (self.db.query(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.status == OrderStatusEnum.COMPLETED,
                    self.model.expired_subscription_at > datetime.now()
                )
                .order_by(self.model.activated_at.desc())
                .first())
    
    def get_pending_orders(self) -> List[Order]:
        """Get all pending orders"""
        return (self.db.query(self.model)
                .filter(self.model.status == OrderStatusEnum.PENDING)
                .all())
    
    def get_expired_pending_orders(self) -> List[Order]:
        """Get all pending orders that have passed their expiration date"""
        return (self.db.query(self.model)
                .filter(
                    self.model.status == OrderStatusEnum.PENDING,
                    self.model.expired_at < datetime.now()
                )
                .all())

    def count_completed_orders(self, user_id: str = None, params: dict = None) -> int:
        """Count total number of completed orders with optional filters and user restriction
        
        Args:
            user_id (str): Optional user ID to filter orders for specific user
            params (dict): Optional filters to apply when counting orders
            
        Returns:
            int: Total count of completed orders matching the criteria
        """
        # Start with basic query for completed orders
        query = self.db.query(self.model).filter(
            self.model.status == OrderStatusEnum.COMPLETED,
            self.model.is_deleted == False
        )
        
        # Apply user filter if provided (for user-specific counts)
        if user_id:
            query = query.filter(self.model.user_id == user_id)
        
        # Apply dynamic filters if provided
        if params:
            query = apply_dynamic_filters(query, self.model, params)
        
        # Count total records
        total_count = query.count()
        
        return total_count
