from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.dashboard.dal.dashboard_dal import DashboardDAL
from app.middleware.translation_manager import _
from app.exceptions.exception import NotFoundException

class DashboardRepo:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.dashboard_dal = DashboardDAL(db)

    def get_dashboard_stats(self):
        user_count = self.dashboard_dal.get_user_count()
        order_count = self.dashboard_dal.get_order_count()
        # Example: total revenue calculation
        total_revenue = sum([x[0] for x in self.dashboard_dal.get_total_revenue()])
        return {
            "user_count": user_count,
            "order_count": order_count,
            "total_revenue": total_revenue
        }
