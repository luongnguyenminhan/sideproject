"""Subscription Routes"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Body, HTTPException, Request, status, Security
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.http.oauth2 import get_current_user, oauth2_scheme, jwt_bearer
from app.modules.users.models.users import User
from app.modules.subscription.services.subscription_service import SubscriptionService
from app.modules.subscription.schemas.subscription_schemas import (
    OrderCreate, 
    CreatePaymentResponse, 
    UserRankResponse, 
    PayOSWebhookRequest
)
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions


# Create router with prefix and tags
route = APIRouter(
    prefix="/subscription", 
    tags=["Subscription"],
    dependencies=[Depends(jwt_bearer)],  # Use the JWT bearer security
)


@route.get(
    "/me/rank", 
    response_model=APIResponse[UserRankResponse],
    operation_id="get_user_rank",
    description="Get the current user's subscription rank",
    response_description="User rank information",
    summary="Get user subscription rank information",
)
@handle_exceptions
async def get_user_rank(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's subscription rank"""
    subscription_service = SubscriptionService(db)
    user_rank = subscription_service.get_user_rank(current_user)
    
    return APIResponse(
        error_code=0,
        message="User rank retrieved successfully",
        data=UserRankResponse(**user_rank)
    )


@route.post(
    "/payment/create-link", 
    response_model=APIResponse[CreatePaymentResponse],
    operation_id="create_payment_link",
    description="Create a payment link for a subscription",
    response_description="Payment link details",
    summary="Create subscription payment link",
)
@handle_exceptions
async def create_payment_link(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment link for a subscription"""
    subscription_service = SubscriptionService(db)
    payment_link = subscription_service.create_payment_link(
        user=current_user,
        rank_type=order_data.rank_type
    )
    
    return APIResponse(
        error_code=0,
        message="Payment link created successfully",
        data=CreatePaymentResponse(**payment_link)
    )


@route.post(
    "/webhook/payos", 
    dependencies=[], 
    include_in_schema=True,
    operation_id="payos_webhook",
    description="PayOS webhook endpoint (no authentication required)",
    response_description="Webhook response",
    responses={
        200: {
            "description": "Successful webhook processing",
            "content": {
                "application/json": {
                    "example": {"code": "00", "message": "Success"}
                }
            }
        }
    },
    # Explicitly override the global security for this endpoint
    openapi_extra={"security": []}
)
@handle_exceptions
async def payos_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle webhook notifications from PayOS"""
    # Get raw webhook data from request
    webhook_data = await request.json()
    
    # Process webhook
    subscription_service = SubscriptionService(db)
    result = subscription_service.handle_payment_webhook(webhook_data)
    
    # Return appropriate response
    if result.get("success"):
        return {"code": "00", "message": "Success"}
    else:
        return {"code": "99", "message": result.get("message", "Failed to process webhook")}
