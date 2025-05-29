import os
from typing import List, Dict, Any, Optional
from pymongo import MongoClient, DESCENDING
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class MongoDBService:
    """MongoDB service for storing chat messages and conversation history"""

    def __init__(self):
        print(f"\033[96m[MongoDBService.__init__] Initializing MongoDB service\033[0m")

        # Get MongoDB connection string from environment
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
        database_name = os.getenv("MONGODB_DATABASE", "cgsem_chat")

        print(
            f"\033[94m[MongoDBService.__init__] Connecting to MongoDB: {mongodb_url}\033[0m"
        )

        try:
            self.client = MongoClient(mongodb_url)
            self.db = self.client[database_name]
            self.messages_collection = self.db.messages
            self.conversations_collection = self.db.conversations

            # Test connection
            self.client.admin.command("ping")
            print(
                f"\033[92m[MongoDBService.__init__] MongoDB connection successful\033[0m"
            )

        except Exception as e:
            print(
                f"\033[91m[MongoDBService.__init__] ERROR: Failed to connect to MongoDB - {e}\033[0m"
            )
            raise e

    def save_message(self, message_data: Dict[str, Any]) -> str:
        """Save a chat message to MongoDB"""
        try:
            result = self.messages_collection.insert_one(message_data)
            logger.info(f"Message saved to MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving message to MongoDB: {e}")
            raise

    def get_conversation_messages(
        self, conversation_id: str, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation from MongoDB"""
        try:
            messages = (
                self.messages_collection.find({"conversation_id": conversation_id})
                .sort("timestamp", DESCENDING)
                .skip(skip)
                .limit(limit)
            )

            return list(messages)
        except Exception as e:
            logger.error(f"Error fetching messages from MongoDB: {e}")
            return []

    def get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent conversation history for context"""
        try:
            messages = (
                self.messages_collection.find({"conversation_id": conversation_id})
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )

            # Reverse to get chronological order
            return list(reversed(list(messages)))
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []

    def update_conversation_summary(
        self, conversation_id: str, summary_data: Dict[str, Any]
    ):
        """Update conversation summary in MongoDB"""
        try:
            self.conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {"$set": summary_data},
                upsert=True,
            )
            logger.info(f"Conversation summary updated for: {conversation_id}")
        except Exception as e:
            logger.error(f"Error updating conversation summary: {e}")
            raise

    def delete_conversation_messages(self, conversation_id: str):
        """Delete all messages for a conversation"""
        try:
            result = self.messages_collection.delete_many(
                {"conversation_id": conversation_id}
            )
            logger.info(
                f"Deleted {result.deleted_count} messages for conversation: {conversation_id}"
            )

            # Also delete conversation summary
            self.conversations_collection.delete_one(
                {"conversation_id": conversation_id}
            )
        except Exception as e:
            logger.error(f"Error deleting conversation messages: {e}")
            raise


# Singleton instance
mongodb_service = MongoDBService()
