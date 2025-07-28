"""Order DAL"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.base_dal import BaseDAL
from app.modules.subscription.models.order import Order
from app.enums.subscription_enums import OrderStatusEnum, RankEnum


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
