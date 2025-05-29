from pymongo import MongoClient, DESCENDING
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
import os
import logging

logger = logging.getLogger(__name__)


class MongoDBService:
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

    def create_conversation(self, user_id: str, conversation_id: str) -> str:
        """Create a new conversation document in MongoDB"""
        print(
            f"\033[92m[MongoDBService.create_conversation] Creating conversation - user_id: {user_id}, conversation_id: {conversation_id}\033[0m"
        )

        conversation_doc = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "messages": [],
            "files": [],
        }

        try:
            result = self.conversations_collection.insert_one(conversation_doc)
            mongo_id = str(result.inserted_id)
            print(
                f"\033[92m[MongoDBService.create_conversation] Conversation created with MongoDB ID: {mongo_id}\033[0m"
            )
            return mongo_id

        except Exception as e:
            print(f"\033[91m[MongoDBService.create_conversation] ERROR: {e}\033[0m")
            raise e

    def add_message(
        self, conversation_id: str, role: str, content: str, timestamp: datetime = None
    ) -> bool:
        """Add a message to conversation"""
        print(
            f"\033[92m[MongoDBService.add_message] Adding message - conversation_id: {conversation_id}, role: {role}\033[0m"
        )
        print(
            f"\033[94m[MongoDBService.add_message] Content length: {len(content)}\033[0m"
        )

        if timestamp is None:
            timestamp = datetime.utcnow()

        message = {"role": role, "content": content, "timestamp": timestamp}

        try:
            result = self.conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"messages": message},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            if result.modified_count > 0:
                print(
                    f"\033[92m[MongoDBService.add_message] Message added successfully\033[0m"
                )
                return True
            else:
                print(
                    f"\033[91m[MongoDBService.add_message] No conversation found with ID: {conversation_id}\033[0m"
                )
                return False

        except Exception as e:
            print(f"\033[91m[MongoDBService.add_message] ERROR: {e}\033[0m")
            raise e

    def add_file(
        self,
        conversation_id: str,
        file_id: str,
        filename: str,
        upload_time: datetime = None,
    ) -> bool:
        """Add a file reference to conversation"""
        print(
            f"\033[92m[MongoDBService.add_file] Adding file - conversation_id: {conversation_id}, file_id: {file_id}, filename: {filename}\033[0m"
        )

        if upload_time is None:
            upload_time = datetime.utcnow()

        file_ref = {
            "file_id": file_id,
            "filename": filename,
            "upload_time": upload_time,
        }

        try:
            result = self.conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$push": {"files": file_ref},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            if result.modified_count > 0:
                print(
                    f"\033[92m[MongoDBService.add_file] File reference added successfully\033[0m"
                )
                return True
            else:
                print(
                    f"\033[91m[MongoDBService.add_file] No conversation found with ID: {conversation_id}\033[0m"
                )
                return False

        except Exception as e:
            print(f"\033[91m[MongoDBService.add_file] ERROR: {e}\033[0m")
            raise e

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation with all messages and files"""
        print(
            f"\033[92m[MongoDBService.get_conversation] Getting conversation: {conversation_id}\033[0m"
        )

        try:
            conversation = self.conversations_collection.find_one(
                {"conversation_id": conversation_id}
            )

            if conversation:
                print(
                    f"\033[92m[MongoDBService.get_conversation] Conversation found with {len(conversation.get('messages', []))} messages and {len(conversation.get('files', []))} files\033[0m"
                )
                # Convert ObjectId to string
                conversation["_id"] = str(conversation["_id"])
                return conversation
            else:
                print(
                    f"\033[91m[MongoDBService.get_conversation] Conversation not found: {conversation_id}\033[0m"
                )
                return None

        except Exception as e:
            print(f"\033[91m[MongoDBService.get_conversation] ERROR: {e}\033[0m")
            raise e

    def get_conversation_messages(
        self, conversation_id: str, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from conversation with pagination"""
        print(
            f"\033[92m[MongoDBService.get_conversation_messages] Getting messages - conversation_id: {conversation_id}, limit: {limit}, skip: {skip}\033[0m"
        )

        try:
            pipeline = [
                {"$match": {"conversation_id": conversation_id}},
                {"$project": {"messages": {"$slice": ["$messages", skip, limit]}}},
            ]

            result = list(self.conversations_collection.aggregate(pipeline))

            if result:
                messages = result[0].get("messages", [])
                print(
                    f"\033[92m[MongoDBService.get_conversation_messages] Retrieved {len(messages)} messages\033[0m"
                )
                return messages
            else:
                print(
                    f"\033[91m[MongoDBService.get_conversation_messages] No conversation found: {conversation_id}\033[0m"
                )
                return []

        except Exception as e:
            print(
                f"\033[91m[MongoDBService.get_conversation_messages] ERROR: {e}\033[0m"
            )
            raise e

    def get_conversation_files(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get files from conversation"""
        print(
            f"\033[92m[MongoDBService.get_conversation_files] Getting files for conversation: {conversation_id}\033[0m"
        )

        try:
            conversation = self.conversations_collection.find_one(
                {"conversation_id": conversation_id}, {"files": 1}
            )

            if conversation:
                files = conversation.get("files", [])
                print(
                    f"\033[92m[MongoDBService.get_conversation_files] Found {len(files)} files\033[0m"
                )
                return files
            else:
                print(
                    f"\033[91m[MongoDBService.get_conversation_files] No conversation found: {conversation_id}\033[0m"
                )
                return []

        except Exception as e:
            print(f"\033[91m[MongoDBService.get_conversation_files] ERROR: {e}\033[0m")
            raise e

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from MongoDB"""
        print(
            f"\033[92m[MongoDBService.delete_conversation] Deleting conversation: {conversation_id}\033[0m"
        )

        try:
            result = self.conversations_collection.delete_one(
                {"conversation_id": conversation_id}
            )

            if result.deleted_count > 0:
                print(
                    f"\033[92m[MongoDBService.delete_conversation] Conversation deleted successfully\033[0m"
                )
                return True
            else:
                print(
                    f"\033[91m[MongoDBService.delete_conversation] No conversation found to delete: {conversation_id}\033[0m"
                )
                return False

        except Exception as e:
            print(f"\033[91m[MongoDBService.delete_conversation] ERROR: {e}\033[0m")
            raise e

    def remove_file_from_conversation(self, conversation_id: str, file_id: str) -> bool:
        """Remove file reference from conversation"""
        print(
            f"\033[92m[MongoDBService.remove_file_from_conversation] Removing file - conversation_id: {conversation_id}, file_id: {file_id}\033[0m"
        )

        try:
            result = self.conversations_collection.update_one(
                {"conversation_id": conversation_id},
                {
                    "$pull": {"files": {"file_id": file_id}},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            if result.modified_count > 0:
                print(
                    f"\033[92m[MongoDBService.remove_file_from_conversation] File reference removed successfully\033[0m"
                )
                return True
            else:
                print(
                    f"\033[91m[MongoDBService.remove_file_from_conversation] No file found to remove\033[0m"
                )
                return False

        except Exception as e:
            print(
                f"\033[91m[MongoDBService.remove_file_from_conversation] ERROR: {e}\033[0m"
            )
            raise e


# Global instance
mongodb_service = MongoDBService()
