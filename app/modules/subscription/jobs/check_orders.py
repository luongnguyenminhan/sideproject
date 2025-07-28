"""Subscription Cron Jobs"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.subscription.services.subscription_service import SubscriptionService
from app.core.database import get_db_session

# Configure logging
logger = logging.getLogger(__name__)


def check_pending_orders():
    """Cron job to check pending orders and update their status
    
    This job should be scheduled to run every 5 minutes
    """
    logger.info(f"[{datetime.now()}] Starting pending order check job")
    
    try:
        # Get database session
        db: Session = next(get_db_session())
        
        # Create subscription service
        subscription_service = SubscriptionService(db)
        
        # Check pending orders
        results = subscription_service.check_pending_orders()
        
        # Log results
        logger.info(f"Processed {len(results)} pending orders")
        for result in results:
            order_id = result.get("order_id")
            status = result.get("status")
            logger.info(f"Order {order_id}: {status}")
            
            # Log errors for failed checks
            if status == "error":
                logger.error(f"Error processing order {order_id}: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Error in check_pending_orders job: {str(e)}", exc_info=True)
    finally:
        # Close the database session
        db.close()
        
    logger.info(f"[{datetime.now()}] Completed pending order check job")
