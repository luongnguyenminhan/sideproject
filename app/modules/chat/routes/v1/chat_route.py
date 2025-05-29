import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.chat.repository.chat_repo import ChatRepo
from app.modules.chat.schemas.chat_request import SendMessageRequest
from app.modules.chat.schemas.chat_response import SendMessageResponse
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.auth_middleware import verify_token
from app.http.oauth2 import get_current_user, verify_websocket_token
from app.middleware.translation_manager import _
from app.exceptions.exception import ValidationException
import logging

logger = logging.getLogger(__name__)

route = APIRouter(prefix="/chat", tags=["Chat"], dependencies=[Depends(verify_token)])


class WebSocketManager:
    """Manage WebSocket connections for chat"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connection established for user: {user_id}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket connection closed for user: {user_id}")

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@route.websocket("/ws/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time chat messaging"""
    try:
        # Verify WebSocket token
        try:
            token_data = verify_websocket_token(token)
            user_id = token_data.get("user_id")
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
        except Exception as e:
            logger.error(f"WebSocket token verification failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return

        chat_repo = ChatRepo(db)

        # Verify user has access to conversation
        try:
            conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
        except:
            await websocket.close(code=4003, reason="Forbidden")
            return

        await websocket_manager.connect(websocket, user_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get("type") == "chat_message":
                    content = message_data.get("content", "").strip()
                    api_key = message_data.get("api_key")

                    if not content:
                        await websocket_manager.send_message(
                            user_id,
                            {"type": "error", "message": _("message_content_required")},
                        )
                        continue

                    # Create user message
                    user_message = chat_repo.create_message(
                        conversation_id=conversation_id,
                        user_id=user_id,
                        content=content,
                        role="user",
                    )

                    # Send user message confirmation
                    await websocket_manager.send_message(
                        user_id,
                        {
                            "type": "user_message",
                            "message": {
                                "id": user_message.id,
                                "content": content,
                                "role": "user",
                                "timestamp": user_message.timestamp.isoformat(),
                            },
                        },
                    )

                    # Send typing indicator
                    await websocket_manager.send_message(
                        user_id, {"type": "assistant_typing", "status": True}
                    )

                    try:
                        # Get AI response with streaming
                        ## TODO: This will integrate with LangChain/LangGraph agent
                        ai_response = await chat_repo.get_ai_response_streaming(
                            conversation_id=conversation_id,
                            user_message=content,
                            api_key=api_key,
                            websocket_manager=websocket_manager,
                            user_id=user_id,
                        )

                        # Create AI message in database
                        ai_message = chat_repo.create_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            content=ai_response["content"],
                            role="assistant",
                            model_used=ai_response.get("model_used"),
                            tokens_used=json.dumps(ai_response.get("usage", {})),
                            response_time_ms=str(
                                ai_response.get("response_time_ms", 0)
                            ),
                        )

                        # Send final message confirmation
                        await websocket_manager.send_message(
                            user_id,
                            {
                                "type": "assistant_message_complete",
                                "message": {
                                    "id": ai_message.id,
                                    "content": ai_message.content,
                                    "role": "assistant",
                                    "timestamp": ai_message.timestamp.isoformat(),
                                    "model_used": ai_message.model_used,
                                    "response_time_ms": ai_message.response_time_ms,
                                },
                            },
                        )

                    except Exception as e:
                        logger.error(f"Error getting AI response: {e}")
                        await websocket_manager.send_message(
                            user_id,
                            {"type": "error", "message": _("ai_response_error")},
                        )

                    finally:
                        # Stop typing indicator
                        await websocket_manager.send_message(
                            user_id, {"type": "assistant_typing", "status": False}
                        )

                elif message_data.get("type") == "ping":
                    # Respond to ping
                    await websocket_manager.send_message(user_id, {"type": "pong"})

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            try:
                await websocket_manager.send_message(
                    user_id, {"type": "error", "message": _("websocket_error")}
                )
            except:
                pass
        finally:
            websocket_manager.disconnect(user_id)

    except Exception as e:
        logger.error(f"Fatal WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass


@route.post("/send-message", response_model=APIResponse)
@handle_exceptions
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a chat message (non-streaming alternative)"""
    chat_repo = ChatRepo(db)
    user_id = current_user.get("user_id")

    # Verify user has access to conversation
    conversation = chat_repo.get_conversation_by_id(request.conversation_id, user_id)

    # Create user message
    user_message = chat_repo.create_message(
        conversation_id=request.conversation_id,
        user_id=user_id,
        content=request.content,
        role="user",
    )

    try:
        # Get AI response (non-streaming)
        ## TODO: This will integrate with LangChain/LangGraph agent
        ai_response = await chat_repo.get_ai_response(
            conversation_id=request.conversation_id,
            user_message=request.content,
            api_key=request.api_key,
        )

        # Create AI message
        ai_message = chat_repo.create_message(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=ai_response["content"],
            role="assistant",
            model_used=ai_response.get("model_used"),
            tokens_used=json.dumps(ai_response.get("usage", {})),
            response_time_ms=str(ai_response.get("response_time_ms", 0)),
        )

        return APIResponse(
            error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
            message=_("message_sent_successfully"),
            data=SendMessageResponse(
                user_message=user_message.dict(), ai_message=ai_message.dict()
            ),
        )

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise ValidationException(_("failed_to_send_message"))
