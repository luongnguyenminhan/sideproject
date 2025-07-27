"""Module init file"""

from fastapi import APIRouter

subscription_router = APIRouter()

# Import v1 routes
from app.modules.subscription.routes.v1 import subscription_router_v1
subscription_router.include_router(subscription_router_v1, prefix="/v1")

__all__ = ["subscription_router"]
