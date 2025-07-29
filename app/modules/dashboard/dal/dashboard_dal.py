from sqlalchemy.orm import Session
from app.core.base_dal import BaseDAL
from app.modules.users.models.users import User
from app.modules.subscription.models.order import Order
from typing import Dict, Any


class DashboardDAL(BaseDAL):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_user_count(self) -> int:
        return self.db.query(User).filter(User.is_deleted == False).count()

    def get_order_count(self) -> int:
        return self.db.query(Order).filter(Order.is_deleted == False).count()

    def get_total_revenue(self) -> int:
        return (
            self.db.query(Order)
            .filter(Order.is_deleted == False, Order.status == "completed")
            .with_entities(Order.amount)
            .all()
        )

    # Add more DAL methods for other statistics as needed
