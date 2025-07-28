# Payment Routes
"""
API routes for the Payment module.
"""
import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.orm import Session

from app.core.base_model import APIResponse
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.exceptions.exception import ValidationException
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user
from app.middleware.translation_manager import _
from app.modules.payment.repository.payment_repo import PaymentRepo
from app.modules.payment.schemas.payment_schemas import (
    CreatePaymentRequest,
    PaymentResponse,
    WebhookVerifyRequest,
    WebhookData,
)

logger = logging.getLogger(__name__)

route = APIRouter(prefix="/payments", tags=["Payments"])


@route.post("/create-payment", response_model=APIResponse)
@handle_exceptions
async def create_payment(
    request: CreatePaymentRequest,
    repo: PaymentRepo = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Create a payment link with PayOS
    
    This endpoint creates a new payment link using the PayOS payment gateway.
    It returns the payment details including checkout URL and QR code.
    """
    user_id = current_user.get("user_id") if current_user else None
    
    # Create payment link
    payment_data = repo.create_payment_link(request, user_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("payment_link_created_successfully"),
        data=payment_data,
    )


@route.get("/{order_id}/info", response_model=APIResponse)
@handle_exceptions
async def get_payment_info(
    order_id: str,
    repo: PaymentRepo = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Get payment information by order ID
    
    This endpoint retrieves information about a payment link from PayOS.
    It returns the current status and details of the payment.
    """
    # Get payment information
    payment_info = repo.get_payment_information(order_id)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("payment_info_retrieved_successfully"),
        data=payment_info,
    )


@route.post("/{order_id}/cancel", response_model=APIResponse)
@handle_exceptions
async def cancel_payment(
    order_id: str,
    cancellation_reason: str = Body(..., embed=True),
    repo: PaymentRepo = Depends(),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Cancel a payment by order ID
    
    This endpoint cancels a payment link in PayOS.
    It requires a cancellation reason.
    """
    # Cancel payment
    cancel_result = repo.cancel_payment(order_id, cancellation_reason)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("payment_cancelled_successfully"),
        data=cancel_result,
    )


@route.post("/webhook/verify", response_model=APIResponse)
@handle_exceptions
async def verify_webhook(
    request: WebhookVerifyRequest,
    repo: PaymentRepo = Depends(),
):
    """
    Verify a webhook URL with PayOS
    
    This endpoint verifies and registers a webhook URL with PayOS.
    It's used to set up the webhook integration.
    """
    # Verify webhook URL
    verify_result = repo.confirm_webhook_url(request)
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("webhook_verified_successfully"),
        data={"result": verify_result},
    )


@route.post("/webhook", response_model=APIResponse)
@handle_exceptions
async def payment_webhook(
    request: Request,
    repo: PaymentRepo = Depends(),
):
    """
    PayOS webhook endpoint
    
    This endpoint receives webhook notifications from PayOS when a payment status changes.
    It verifies the webhook data and updates the payment status in the database.
    """
    # Read request body
    body_bytes = await request.body()
    webhook_data = json.loads(body_bytes)
    
    logger.info(f"Received webhook data: {json.dumps(webhook_data)}")
    
    try:
        # Verify webhook data
        verify_result = repo.verify_payment_webhook(webhook_data)
        
        return APIResponse(
            error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
            message=_("webhook_processed_successfully"),
            data={"result": "success", "verified_data": verify_result},
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return APIResponse(
            error_code=BaseErrorCode.ERROR_CODE_FAIL,
            message=_("webhook_processing_failed"),
            data={"result": "failed", "error": str(e)},
        )


@route.get("/my-payments", response_model=APIResponse)
@handle_exceptions
async def get_my_payments(
    limit: int = 10,
    offset: int = 0,
    repo: PaymentRepo = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """
    Get current user's payments
    
    This endpoint returns the current user's payment history.
    """
    user_id = current_user.get("user_id")
    if not user_id:
        raise ValidationException(_("user_not_authenticated"))
    
    # Get user payments
    payments = repo.get_user_payments(user_id, limit, offset)
    
    # Convert to response schema
    payment_responses = []
    for payment in payments:
        payment_responses.append({
            "id": payment.id,
            "order_code": payment.order_code,
            "amount": payment.amount,
            "description": payment.description,
            "status": payment.status,
            "payment_link_id": payment.payment_link_id,
            "checkout_url": payment.checkout_url,
            "qr_code": payment.qr_code,
            "currency": payment.currency,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "completed_at": payment.completed_at,
            "cancelled_at": payment.cancelled_at,
        })
    
    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("user_payments_retrieved_successfully"),
        data=payment_responses,
    )
