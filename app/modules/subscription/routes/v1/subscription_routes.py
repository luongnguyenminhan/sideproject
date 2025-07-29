
"""Subscription Routes"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Body, HTTPException, Request, status, Security, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.http.oauth2 import get_current_user, oauth2_scheme, jwt_bearer
from ...models.order import Order
from ...repository.order_repository import OrderRepository
from app.modules.users.models.users import User
from app.modules.subscription.services.subscription_service import SubscriptionService
from app.modules.subscription.schemas.subscription_schemas import (
    OrderCreate, 
    CreatePaymentResponse, 
    UserRankResponse, 
    PayOSWebhookRequest,
    OrderListResponse,
    CountCompletedOrdersResponse
)
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from urllib.parse import urlencode

# Create router with prefix and tags
route = APIRouter(
    prefix="/subscription", 
    tags=["Subscription"],  # Use the JWT bearer security
)


@route.get(
    "/",
    response_model=APIResponse[OrderListResponse],
    operation_id="get_orders_paginated",
    description="Get paginated subscription orders (admin only)",
    response_description="Paginated list of orders",
    summary="Get paginated subscription orders (admin)",
)
@handle_exceptions
async def get_orders_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get paginated orders (admin only), including user info"""
    total = db.query(Order).count()
    orders = db.query(Order).order_by(Order.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    result = []
    for order in orders:
        order_data = order.__dict__.copy()
        user_obj = db.query(User).filter(User.id == order.user_id).first()
        order_data['user'] = user_obj.to_dict() if user_obj else None
        result.append(order_data)
    return APIResponse(
        error_code=0,
        message="Paginated orders retrieved successfully",
        data={
            "orders": result,
            "paging": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }
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
    user_rank = subscription_service.get_user_rank(current_user['user_id'])
    
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
        user_id=current_user['user_id'],
        rank_type=order_data.rank_type
    )
    
    return APIResponse(
        error_code=0,
        message="Payment link created successfully",
        data=CreatePaymentResponse(**payment_link)
    )


@route.get(
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
    openapi_extra={"security": []}
)
@handle_exceptions
async def payos_webhook(
    order: str = None,
    code: str = None,
    id: str = None,
    cancel: str = None,
    status: str = None,
    orderCode: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle webhook notifications from PayOS via query parameters and redirect to payment page.
    Example: /webhook/payos?order=...&code=...&id=...&cancel=...&status=...&orderCode=...
    """
    webhook_data = {
        "order": order,
        "code": code,
        "id": id,
        "cancel": cancel,
        "status": status,
        "orderCode": orderCode
    }
    subscription_service = SubscriptionService(db)
    return subscription_service.handle_payment_webhook(webhook_data)

# API: Get current user's orders
@route.get(
    "/me/orders",
    response_model=APIResponse[OrderListResponse],
    operation_id="get_user_orders",
    description="Get the current user's subscription orders",
    response_description="List of user's orders",
    summary="Get user subscription orders",
)
@handle_exceptions
async def get_user_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all orders for the current user, including user info"""
    order_repo = OrderRepository(db)
    orders = order_repo.get_user_orders(current_user['user_id'])
    result = []
    for order in orders:
        order_data = order.__dict__.copy()
        print("**"*100, type(order_data))
        # Always query user by user_id if not loaded
        user_obj = None
        user_obj = db.query(User).filter(User.id == order.user_id).first()
        order_data['user'] = user_obj.to_dict()
        print("=="*10, order_data)
        result.append(order_data)
    return APIResponse(
        error_code=0,
        message="User orders retrieved successfully",
        data={"orders": result}
    )

# API: Get all orders (admin)
@route.get(
    "/admin/orders",
    response_model=APIResponse[OrderListResponse],
    operation_id="get_all_orders",
    description="Get all subscription orders (admin only)",
    response_description="List of all orders",
    summary="Get all subscription orders (admin)",
)
@handle_exceptions
async def get_all_orders(
    db: Session = Depends(get_db)
):
    """Get all orders (admin only), including user info"""
    orders = db.query(Order).all()
    result = []
    for order in orders:
        order_data = order.__dict__.copy()
        # Always query user by user_id if not loaded
        user_obj = None
        user_obj = db.query(User).filter(User.id == order.user_id).first()
        order_data['user'] = user_obj.to_dict()
        result.append(order_data)
    return APIResponse(
        error_code=0,
        message="All orders retrieved successfully",
        data={"orders": result}
    )


@route.get(
    "/orders/count/completed",
    response_model=APIResponse[CountCompletedOrdersResponse],
    operation_id="count_completed_orders",
    description="Count completed subscription orders",
    response_description="Count of completed orders",
    summary="Count completed subscription orders",
)
@handle_exceptions
async def count_completed_orders(
    filters_json: str | None = Query(None, description='JSON string of filters'),
    include_user_filter: bool = Query(False, description='Whether to filter orders for current user only'),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Count total number of completed orders with optional filtering

    Supports filtering using a JSON string of filters with field, operator, and value.
    By default, counts all completed orders (admin view).
    
    Example with structured filters:
    GET /subscription/orders/count/completed?filters_json=[{"field":"rank_type","operator":"eq","value":"pro"}]
    
    Available operators:
    - eq: Equal
    - ne: Not equal  
    - lt: Less than
    - lte: Less than or equal
    - gt: Greater than
    - gte: Greater than or equal
    - contains: String contains
    - startswith: String starts with
    - endswith: String ends with
    - in_list: Value is in a list
    - not_in: Value is not in a list
    - is_null: Field is null
    - is_not_null: Field is not null
    """
    filters = []
    if filters_json:
        try:
            filters = json.loads(filters_json)
            if not isinstance(filters, list):
                filters = []
        except json.JSONDecodeError:
            filters = []
        except Exception:
            filters = []

    filter_params = {'filters': filters} if filters else {}
    
    # Get user_id if include_user_filter is True
    user_id = current_user.get('user_id') if include_user_filter else None
    
    order_repo = OrderRepository(db)
    total_count = order_repo.count_completed_orders(user_id, filter_params)
    
    return APIResponse(
        error_code=0,
        message=_('operation_successful'),
        data=CountCompletedOrdersResponse(total_count=total_count),
    )