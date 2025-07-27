"""Module init file"""

from fastapi import APIRouter

subscription_router_v1 = APIRouter()

# Import routes after defining router
from app.modules.subscription.routes.v1.subscription_routes import router
subscription_router_v1.include_router(router)

__all__ = ["subscription_router_v1"]
