from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.modules.dashboard.repository.dashboard_repo import DashboardRepo
from app.modules.dashboard.schemas.dashboard_request import DashboardStatsRequest
from app.modules.dashboard.schemas.dashboard_response import DashboardStatsResponse
from app.middleware.translation_manager import _

route = APIRouter(prefix="/dashboard", tags=["dashboard"])


@route.get("/stats", response_model=APIResponse)
@handle_exceptions
async def get_dashboard_stats(
    request: DashboardStatsRequest = Depends(), repo: DashboardRepo = Depends()
):
    stats = repo.get_dashboard_stats()
    return APIResponse(
        error_code=0, message=_("success"), data=DashboardStatsResponse(**stats)
    )
