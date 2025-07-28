"""Subscription Service"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.subscription.repository.rank_repository import RankRepository
from app.modules.subscription.repository.order_repository import OrderRepository
from app.modules.subscription.services.payos_service import PayOSService
from app.modules.subscription.models.rank import Rank
from app.modules.subscription.models.order import Order
from app.modules.users.models.users import User
from app.enums.subscription_enums import RankEnum, OrderStatusEnum
from app.exceptions.exception import CustomHTTPException
from ...users.repository.user_repo import UserRepo
import uuid


class SubscriptionService:
    """Service for handling subscription related operations"""

    def __init__(self, db: Session):
        self.db = db
        self.rank_repo = RankRepository(db)
        self.order_repo = OrderRepository(db)
        self.payos_service = PayOSService()
        self.user_repo = UserRepo(db)

        # Define subscription plans with their prices
        self.subscription_prices = {
            RankEnum.PRO: 49000,  # 399,000 VND for PRO
            RankEnum.ECO: 29000,
            RankEnum.ULTRA: 79000,  # 699,000 VND for ULTRA
            RankEnum.TEST: 5000,
        }

    def get_user_rank(self, user_id) -> Dict[str, Any]:
        """Get the current rank information for a user

        Args:
            user: The user to get rank information for

        Returns:
            Dictionary containing rank information
        """
        # Get rank details
        user = self.user_repo.get_user_by_id(user_id)
        rank = self.rank_repo.get_by_user_id(user_id)

        # Check if the rank has expired
        is_active = False
        if user.rank != RankEnum.BASIC:
            is_active = (
                user.rank_expired_at is not None
                and user.rank_expired_at > datetime.now()
            )

        return {
            "rank": user.rank,
            "description": rank.description if rank else "",
            "benefits": rank.benefits if rank else {},
            "activated_at": user.rank_activated_at,
            "expired_at": user.rank_expired_at,
            "is_active": is_active,
        }

    def create_payment_link(self, user_id: str, rank_type: RankEnum) -> Dict[str, Any]:
        """Create a payment link for a subscription

        Args:
            user: The user requesting the subscription
            rank_type: The subscription rank to purchase

        Returns:
            Dictionary containing payment link information
        """
        user = self.user_repo.get_user_by_id(user_id)
        # Validate rank type
        if rank_type not in [RankEnum.PRO, RankEnum.ULTRA, RankEnum.ECO, RankEnum.TEST]:
            raise CustomHTTPException(
                message="Invalid subscription plan",
            )

        # Get amount from subscription prices
        amount = self.subscription_prices.get(rank_type)
        if not amount:
            raise CustomHTTPException(
                message="Invalid subscription plan",
            )

        # Create payment description
        description = f"{rank_type} 1 month"

        # Create payment link with PayOS
        # Generate a random integer order code (8 digits)
        order_code = str(uuid.uuid4().int)[:8]
        payment_data = self.payos_service.create_payment_link(
            order_code=order_code,
            amount=amount,
            description=description,
            user_email=user.email,
        )

        # Create order in database
        print("dang luu db")
        order = self.order_repo.create_order(
            order_code=order_code,
            user_id=user.id,
            rank_type=rank_type,
            amount=amount,
            payment_data=payment_data,
        )
        self.db.commit()
        print("luu db xong roi")
        return {
            "checkout_url": order.checkout_url,
            "order_code": order.order_code,
            "expired_at": order.expired_at,
        }

    def handle_payment_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment webhook from PayOS and redirect to app.wc504.io.vn/payment with all params as query params"""
        from urllib.parse import urlencode

        try:
            # Verify webhook data
            verified_data = self.payos_service.verify_webhook_data(webhook_data)

            # Extract key information
            payment_link_id = verified_data.get("paymentLinkId")
            order_code = verified_data.get("orderCode")
            status_code = verified_data.get("code")
            transaction_id = verified_data.get("reference", "")
            desc = verified_data.get("desc", "")
            success = verified_data.get("success", False)

            # Find the order
            order = None
            if order_code:
                order = self.order_repo.get_by_order_code(str(order_code))
            elif payment_link_id:
                order = self.order_repo.get_by_payment_link_id(payment_link_id)

            if not order:
                redirect_url = f"https://app.wc504.io.vn/payment?{urlencode({'success': False, 'message': 'Order not found'})}"
                return {"redirect_url": redirect_url}

            # Process payment status
            params = {
                "order_id": order.id,
                "order_code": order.order_code,
                "user_id": order.user_id,
                "payment_link_id": payment_link_id,
                "transaction_id": transaction_id,
                "status_code": status_code,
                "desc": desc,
                "success": success,
            }

            if status_code == "00":  # Success code
                # Mark order as completed
                order = self.order_repo.mark_order_as_completed(order, transaction_id)

                # Get user and update their rank
                user = self.db.query(User).filter(User.id == order.user_id).first()
                if user:
                    self.order_repo.update_user_rank(user, order)

                params["message"] = "Payment successful"
                params["success"] = True
            else:
                # Payment failed
                self.order_repo.mark_order_as_canceled(order, f"Payment failed: {desc}")
                params["message"] = "Payment failed"
                params["success"] = False

            redirect_url = f"https://app.wc504.io.vn/payment?{urlencode(params)}"
            return {"redirect_url": redirect_url}

        except Exception as e:
            redirect_url = f"https://app.wc504.io.vn/payment?{urlencode({'success': False, 'message': str(e)})}"
            return {"redirect_url": redirect_url}

    def check_pending_orders(self) -> List[Dict[str, Any]]:
        """Check all pending orders and update their status

        Returns:
            List of processed order results
        """
        results = []

        # Get all pending orders
        pending_orders = self.order_repo.get_pending_orders()

        for order in pending_orders:
            try:
                # Skip orders that don't have payment link ID
                if not order.payment_link_id:
                    continue

                # Check if order is expired locally
                if order.expired_at < datetime.now():
                    self.order_repo.mark_order_as_canceled(order, "Order expired")
                    results.append(
                        {
                            "order_id": order.id,
                            "status": "canceled",
                            "reason": "Order expired locally",
                        }
                    )
                    continue

                # Check payment status with PayOS
                payment_info = self.payos_service.get_payment_info(
                    order.payment_link_id
                )
                status = payment_info.get("status", "").lower()

                # Process based on status
                if status == "paid":
                    # Payment successful
                    transaction_id = ""
                    transactions = payment_info.get("transactions", [])
                    if transactions and len(transactions) > 0:
                        transaction_id = transactions[0].get("reference", "")

                    order = self.order_repo.mark_order_as_completed(
                        order, transaction_id
                    )

                    # Update user rank
                    user = self.db.query(User).filter(User.id == order.user_id).first()
                    if user:
                        self.order_repo.update_user_rank(user, order)

                    results.append(
                        {
                            "order_id": order.id,
                            "status": "completed",
                            "transaction_id": transaction_id,
                        }
                    )
                elif status in ["cancelled", "expired"]:
                    # Payment canceled or expired
                    self.order_repo.mark_order_as_canceled(order, f"Payment {status}")
                    results.append(
                        {
                            "order_id": order.id,
                            "status": "canceled",
                            "reason": f"Payment {status}",
                        }
                    )
                else:
                    # Still pending
                    results.append({"order_id": order.id, "status": "pending"})

            except Exception as e:
                results.append(
                    {"order_id": order.id, "status": "error", "error": str(e)}
                )

        return results
