"""PayOS Service for payment integration"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from payos import PayOS, PaymentData, ItemData

from app.core.config import PAYOS_CLIENT_ID, PAYOS_API_KEY, PAYOS_CHECKSUM_KEY


class PayOSService:
    """Service for PayOS payment integration"""
    
    def __init__(self):
        """Initialize the PayOS client"""
        self.client_id = PAYOS_CLIENT_ID
        self.api_key = PAYOS_API_KEY
        self.checksum_key = PAYOS_CHECKSUM_KEY
        
        if not all([self.client_id, self.api_key, self.checksum_key]):
            raise ValueError("PayOS credentials are not properly configured")
            
        self.payos = PayOS(
            client_id=self.client_id, 
            api_key=self.api_key, 
            checksum_key=self.checksum_key
        )
    
    def create_payment_link(self, order_code: str, amount: float, description: str, user_email: str) -> Dict[str, Any]:
        """Create a payment link for an order
        
        Args:
            order_code: The unique code for the order
            amount: The amount to pay in VND
            description: The payment description
            user_email: User's email for reference
            
        Returns:
            Dictionary containing payment link information
        """
        # Create item data (can be customized based on subscription plan)
        item = ItemData(
            name=f"Enterviu Subscription - {order_code}",
            quantity=1,
            price=amount
        )
        
        # Create payment data
        print(order_code, "---"*100)
        payment_data = PaymentData(
            orderCode=int(order_code),
            amount=int(amount),  # PayOS requires integer amount
            description=description,
            items=[item],
            cancelUrl=f"https://app.enterviu.ai/subscription/cancel?order={order_code}",
            returnUrl=f"https://app.enterviu.ai/subscription/success?order={order_code}",
            # Optional additional metadata
            buyerName=user_email,
            buyerEmail=user_email
        )
        
        # Create payment link
        payment_link_data = self.payos.createPaymentLink(paymentData=payment_data)
        
        return payment_link_data.to_json()
    
    def get_payment_info(self, order_id: str) -> Dict[str, Any]:
        """Get payment information for an existing order
        
        Args:
            order_id: The PayOS payment link ID
            
        Returns:
            Dictionary containing payment information
        """
        payment_info = self.payos.getPaymentLinkInformation(orderId=order_id)
        return payment_info.to_json()
    
    def verify_webhook_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify webhook data from PayOS
        
        Args:
            webhook_data: The raw webhook data from PayOS
            
        Returns:
            Verified webhook data or raises exception if invalid
        """
        verified_data = self.payos.verifyPaymentWebhookData(webhook_data)
        return verified_data.to_json()
