from app.core.base_model import RequestSchema
from typing import Optional

class DashboardStatsRequest(RequestSchema):
    # Add filter fields if needed
    start_date: Optional[str] = None
    end_date: Optional[str] = None
