"""Subscription module"""

from fastapi import APIRouter

router = APIRouter()

__all__ = ["router"]

# Import routes at the end to avoid circular imports
from app.modules.subscription.routes import subscription_router
router.include_router(subscription_router, prefix="")
