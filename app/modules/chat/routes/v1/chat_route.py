import json
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.enums.base_enums import BaseErrorCode
from app.modules.chat.repository.chat_repo import ChatRepo
from app.modules.chat.schemas.chat_request import SendMessageRequest
from app.modules.chat.schemas.chat_response import SendMessageResponse
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.http.oauth2 import get_current_user, verify_websocket_token
from app.middleware.translation_manager import _
from app.exceptions.exception import ValidationException
from app.middleware.websocket_middleware import WebSocketErrorHandler
import logging

logger = logging.getLogger(__name__)

route = APIRouter(prefix="/chat", tags=["Chat"])


class WebSocketManager:
    """Manage WebSocket connections for chat"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        logger.info(
            f"\033[95m[WebSocketManager.__init__] WebSocketManager initialized\033[0m"
        )

    async def connect(self, websocket: WebSocket, user_id: str):
        logger.info(
            f"\033[94m[WebSocketManager.connect] Connecting user: {user_id}\033[0m"
        )
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(
            f"\033[92m[WebSocketManager.connect] Connection established for user: {user_id}, total connections: {len(self.active_connections)}\033[0m"
        )
        logger.info(f"WebSocket connection established for user: {user_id}")

    def disconnect(self, user_id: str):
        logger.info(
            f"\033[93m[WebSocketManager.disconnect] Disconnecting user: {user_id}\033[0m"
        )
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(
                f"\033[92m[WebSocketManager.disconnect] User {user_id} disconnected, remaining connections: {len(self.active_connections)}\033[0m"
            )
            logger.info(f"WebSocket connection closed for user: {user_id}")
        else:
            logger.info(
                f"\033[91m[WebSocketManager.disconnect] User {user_id} not found in active connections\033[0m"
            )

    async def send_message(self, user_id: str, message: dict):
        logger.info(
            f'\033[96m[WebSocketManager.send_message] Sending to user {user_id}: {message.get("type", "unknown_type")}\033[0m'
        )
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                message_str = json.dumps(message)
                logger.info(
                    f"\033[94m[WebSocketManager.send_message] Message size: {len(message_str)} chars\033[0m"
                )
                await websocket.send_text(message_str)
                logger.info(
                    f"\033[92m[WebSocketManager.send_message] Message sent successfully to user: {user_id}\033[0m"
                )
            except Exception as e:
                logger.info(
                    f"\033[91m[WebSocketManager.send_message] Error sending message to user {user_id}: {e}\033[0m"
                )
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
        else:
            logger.info(
                f"\033[91m[WebSocketManager.send_message] User {user_id} not found in active connections\033[0m"
            )


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


@route.post("/websocket/token", response_model=APIResponse)
@handle_exceptions
async def get_websocket_token(
    current_user: dict = Depends(get_current_user),
):
    """Generate WebSocket token for authentication"""
    logger.info(f"\033[95m[get_websocket_token] Starting token generation\033[0m")
    from app.http.oauth2 import create_websocket_token

    user_id = current_user.get("user_id")
    email = current_user.get("email")
    role = current_user.get("role", "user")

    logger.info(
        f"\033[94m[get_websocket_token] User data - ID: {user_id}, Email: {email}, Role: {role}\033[0m"
    )
    logger.info(f"Generating WebSocket token for user: {user_id}, email: {email}")

    # Create token with all required user data
    user_data = {"user_id": user_id, "email": email, "role": role}

    logger.info(
        f"\033[96m[get_websocket_token] Creating token with user data: {user_data}\033[0m"
    )
    token = create_websocket_token(user_data)

    logger.info(
        f"\033[92m[get_websocket_token] Token generated successfully for user: {user_id}\033[0m"
    )
    logger.info(f"WebSocket token generated successfully for user: {user_id}")

    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("websocket_token_generated"),
        data={"token": token, "expires_in": 3600},
    )


@route.websocket("/ws/{conversation_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for real-time chat messaging"""
    logger.info(
        f"\033[95m[websocket_chat_endpoint] Starting WebSocket connection for conversation: {conversation_id}\033[0m"
    )

    user_id = None
    try:
        # Get token from query parameters
        query_params = dict(websocket.query_params)
        token = query_params.get("token")

        logger.info(
            f"\033[94m[websocket_chat_endpoint] Query params: {list(query_params.keys())}\033[0m"
        )
        logger.info(
            f'\033[94m[websocket_chat_endpoint] Token present: {"Yes" if token else "No"}\033[0m'
        )
        logger.info(f"WebSocket connection attempt for conversation: {conversation_id}")
        logger.info(f'Token received: {"Yes" if token else "No"}')

        # Verify WebSocket token
        try:
            logger.info(
                f"\033[96m[websocket_chat_endpoint] Starting token verification\033[0m"
            )
            if not token:
                logger.info(
                    f"\033[91m[websocket_chat_endpoint] Token missing - closing connection\033[0m"
                )
                logger.error("WebSocket token missing")
                await WebSocketErrorHandler.handle_auth_error(
                    websocket, reason="Token required"
                )
                return

            logger.info(f"\033[94m[websocket_chat_endpoint] Verifying token\033[0m")
            token_data = verify_websocket_token(token)
            logger.info(
                f"\033[96m[websocket_chat_endpoint] Token data: {token_data}\033[0m"
            )

            user_id = token_data.get("user_id")
            if not user_id:
                logger.info(
                    f"\033[91m[websocket_chat_endpoint] Invalid token - no user_id\033[0m"
                )
                logger.error("WebSocket token invalid - no user_id")
                await WebSocketErrorHandler.handle_auth_error(
                    websocket, reason="Invalid token"
                )
                return

            logger.info(
                f"\033[92m[websocket_chat_endpoint] Authentication successful for user: {user_id}\033[0m"
            )
            logger.info(f"WebSocket authentication successful for user: {user_id}")
        except Exception as e:
            logger.info(
                f"\033[91m[websocket_chat_endpoint] Token verification failed: {e}\033[0m"
            )
            logger.error(f"WebSocket token verification failed: {e}")
            await WebSocketErrorHandler.handle_auth_error(
                websocket, reason="Authentication failed"
            )
            return

        logger.info(
            f"\033[96m[websocket_chat_endpoint] Creating ChatRepo instance\033[0m"
        )
        chat_repo = ChatRepo(db)

        # Verify user has access to conversation
        try:
            logger.info(
                f"\033[94m[websocket_chat_endpoint] Verifying user access to conversation\033[0m"
            )
            conversation = chat_repo.get_conversation_by_id(conversation_id, user_id)
            logger.info(
                f"\033[92m[websocket_chat_endpoint] User has access to conversation: {conversation_id}\033[0m"
            )
        except Exception as e:
            logger.info(
                f"\033[91m[websocket_chat_endpoint] Access denied to conversation: {e}\033[0m"
            )
            await WebSocketErrorHandler.handle_forbidden_error(
                websocket, reason="Access denied to conversation"
            )
            return

        logger.info(
            f"\033[96m[websocket_chat_endpoint] Connecting to WebSocket manager\033[0m"
        )
        await websocket_manager.connect(websocket, user_id)
        try:
            logger.info(
                f"\033[95m[websocket_chat_endpoint] Starting message loop for user: {user_id}\033[0m"
            )
            while True:
                # Receive message from client
                logger.info(
                    f"\033[94m[websocket_chat_endpoint] Waiting for message from client\033[0m"
                )
                data = await websocket.receive_text()
                logger.info(
                    f'\033[96m[websocket_chat_endpoint] Received raw data: {data[:200]}{"..." if len(data) > 200 else ""}\033[0m'
                )

                try:
                    message_data = json.loads(data)
                    logger.info(
                        f'\033[94m[websocket_chat_endpoint] Parsed message type: {message_data.get("type", "unknown")}\033[0m'
                    )
                except json.JSONDecodeError as e:
                    logger.info(
                        f"\033[91m[websocket_chat_endpoint] JSON decode error: {e}\033[0m"
                    )
                    await websocket_manager.send_message(
                        user_id,
                        {"type": "error", "message": "Invalid JSON format"},
                    )
                    continue

                if message_data.get("type") == "chat_message":
                    logger.info(
                        f"\033[95m[websocket_chat_endpoint] Processing chat message\033[0m"
                    )
                    content = message_data.get("content", "").strip()
                    api_key = message_data.get("api_key")

                    logger.info(
                        f"\033[94m[websocket_chat_endpoint] Message content length: {len(content)}\033[0m"
                    )
                    logger.info(
                        f'\033[94m[websocket_chat_endpoint] API key provided: {"Yes" if api_key else "No"}\033[0m'
                    )

                    if not content:
                        logger.info(
                            f"\033[91m[websocket_chat_endpoint] Empty message content\033[0m"
                        )
                        await websocket_manager.send_message(
                            user_id,
                            {"type": "error", "message": _("message_content_required")},
                        )
                        continue

                    # Create user message
                    logger.info(
                        f"\033[96m[websocket_chat_endpoint] Creating user message in database\033[0m"
                    )
                    try:
                        user_message = chat_repo.create_message(
                            conversation_id=conversation_id,
                            user_id=user_id,
                            content=content,
                            role="user",
                        )
                        logger.info(
                            f"\033[92m[websocket_chat_endpoint] User message created with ID: {user_message.id}\033[0m"
                        )
                    except Exception as e:
                        logger.info(
                            f"\033[91m[websocket_chat_endpoint] Failed to create user message: {e}\033[0m"
                        )
                        await websocket_manager.send_message(
                            user_id,
                            {"type": "error", "message": "Failed to save message"},
                        )
                        continue

                    # Send user message confirmation
                    logger.info(
                        f"\033[96m[websocket_chat_endpoint] Sending user message confirmation\033[0m"
                    )
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
                    logger.info(
                        f"\033[96m[websocket_chat_endpoint] Sending typing indicator\033[0m"
                    )
                    await websocket_manager.send_message(
                        user_id, {"type": "assistant_typing", "status": True}
                    )

                    try:
                        # Get AI response with streaming using Agent system
                        logger.info(
                            f"\033[95m[websocket_chat_endpoint] Getting AI response via Agent system\033[0m"
                        )
                        ai_response = await chat_repo.get_ai_response(
                            conversation_id=conversation_id,
                            user_message=content,
                            api_key=api_key,
                            user_id=user_id,
                        )
                        logger.info(
                            f"\033[92m[websocket_chat_endpoint] Agent response received: {ai_response}\033[0m"
                        )

                        # Create AI message in database
                        logger.info(
                            f"\033[96m[websocket_chat_endpoint] Creating AI message in database\033[0m"
                        )
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
                        logger.info(
                            f"\033[92m[websocket_chat_endpoint] AI message created with ID: {ai_message.id}\033[0m"
                        )

                        # Send final message confirmation
                        logger.info(
                            f"\033[96m[websocket_chat_endpoint] Sending AI message confirmation\033[0m"
                        )
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
                        logger.info(
                            f"\033[92m[websocket_chat_endpoint] AI message sent successfully\033[0m"
                        )

                    except Exception as e:
                        logger.info(
                            f"\033[91m[websocket_chat_endpoint] Error getting AI response: {e}\033[0m"
                        )
                        logger.error(f"Error getting AI response: {e}")
                        await websocket_manager.send_message(
                            user_id,
                            {"type": "error", "message": _("ai_response_error")},
                        )

                    finally:
                        # Stop typing indicator
                        logger.info(
                            f"\033[96m[websocket_chat_endpoint] Stopping typing indicator\033[0m"
                        )
                        await websocket_manager.send_message(
                            user_id, {"type": "assistant_typing", "status": False}
                        )

                elif message_data.get("type") == "ping":
                    logger.info(
                        f"\033[94m[websocket_chat_endpoint] Received ping, sending pong\033[0m"
                    )
                    # Respond to ping
                    await websocket_manager.send_message(user_id, {"type": "pong"})
                else:
                    logger.info(
                        f'\033[93m[websocket_chat_endpoint] Unknown message type: {message_data.get("type")}\033[0m'
                    )

        except WebSocketDisconnect:
            logger.info(
                f"\033[93m[websocket_chat_endpoint] WebSocket disconnected for user: {user_id}\033[0m"
            )
            logger.info(f"WebSocket disconnected for user: {user_id}")
        except Exception as e:
            logger.info(
                f"\033[91m[websocket_chat_endpoint] WebSocket error for user {user_id}: {e}\033[0m"
            )
            logger.error(f"WebSocket error for user {user_id}: {e}")
            try:
                await websocket_manager.send_message(
                    user_id, {"type": "error", "message": _("websocket_error")}
                )
            except:
                logger.info(
                    f"\033[91m[websocket_chat_endpoint] Failed to send error message to user {user_id}\033[0m"
                )
        finally:
            if user_id:
                logger.info(
                    f"\033[93m[websocket_chat_endpoint] Cleaning up connection for user: {user_id}\033[0m"
                )
                websocket_manager.disconnect(user_id)

    except Exception as e:
        logger.info(
            f"\033[91m[websocket_chat_endpoint] Fatal WebSocket error: {e}\033[0m"
        )
        logger.error(f"Fatal WebSocket error: {e}")
        try:
            await WebSocketErrorHandler.handle_auth_error(
                websocket, 1011, "Internal server error"
            )
        except:
            logger.info(
                f"\033[91m[websocket_chat_endpoint] Failed to close WebSocket connection\033[0m"
            )


@route.post("/send-message", response_model=APIResponse)
@handle_exceptions
async def send_message(
    request: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Send a chat message (non-streaming alternative)"""
    logger.info(f"\033[95m[send_message] Starting non-streaming message send\033[0m")
    chat_repo = ChatRepo(db)
    user_id = current_user.get("user_id")

    logger.info(
        f"\033[94m[send_message] User ID: {user_id}, Conversation ID: {request.conversation_id}\033[0m"
    )
    logger.info(
        f"\033[94m[send_message] Message content length: {len(request.content)}\033[0m"
    )

    # Verify user has access to conversation
    logger.info(f"\033[96m[send_message] Verifying user access to conversation\033[0m")
    try:
        conversation = chat_repo.get_conversation_by_id(
            request.conversation_id, user_id
        )
        logger.info(f"\033[92m[send_message] User has access to conversation\033[0m")
    except Exception as e:
        logger.info(f"\033[91m[send_message] Access verification failed: {e}\033[0m")
        raise

    # Create user message
    logger.info(f"\033[96m[send_message] Creating user message\033[0m")
    try:
        user_message = chat_repo.create_message(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=request.content,
            role="user",
            file_ids=request.file_ids,
        )
        logger.info(
            f"\033[92m[send_message] User message created with ID: {user_message.id}\033[0m"
        )
    except Exception as e:
        logger.info(f"\033[91m[send_message] Failed to create user message: {e}\033[0m")
        raise

    try:
        # Get AI response using Agent system (non-streaming)
        logger.info(
            f"\033[95m[send_message] Getting AI response via Agent system (non-streaming)\033[0m"
        )
        ai_response = await chat_repo.get_ai_response(
            conversation_id=request.conversation_id,
            user_message=request.content,
            api_key=request.api_key,
            user_id=user_id,
        )
        logger.info(
            f'\033[92m[send_message] Agent response received: {ai_response.get("model_used", "unknown_model")}\033[0m'
        )

        # Create AI message
        logger.info(f"\033[96m[send_message] Creating AI message\033[0m")
        ai_message = chat_repo.create_message(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=ai_response["content"],
            role="assistant",
            model_used=ai_response.get("model_used"),
            tokens_used=json.dumps(ai_response.get("usage", {})),
            response_time_ms=str(ai_response.get("response_time_ms", 0)),
        )
        logger.info(
            f"\033[92m[send_message] AI message created with ID: {ai_message.id}\033[0m"
        )
        logger.info(
            f"\033[92m[send_message] Message exchange completed successfully\033[0m"
        )
        return APIResponse(
            error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
            message=_("message_sent_successfully"),
            data=SendMessageResponse(
                user_message=user_message.dict(include_relationships=False),
                ai_message=ai_message.dict(include_relationships=False),
            ),
        )

    except Exception as e:
        logger.info(f"\033[91m[send_message] Error sending message: {e}\033[0m")
        logger.error(f"Error sending message: {e}")
        raise ValidationException(_("failed_to_send_message"))


@route.get("/files/{file_id}/download", response_model=APIResponse)
@handle_exceptions
async def get_file_download_url(
    file_id: str,
    expires: int = 3600,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get temporary download URL for file in chat context"""
    from app.modules.chat.repository.file_repo import FileRepo

    file_repo = FileRepo(db)
    user_id = current_user.get("user_id")
    download_url = file_repo.get_file_download_url(file_id, user_id, expires)

    return APIResponse(
        error_code=BaseErrorCode.ERROR_CODE_SUCCESS,
        message=_("download_url_generated"),
        data={"download_url": download_url, "expires_in": expires},
    )
