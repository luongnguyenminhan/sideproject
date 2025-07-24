# Payment Service
"""
Service layer for interacting with PayOS payment gateway.
"""
import logging
import os
from typing import Dict, Any, Optional, Union

from payos import PayOS, ItemData as PayOSItemData, PaymentData
from sqlalchemy.orm import Session

from app.core.config import (
    PAYOS_CLIENT_ID,
    PAYOS_API_KEY,
    PAYOS_CHECKSUM_KEY,
)
from app.modules.payment.models.payment import Payment, PaymentStatus
from app.modules.payment.dal.payment_dal import PaymentDAL
from app.modules.payment.schemas.payment_schemas import ItemData

logger = logging.getLogger(__name__)

class PaymentService:
    """Service class for handling PayOS payment operations"""
    
    def __init__(self, db: Session):
        """Initialize payment service with DB session and PayOS client"""
        self.db = db
        self.dal = PaymentDAL(db)
        
        # Initialize PayOS client
        self.client_id = PAYOS_CLIENT_ID
        self.api_key = PAYOS_API_KEY
        self.checksum_key = PAYOS_CHECKSUM_KEY
        
        self.payos = PayOS(
            client_id=self.client_id,
            api_key=self.api_key,
            checksum_key=self.checksum_key
        )
        
        logger.info("PayOS service initialized")
    
    def create_payment_link(self, 
                           order_code: int,
                           amount: int,
                           description: str,
                           items: list[ItemData],
                           cancel_url: str,
                           return_url: str,
                           user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a payment link using PayOS
        
        Args:
            order_code: Unique order code
            amount: Amount to pay (in VND)
            description: Payment description
            items: List of items to pay for
            cancel_url: URL to redirect to when payment is cancelled
            return_url: URL to redirect to when payment is successful
            user_id: Optional user ID
            
        Returns:
            Payment details with checkout URL
        """
        logger.info(f"Creating payment link for order {order_code}, amount {amount}")
        
        # Check if payment with this order_code already exists
        existing_payment = self.dal.get_payment_by_order_code(order_code)
        if existing_payment:
            logger.info(f"Payment for order {order_code} already exists, returning existing payment")
            return {
                "id": existing_payment.id,
                "order_code": existing_payment.order_code,
                "amount": existing_payment.amount,
                "description": existing_payment.description,
                "status": existing_payment.status,
                "payment_link_id": existing_payment.payment_link_id,
                "checkout_url": existing_payment.checkout_url,
                "qr_code": existing_payment.qr_code,
                "currency": existing_payment.currency
            }
        
        # Convert items to PayOS format
        payos_items = []
        for item in items:
            payos_item = PayOSItemData(
                name=item.name,
                quantity=item.quantity,
                price=item.price
            )
            payos_items.append(payos_item)
        
        # Create PayOS payment data
        payment_data = PaymentData(
            orderCode=order_code,
            amount=amount,
            description=description,
            items=payos_items,
            cancelUrl=cancel_url,
            returnUrl=return_url
        )
        
        try:
            # Create payment link using PayOS API
            result = self.payos.createPaymentLink(paymentData=payment_data)
            
            # Save payment details to database
            payment_record = {
                "order_code": order_code,
                "amount": amount,
                "description": description,
                "payment_link_id": result.paymentLinkId,
                "status": PaymentStatus.CREATED,
                "checkout_url": result.checkoutUrl,
                "qr_code": result.qrCode,
                "currency": result.currency
            }
            
            if user_id:
                payment_record["user_id"] = user_id
                
            # Save to database
            saved_payment = self.dal.create_payment(payment_record)
            
            # Return payment details
            return {
                "id": saved_payment.id,
                "order_code": saved_payment.order_code,
                "amount": saved_payment.amount,
                "description": saved_payment.description,
                "status": saved_payment.status,
                "payment_link_id": saved_payment.payment_link_id,
                "checkout_url": saved_payment.checkout_url,
                "qr_code": saved_payment.qr_code,
                "currency": saved_payment.currency
            }
            
        except Exception as e:
            logger.error(f"Error creating payment link: {str(e)}")
            raise e
    
    def get_payment_link_information(self, order_id: Union[str, int]) -> Dict[str, Any]:
        """
        Get information about a payment link
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Payment link information
        """
        logger.info(f"Getting payment information for order {order_id}")
        
        try:
            result = self.payos.getPaymentLinkInformation(orderId=order_id)
            
            # Check if payment exists in our database
            payment = self.dal.get_payment_by_order_code(int(order_id))
            if payment:
                # Update payment status based on PayOS status
                payos_status = result.status.lower()
                
                # Map PayOS status to our status
                status_mapping = {
                    "pending": PaymentStatus.PENDING,
                    "processing": PaymentStatus.PROCESSING,
                    "paid": PaymentStatus.COMPLETED,
                    "cancelled": PaymentStatus.CANCELLED,
                    "expired": PaymentStatus.FAILED
                }
                
                if payos_status in status_mapping:
                    self.dal.update_payment_status(
                        payment_id=payment.id,
                        status=status_mapping[payos_status]
                    )
            
            return result.to_json()
            
        except Exception as e:
            logger.error(f"Error getting payment information: {str(e)}")
            raise e
    
    def cancel_payment_link(self, order_id: Union[str, int], cancellation_reason: str) -> Dict[str, Any]:
        """
        Cancel a payment link
        
        Args:
            order_id: Order ID to cancel
            cancellation_reason: Reason for cancellation
            
        Returns:
            Cancelled payment information
        """
        logger.info(f"Cancelling payment for order {order_id}")
        
        try:
            result = self.payos.cancelPaymentLink(orderId=order_id, cancellationReason=cancellation_reason)
            
            # Update payment status in database
            payment = self.dal.get_payment_by_order_code(int(order_id))
            if payment:
                self.dal.update_payment_status(
                    payment_id=payment.id,
                    status=PaymentStatus.CANCELLED
                )
            
            return result.to_json()
            
        except Exception as e:
            logger.error(f"Error cancelling payment: {str(e)}")
            raise e
    
    def confirm_webhook(self, webhook_url: str) -> str:
        """
        Confirm a webhook URL with PayOS
        
        Args:
            webhook_url: Webhook URL to confirm
            
        Returns:
            Confirmation result
        """
        logger.info(f"Confirming webhook URL: {webhook_url}")
        
        try:
            result = self.payos.confirmWebhook(webhook_url)
            return result
            
        except Exception as e:
            logger.error(f"Error confirming webhook URL: {str(e)}")
            raise e
    
    def verify_payment_webhook(self, webhook_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify payment webhook data
        
        Args:
            webhook_body: Webhook data from PayOS
            
        Returns:
            Verified webhook data
        """
        logger.info(f"Verifying webhook data for payment")
        
        try:
            result = self.payos.verifyPaymentWebhookData(webhook_body)
            
            # Convert to dictionary
            data_dict = result.to_json()
            
            # Update payment in database
            payment_link_id = data_dict.get("paymentLinkId")
            if payment_link_id:
                self.dal.update_payment_from_webhook(
                    payment_link_id=payment_link_id,
                    webhook_data=data_dict
                )
            
            return data_dict
            
        except Exception as e:
            logger.error(f"Error verifying webhook data: {str(e)}")
            raise e
