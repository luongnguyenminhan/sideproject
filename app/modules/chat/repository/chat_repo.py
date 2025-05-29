from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.chat.dal.message_dal import MessageDAL
from app.modules.chat.dal.api_key_dal import ApiKeyDAL
from app.modules.chat.services.mongodb_service import mongodb_service
from app.exceptions.exception import NotFoundException, ValidationException
from app.middleware.translation_manager import _
from datetime import datetime
import time
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ChatRepo:
    def __init__(self, db: Session = Depends(get_db)):
        print(
            f"\033[96m[ChatRepo.__init__] Initializing ChatRepo with db session: {db}\033[0m"
        )
        self.db = db
        self.conversation_dal = ConversationDAL(db)
        self.message_dal = MessageDAL(db)
        self.api_key_dal = ApiKeyDAL(db)
        print(f"\033[92m[ChatRepo.__init__] ChatRepo initialized successfully\033[0m")

    def get_conversation_by_id(self, conversation_id: str, user_id: str):
        """Get conversation by ID and verify user access"""
        print(
            f"\033[93m[ChatRepo.get_conversation_by_id] Getting conversation: {conversation_id} for user: {user_id}\033[0m"
        )
        conversation = self.conversation_dal.get_user_conversation_by_id(
            conversation_id, user_id
        )
        if not conversation:
            print(
                f"\033[91m[ChatRepo.get_conversation_by_id] Conversation not found: {conversation_id}\033[0m"
            )
            raise NotFoundException(_("conversation_not_found"))
        print(
            f"\033[92m[ChatRepo.get_conversation_by_id] Conversation found: {conversation.name}\033[0m"
        )
        return conversation

    def create_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        role: str,
        model_used: str = None,
        tokens_used: str = None,
        response_time_ms: str = None,
    ):
        """Create a new message in the conversation"""
        print(
            f"\033[93m[ChatRepo.create_message] Creating message in conversation: {conversation_id}, user: {user_id}, role: {role}, content_length: {len(content)}, model: {model_used}, tokens: {tokens_used}, response_time: {response_time_ms}ms\033[0m"
        )
        # Verify conversation exists and user has access
        conversation = self.get_conversation_by_id(conversation_id, user_id)
        print(
            f"\033[94m[ChatRepo.create_message] Conversation verified: {conversation.name}\033[0m"
        )

        message_timestamp = datetime.utcnow()
        print(
            f"\033[96m[ChatRepo.create_message] Message timestamp: {message_timestamp}\033[0m"
        )

        # Create message metadata in MySQL
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": message_timestamp,
            "model_used": model_used,
            "tokens_used": tokens_used,
            "response_time_ms": response_time_ms,
        }
        print(
            f"\033[96m[ChatRepo.create_message] Created message_data for MySQL\033[0m"
        )

        with self.message_dal.transaction():
            print(f"\033[94m[ChatRepo.create_message] Creating message in MySQL\033[0m")
            message = self.message_dal.create(message_data)
            print(
                f"\033[92m[ChatRepo.create_message] Message created in MySQL with ID: {message.id}\033[0m"
            )

            # Store full message content in MongoDB
            mongo_message_data = {
                "message_id": message.id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "timestamp": message_timestamp,
                "model_used": model_used,
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms,
            }
            print(
                f"\033[96m[ChatRepo.create_message] Created mongo_message_data for MongoDB\033[0m"
            )

            try:
                print(
                    f"\033[94m[ChatRepo.create_message] Saving message to MongoDB\033[0m"
                )
                mongodb_service.save_message(mongo_message_data)
                print(
                    f"\033[92m[ChatRepo.create_message] Message saved to MongoDB successfully\033[0m"
                )
            except Exception as e:
                print(
                    f"\033[91m[ChatRepo.create_message] Failed to save message to MongoDB: {e}\033[0m"
                )
                logger.error(f"Failed to save message to MongoDB: {e}")

            # Update conversation activity and message count
            print(
                f"\033[94m[ChatRepo.create_message] Updating conversation activity and message count\033[0m"
            )
            conversation.last_activity = message_timestamp
            conversation.message_count += 1
            print(
                f"\033[96m[ChatRepo.create_message] New message count: {conversation.message_count}\033[0m"
            )
            self.conversation_dal.update(
                conversation.id,
                {
                    "last_activity": conversation.last_activity,
                    "message_count": conversation.message_count,
                },
            )
            print(
                f"\033[92m[ChatRepo.create_message] Conversation updated successfully\033[0m"
            )

            return message

    async def get_ai_response(
        self, conversation_id: str, user_message: str, api_key: str = None
    ) -> dict:
        """Get AI response for a message (non-streaming)"""
        print(
            f"\033[93m[ChatRepo.get_ai_response] Getting AI response for conversation: {conversation_id}, message_length: {len(user_message)}, has_api_key: {api_key is not None}\033[0m"
        )
        start_time = time.time()

        # Get conversation history for context from MongoDB
        try:
            print(
                f"\033[94m[ChatRepo.get_ai_response] Getting conversation history from MongoDB\033[0m"
            )
            conversation_history = mongodb_service.get_conversation_history(
                conversation_id=conversation_id, limit=10
            )
            print(
                f"\033[92m[ChatRepo.get_ai_response] Retrieved {len(conversation_history)} messages from history\033[0m"
            )
        except Exception as e:
            print(
                f"\033[91m[ChatRepo.get_ai_response] Failed to get conversation history: {e}\033[0m"
            )
            logger.error(f"Failed to get conversation history from MongoDB: {e}")
            conversation_history = []

        # Get user's API key if not provided
        if not api_key:
            print(
                f"\033[94m[ChatRepo.get_ai_response] No API key provided, getting user's default key\033[0m"
            )
            conversation = self.get_conversation_by_id(conversation_id, "")
            print(
                f"\033[94m[ChatRepo.get_ai_response] Getting default API key for user: {conversation.user_id}\033[0m"
            )
            default_key = self.api_key_dal.get_user_default_api_key(
                user_id=conversation.user_id, provider="openai"
            )
            if default_key:
                api_key = default_key.get_api_key()
                print(
                    f"\033[92m[ChatRepo.get_ai_response] Found default API key for OpenAI\033[0m"
                )

        if not api_key:
            print(f"\033[91m[ChatRepo.get_ai_response] No API key available\033[0m")
            raise ValidationException(_("api_key_required"))

        try:
            print(
                f"\033[94m[ChatRepo.get_ai_response] Calling AI response simulation\033[0m"
            )
            ai_response = await self._simulate_ai_response(
                message=user_message, history=conversation_history, api_key=api_key
            )
            response_time = int((time.time() - start_time) * 1000)
            print(
                f"\033[92m[ChatRepo.get_ai_response] AI response received, response_time: {response_time}ms, content_length: {len(ai_response['content'])}\033[0m"
            )

            return {
                "content": ai_response["content"],
                "model_used": ai_response.get("model", "gpt-3.5-turbo"),
                "usage": ai_response.get("usage", {}),
                "response_time_ms": response_time,
            }

        except Exception as e:
            print(
                f"\033[91m[ChatRepo.get_ai_response] Error getting AI response: {e}\033[0m"
            )
            logger.error(f"Error getting AI response: {e}")
            raise ValidationException(_("ai_response_error"))

    async def get_ai_response_streaming(
        self,
        conversation_id: str,
        user_message: str,
        api_key: str = None,
        websocket_manager=None,
        user_id: str = None,
    ) -> dict:
        """Get AI response with streaming support"""
        print(
            f"\033[93m[ChatRepo.get_ai_response_streaming] Getting streaming AI response for conversation: {conversation_id}, user: {user_id}, message_length: {len(user_message)}, has_websocket: {websocket_manager is not None}\033[0m"
        )
        start_time = time.time()

        # Get conversation history for context from MongoDB
        try:
            print(
                f"\033[94m[ChatRepo.get_ai_response_streaming] Getting conversation history from MongoDB\033[0m"
            )
            conversation_history = mongodb_service.get_conversation_history(
                conversation_id=conversation_id, limit=10
            )
            print(
                f"\033[92m[ChatRepo.get_ai_response_streaming] Retrieved {len(conversation_history)} messages from history\033[0m"
            )
        except Exception as e:
            print(
                f"\033[91m[ChatRepo.get_ai_response_streaming] Failed to get conversation history: {e}\033[0m"
            )
            logger.error(f"Failed to get conversation history from MongoDB: {e}")
            conversation_history = []

        # Get user's API key if not provided
        if not api_key:
            print(
                f"\033[94m[ChatRepo.get_ai_response_streaming] No API key provided, getting user's default key\033[0m"
            )
            conversation = self.get_conversation_by_id(conversation_id, user_id)
            print(
                f"\033[94m[ChatRepo.get_ai_response_streaming] Getting default API key for user: {conversation.user_id}\033[0m"
            )
            default_key = self.api_key_dal.get_user_default_api_key(
                user_id=conversation.user_id, provider="openai"
            )
            if default_key:
                api_key = default_key.get_api_key()
                print(
                    f"\033[92m[ChatRepo.get_ai_response_streaming] Found default API key for OpenAI\033[0m"
                )

        if not api_key:
            print(
                f"\033[91m[ChatRepo.get_ai_response_streaming] No API key available\033[0m"
            )
            raise ValidationException(_("api_key_required"))

        try:
            print(
                f"\033[94m[ChatRepo.get_ai_response_streaming] Calling streaming AI response simulation\033[0m"
            )
            full_response = await self._simulate_streaming_ai_response(
                message=user_message,
                history=conversation_history,
                api_key=api_key,
                websocket_manager=websocket_manager,
                user_id=user_id,
            )
            response_time = int((time.time() - start_time) * 1000)
            print(
                f"\033[92m[ChatRepo.get_ai_response_streaming] Streaming AI response completed, response_time: {response_time}ms, content_length: {len(full_response['content'])}\033[0m"
            )

            return {
                "content": full_response["content"],
                "model_used": full_response.get("model", "gpt-3.5-turbo"),
                "usage": full_response.get("usage", {}),
                "response_time_ms": response_time,
            }

        except Exception as e:
            print(
                f"\033[91m[ChatRepo.get_ai_response_streaming] Error getting streaming AI response: {e}\033[0m"
            )
            logger.error(f"Error getting streaming AI response: {e}")
            raise ValidationException(_("ai_response_error"))

    async def _simulate_ai_response(
        self, message: str, history: list, api_key: str
    ) -> dict:
        """
        Simulate AI response (replace with actual LangChain/LangGraph integration)
        ## TODO: Replace with actual LangChain/LangGraph agent implementation
        """
        print(
            f"\033[93m[ChatRepo._simulate_ai_response] Simulating AI response for message_length: {len(message)}, history_count: {len(history)}\033[0m"
        )
        # Simulate processing delay
        print(
            f"\033[94m[ChatRepo._simulate_ai_response] Simulating processing delay\033[0m"
        )
        await asyncio.sleep(1)

        # Simple response based on input
        response_content = f"I received your message: '{message}'. This is a simulated response with **markdown** support and `code` formatting. "

        if "hello" in message.lower():
            response_content += "Hello! How can I help you today?"
            print(
                f"\033[95m[ChatRepo._simulate_ai_response] Detected greeting in message\033[0m"
            )
        elif "how are you" in message.lower():
            response_content += "I'm doing well, thank you for asking!"
            print(
                f"\033[95m[ChatRepo._simulate_ai_response] Detected how are you question\033[0m"
            )
        else:
            response_content += (
                "I'm here to help you with any questions you might have."
            )
            print(
                f"\033[95m[ChatRepo._simulate_ai_response] Using default response\033[0m"
            )

        response_data = {
            "content": response_content,
            "model": "gpt-3.5-turbo-simulated",
            "usage": {
                "prompt_tokens": len(message.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(message.split()) + len(response_content.split()),
            },
        }
        print(
            f"\033[92m[ChatRepo._simulate_ai_response] AI response simulation completed, tokens: {response_data['usage']['total_tokens']}\033[0m"
        )
        return response_data

    async def _simulate_streaming_ai_response(
        self,
        message: str,
        history: list,
        api_key: str,
        websocket_manager=None,
        user_id: str = None,
    ) -> dict:
        """
        Simulate streaming AI response (replace with actual LangChain/LangGraph integration)
        ## TODO: Replace with actual LangChain/LangGraph agent streaming implementation
        """
        print(
            f"\033[93m[ChatRepo._simulate_streaming_ai_response] Simulating streaming AI response for message_length: {len(message)}, history_count: {len(history)}, user: {user_id}\033[0m"
        )
        # Get the full response first
        full_response = await self._simulate_ai_response(message, history, api_key)
        response_text = full_response["content"]
        print(
            f"\033[94m[ChatRepo._simulate_streaming_ai_response] Full response generated, preparing to stream\033[0m"
        )

        if websocket_manager and user_id:
            print(
                f"\033[94m[ChatRepo._simulate_streaming_ai_response] Starting streaming simulation\033[0m"
            )
            # Simulate streaming by sending chunks
            words = response_text.split()
            current_chunk = ""
            print(
                f"\033[96m[ChatRepo._simulate_streaming_ai_response] Will stream {len(words)} words in chunks\033[0m"
            )

            for i, word in enumerate(words):
                current_chunk += word + " "

                # Send chunk every few words to simulate streaming
                if i % 3 == 0 or i == len(words) - 1:
                    print(
                        f"\033[95m[ChatRepo._simulate_streaming_ai_response] Sending chunk {i//3 + 1}, words: {i+1}/{len(words)}, is_final: {i == len(words) - 1}\033[0m"
                    )
                    await websocket_manager.send_message(
                        user_id,
                        {
                            "type": "assistant_message_chunk",
                            "chunk": current_chunk.strip(),
                            "is_final": i == len(words) - 1,
                        },
                    )
                    current_chunk = ""
                    # Small delay to simulate real streaming
                    await asyncio.sleep(0.1)

            print(
                f"\033[92m[ChatRepo._simulate_streaming_ai_response] Streaming simulation completed\033[0m"
            )

        return full_response
