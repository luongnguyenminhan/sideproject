from app.core.base_model import ResponseSchema, APIResponse
from pydantic import ConfigDict


class DashboardStatsResponse(ResponseSchema):
    model_config = ConfigDict(from_attributes=True)
    user_count: int
    order_count: int
    total_revenue: int
