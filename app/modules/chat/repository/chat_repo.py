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
        self.db = db
        self.conversation_dal = ConversationDAL(db)
        self.message_dal = MessageDAL(db)
        self.api_key_dal = ApiKeyDAL(db)

    def get_conversation_by_id(self, conversation_id: str, user_id: str):
        """Get conversation by ID and verify user access"""
        conversation = self.conversation_dal.get_user_conversation_by_id(
            conversation_id, user_id
        )
        if not conversation:
            raise NotFoundException(_("conversation_not_found"))
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
        # Verify conversation exists and user has access
        conversation = self.get_conversation_by_id(conversation_id, user_id)

        message_timestamp = datetime.utcnow()

        # Create message metadata in MySQL
        message_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": role,
            "content": content,  # Store in MySQL for metadata
            "timestamp": message_timestamp,
            "model_used": model_used,
            "tokens_used": tokens_used,
            "response_time_ms": response_time_ms,
        }

        with self.message_dal.transaction():
            message = self.message_dal.create(message_data)

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

            try:
                mongodb_service.save_message(mongo_message_data)
            except Exception as e:
                logger.error(f"Failed to save message to MongoDB: {e}")
                # Continue with MySQL operation even if MongoDB fails

            # Update conversation activity and message count
            conversation.last_activity = message_timestamp
            conversation.message_count += 1
            self.conversation_dal.update(
                conversation.id,
                {
                    "last_activity": conversation.last_activity,
                    "message_count": conversation.message_count,
                },
            )

            return message

    async def get_ai_response(
        self, conversation_id: str, user_message: str, api_key: str = None
    ) -> dict:
        """Get AI response for a message (non-streaming)"""
        start_time = time.time()

        # Get conversation history for context from MongoDB
        try:
            conversation_history = mongodb_service.get_conversation_history(
                conversation_id=conversation_id, limit=10
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history from MongoDB: {e}")
            conversation_history = []

        # Get user's API key if not provided
        if not api_key:
            conversation = self.get_conversation_by_id(conversation_id, "")
            default_key = self.api_key_dal.get_user_default_api_key(
                user_id=conversation.user_id, provider="openai"
            )
            if default_key:
                api_key = default_key.get_api_key()

        if not api_key:
            raise ValidationException(_("api_key_required"))

        try:
            ## TODO: Integrate with LangChain/LangGraph agent
            # This is a placeholder that simulates AI response
            ai_response = await self._simulate_ai_response(
                message=user_message, history=conversation_history, api_key=api_key
            )

            response_time = int((time.time() - start_time) * 1000)

            return {
                "content": ai_response["content"],
                "model_used": ai_response.get("model", "gpt-3.5-turbo"),
                "usage": ai_response.get("usage", {}),
                "response_time_ms": response_time,
            }

        except Exception as e:
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
        start_time = time.time()

        # Get conversation history for context from MongoDB
        try:
            conversation_history = mongodb_service.get_conversation_history(
                conversation_id=conversation_id, limit=10
            )
        except Exception as e:
            logger.error(f"Failed to get conversation history from MongoDB: {e}")
            conversation_history = []

        # Get user's API key if not provided
        if not api_key:
            conversation = self.get_conversation_by_id(conversation_id, user_id)
            default_key = self.api_key_dal.get_user_default_api_key(
                user_id=conversation.user_id, provider="openai"
            )
            if default_key:
                api_key = default_key.get_api_key()

        if not api_key:
            raise ValidationException(_("api_key_required"))

        try:
            ## TODO: Integrate with LangChain/LangGraph agent for streaming
            # This is a placeholder that simulates streaming AI response
            full_response = await self._simulate_streaming_ai_response(
                message=user_message,
                history=conversation_history,
                api_key=api_key,
                websocket_manager=websocket_manager,
                user_id=user_id,
            )

            response_time = int((time.time() - start_time) * 1000)

            return {
                "content": full_response["content"],
                "model_used": full_response.get("model", "gpt-3.5-turbo"),
                "usage": full_response.get("usage", {}),
                "response_time_ms": response_time,
            }

        except Exception as e:
            logger.error(f"Error getting streaming AI response: {e}")
            raise ValidationException(_("ai_response_error"))

    async def _simulate_ai_response(
        self, message: str, history: list, api_key: str
    ) -> dict:
        """
        Simulate AI response (replace with actual LangChain/LangGraph integration)
        ## TODO: Replace with actual LangChain/LangGraph agent implementation
        """
        # Simulate processing delay
        await asyncio.sleep(1)

        # Simple response based on input
        response_content = f"I received your message: '{message}'. This is a simulated response with **markdown** support and `code` formatting. "

        if "hello" in message.lower():
            response_content += "Hello! How can I help you today?"
        elif "how are you" in message.lower():
            response_content += "I'm doing well, thank you for asking!"
        else:
            response_content += (
                "I'm here to help you with any questions you might have."
            )

        return {
            "content": response_content,
            "model": "gpt-3.5-turbo-simulated",
            "usage": {
                "prompt_tokens": len(message.split()),
                "completion_tokens": len(response_content.split()),
                "total_tokens": len(message.split()) + len(response_content.split()),
            },
        }

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
        # Get the full response first
        full_response = await self._simulate_ai_response(message, history, api_key)
        response_text = full_response["content"]

        if websocket_manager and user_id:
            # Simulate streaming by sending chunks
            words = response_text.split()
            current_chunk = ""

            for i, word in enumerate(words):
                current_chunk += word + " "

                # Send chunk every few words to simulate streaming
                if i % 3 == 0 or i == len(words) - 1:
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

        return full_response
