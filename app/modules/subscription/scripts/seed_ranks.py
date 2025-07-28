"""Seed rank data"""

import os
import sys

# Add project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.modules.subscription.models.rank import Rank
from app.enums.subscription_enums import RankEnum


def seed_ranks():
    """Seed initial rank data"""
    db = SessionLocal()
    try:
        # Check if ranks already exist
        existing_ranks = db.query(Rank).count()
        if existing_ranks > 0:
            print(f"Ranks already seeded. Found {existing_ranks} ranks.")
            return

        # Define rank data
        ranks_data = [
            {
                "name": RankEnum.BASIC,
                "description": "Basic user level with limited access to features",
                "benefits": {
                    "daily_tokens": 1000,
                    "max_storage_mb": 100,
                    "features": ["basic-chat", "basic-analytics"]
                },
                "price": "0"
            },
            {
                "name": RankEnum.PRO,
                "description": "Pro subscription with enhanced capabilities",
                "benefits": {
                    "daily_tokens": 5000,
                    "max_storage_mb": 1000,
                    "features": [
                        "basic-chat", 
                        "basic-analytics", 
                        "advanced-chat", 
                        "export-data", 
                        "priority-support"
                    ]
                },
                "price": "399,000 VND"
            },
            {
                "name": RankEnum.ULTRA,
                "description": "Ultra subscription with all premium features",
                "benefits": {
                    "daily_tokens": 20000,
                    "max_storage_mb": 10000,
                    "features": [
                        "basic-chat", 
                        "basic-analytics", 
                        "advanced-chat", 
                        "export-data", 
                        "priority-support",
                        "custom-agents",
                        "api-access",
                        "team-collaboration"
                    ]
                },
                "price": "699,000 VND"
            }
        ]

        # Insert ranks
        for rank_data in ranks_data:
            rank = Rank(**rank_data)
            db.add(rank)

        db.commit()
        print(f"Successfully seeded {len(ranks_data)} ranks.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding ranks: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_ranks()
