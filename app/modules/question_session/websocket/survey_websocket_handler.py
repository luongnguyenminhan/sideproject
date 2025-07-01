"""
WebSocket Integration Example for Survey Response Processing
Demonstrates how to integrate the survey response API with WebSocket handlers
"""

import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.modules.question_session.services.survey_response_processor import SurveyResponseProcessor
from app.modules.question_session.services.survey_chat_integration import SurveyChatIntegrationService
from app.modules.question_session.schemas.question_session_request import ParseSurveyResponseRequest

logger = logging.getLogger(__name__)


class SurveyWebSocketHandler:
    """
    WebSocket handler for survey response processing
    
    This class demonstrates how to integrate the survey response processing
    with WebSocket connections for real-time AI feedback
    """

    def __init__(self, db: Session):
        self.db = db
        self.survey_processor = SurveyResponseProcessor(db)
        self.integration_service = SurveyChatIntegrationService(db)

    async def handle_survey_response_message(
        self,
        websocket_connection,
        message: Dict[str, Any],
        user_id: str
    ) -> None:
        """
        Handle incoming survey response message via WebSocket
        
        Args:
            websocket_connection: WebSocket connection object
            message: Survey response message data
            user_id: User ID from authentication
        """
        try:
            # Validate message type
            if message.get('type') != 'survey_response':
                await self._send_error(websocket_connection, "Invalid message type")
                return

            # Extract required fields
            conversation_id = message.get('conversation_id')
            answers = message.get('answers', {})
            
            if not conversation_id or not answers:
                await self._send_error(websocket_connection, "Missing required fields")
                return

            # Send processing acknowledgment
            await self._send_acknowledgment(websocket_connection, conversation_id)

            # Create request object
            request = ParseSurveyResponseRequest(
                type='survey_response',
                answers=answers,
                conversation_id=conversation_id,
                timestamp=message.get('timestamp')
            )

            # Process survey response with AI integration
            result = await self.integration_service.process_survey_and_chat_response(
                survey_request=request.model_dump(),
                conversation_id=conversation_id,
                user_id=user_id
            )

            # Send comprehensive response back via WebSocket
            await self._send_survey_result(websocket_connection, result)

            # Optional: Send AI response as a separate chat message
            if result.get('ai_response', {}).get('content'):
                await self._send_ai_chat_message(
                    websocket_connection,
                    result['ai_response']['content'],
                    conversation_id
                )

        except Exception as e:
            logger.error(f"Error handling survey response message: {e}")
            await self._send_error(websocket_connection, f"Processing error: {str(e)}")

    async def handle_format_survey_message(
        self,
        websocket_connection,
        message: Dict[str, Any],
        user_id: str
    ) -> None:
        """
        Handle request to format survey as human message
        
        Args:
            websocket_connection: WebSocket connection object
            message: Message data
            user_id: User ID from authentication
        """
        try:
            # Create request object
            request = ParseSurveyResponseRequest(
                type='survey_response',
                answers=message.get('answers', {}),
                conversation_id=message.get('conversation_id'),
                timestamp=message.get('timestamp')
            )

            # Format as human message
            human_message = await self.survey_processor.format_survey_response_as_human_message(
                request=request,
                user_id=user_id
            )

            # Send formatted message back
            response = {
                'type': 'survey_formatted',
                'conversation_id': message.get('conversation_id'),
                'human_message': human_message,
                'timestamp': message.get('timestamp'),
                'success': True
            }

            await websocket_connection.send_json(response)

        except Exception as e:
            logger.error(f"Error formatting survey message: {e}")
            await self._send_error(websocket_connection, f"Formatting error: {str(e)}")

    async def _send_acknowledgment(
        self,
        websocket_connection,
        conversation_id: str
    ) -> None:
        """Send processing acknowledgment"""
        ack_message = {
            'type': 'survey_processing_started',
            'conversation_id': conversation_id,
            'message': 'Survey response received and processing started',
            'timestamp': self._get_current_timestamp()
        }
        await websocket_connection.send_json(ack_message)

    async def _send_survey_result(
        self,
        websocket_connection,
        result: Dict[str, Any]
    ) -> None:
        """Send comprehensive survey processing result"""
        response_message = {
            'type': 'survey_processing_complete',
            'data': result,
            'timestamp': self._get_current_timestamp()
        }
        await websocket_connection.send_json(response_message)

    async def _send_ai_chat_message(
        self,
        websocket_connection,
        ai_content: str,
        conversation_id: str
    ) -> None:
        """Send AI response as a chat message"""
        chat_message = {
            'type': 'ai_message',
            'conversation_id': conversation_id,
            'content': ai_content,
            'source': 'survey_analysis',
            'timestamp': self._get_current_timestamp()
        }
        await websocket_connection.send_json(chat_message)

    async def _send_error(
        self,
        websocket_connection,
        error_message: str
    ) -> None:
        """Send error message"""
        error_response = {
            'type': 'survey_error',
            'error': error_message,
            'timestamp': self._get_current_timestamp()
        }
        await websocket_connection.send_json(error_response)

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()


# Example usage in a WebSocket route or handler
"""
# In your WebSocket handler

async def websocket_handler(websocket, db: Session):
    survey_handler = SurveyWebSocketHandler(db)
    
    try:
        while True:
            message = await websocket.receive_json()
            user_id = get_user_id_from_websocket(websocket)  # Your auth logic
            
            if message.get('type') == 'survey_response':
                await survey_handler.handle_survey_response_message(
                    websocket, message, user_id
                )
            elif message.get('type') == 'format_survey':
                await survey_handler.handle_format_survey_message(
                    websocket, message, user_id
                )
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
"""


class SurveyWebSocketMessages:
    """
    Utility class containing message format examples for survey WebSocket integration
    """

    @staticmethod
    def survey_response_message(conversation_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Create a survey response message"""
        return {
            'type': 'survey_response',
            'conversation_id': conversation_id,
            'answers': answers,
            'timestamp': SurveyWebSocketHandler()._get_current_timestamp()
        }

    @staticmethod
    def format_survey_message(conversation_id: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """Create a format survey message"""
        return {
            'type': 'format_survey',
            'conversation_id': conversation_id,
            'answers': answers,
            'timestamp': SurveyWebSocketHandler()._get_current_timestamp()
        }

    @staticmethod
    def survey_processing_complete_response(result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a processing complete response"""
        return {
            'type': 'survey_processing_complete',
            'data': result,
            'timestamp': SurveyWebSocketHandler()._get_current_timestamp()
        }
