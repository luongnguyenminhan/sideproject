"""
AI Chat Integration Service for Survey Responses
Integrates survey responses with the chat workflow and agent processing
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.modules.agent.services.langgraph_service import LangGraphService
from app.modules.agent.repository.system_agent_repo import SystemAgentRepo
from app.modules.chat.dal.conversation_dal import ConversationDAL
from app.modules.question_session.services.survey_response_processor import SurveyResponseProcessor

logger = logging.getLogger(__name__)


class SurveyChatIntegrationService:
    """Service to integrate survey responses with chat workflow and AI agents"""

    def __init__(self, db: Session):
        self.db = db
        self.langgraph_service = LangGraphService(db)
        self.agent_repo = SystemAgentRepo(db)
        self.conversation_dal = ConversationDAL(db)
        self.survey_processor = SurveyResponseProcessor(db)

    async def process_survey_and_chat_response(
        self,
        survey_request: Dict[str, Any],
        conversation_id: str,
        user_id: str,
        custom_ai_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Survey processing + AI chat response
        
        Args:
            survey_request: Survey response data
            conversation_id: Conversation ID
            user_id: User ID
            custom_ai_prompt: Optional custom prompt for AI processing

        Returns:
            Complete response with survey processing and AI feedback
        """
        logger.info(f"Starting survey + chat integration for user {user_id}, conversation {conversation_id}")

        try:
            # Step 1: Process survey responses
            from app.modules.question_session.schemas.question_session_request import ParseSurveyResponseRequest
            
            survey_request_obj = ParseSurveyResponseRequest(**survey_request)
            
            # Convert survey to human message
            human_message = await self.survey_processor.format_survey_response_as_human_message(
                request=survey_request_obj,
                user_id=user_id
            )

            # Step 2: Get agent and conversation context
            conversation = self.conversation_dal.get_user_conversation_by_id(conversation_id, user_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            # Get the default agent or specific agent for this conversation
            agent = await self._get_conversation_agent(conversation_id, user_id)
            
            # Step 3: Prepare AI prompt
            ai_prompt = self._prepare_ai_prompt_for_survey(human_message, custom_ai_prompt)

            # Step 4: Get conversation history
            conversation_history = await self._get_conversation_history(conversation_id, user_id)

            # Step 5: Process with AI
            ai_result = await self.langgraph_service.execute_conversation(
                agent=agent,
                conversation_id=conversation_id,
                user_message=ai_prompt,
                conversation_system_prompt=self._get_survey_analysis_system_prompt(),
                conversation_history=conversation_history,
                user_id=user_id
            )

            # Step 6: Format comprehensive response
            result = {
                'survey_data': {
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'survey_answers': survey_request.get('answers', {}),
                    'processed_at': datetime.now().isoformat()
                },
                'human_message': human_message,
                'ai_response': {
                    'content': ai_result.get('content', ''),
                    'metadata': ai_result.get('metadata', {}),
                    'processing_time': ai_result.get('metadata', {}).get('response_time_ms', 0)
                },
                'integration_metadata': {
                    'success': True,
                    'agent_used': agent.name if agent else 'default',
                    'total_processing_time': 0,  # Calculate if needed
                    'human_message_length': len(human_message),
                    'ai_response_length': len(ai_result.get('content', ''))
                }
            }

            logger.info(f"Survey + chat integration completed successfully for conversation {conversation_id}")
            return result

        except Exception as e:
            logger.error(f"Error in survey + chat integration: {e}")
            return {
                'survey_data': survey_request,
                'human_message': None,
                'ai_response': {
                    'content': f"I apologize, but I encountered an error while processing your survey responses: {str(e)}",
                    'metadata': {},
                    'processing_time': 0
                },
                'integration_metadata': {
                    'success': False,
                    'error': str(e),
                    'agent_used': None
                }
            }

    async def _get_conversation_agent(self, conversation_id: str, user_id: str):
        """Get the appropriate agent for the conversation"""
        try:
            # For now, use the system agent as the default
            # In the future, you can add logic to get user-specific agents
            agent = self.agent_repo.get_system_agent()
            return agent

        except Exception as e:
            logger.warning(f"Could not get conversation agent: {e}, using survey analysis agent")
            return self._create_survey_analysis_agent()

    def _create_survey_analysis_agent(self):
        """Create a basic agent for survey analysis"""
        from app.modules.agent.models.agent import Agent
        from app.enums.base_enums import ModelProvider
        
        # Create a simple agent instance for survey processing
        class SurveyAgent:
            def __init__(self):
                self.name = "Survey Analysis Agent"
                self.model_provider = ModelProvider.GEMINI  # or whatever default you prefer
                self.model_name = "gemini-1.5-flash"
                self.default_system_prompt = self._get_survey_analysis_system_prompt()

        return SurveyAgent()

    def _get_survey_analysis_system_prompt(self) -> str:
        """Get system prompt optimized for survey analysis"""
        return """You are an AI assistant specialized in analyzing survey responses and providing insightful feedback.

Your capabilities include:
- Understanding and interpreting survey responses
- Providing thoughtful analysis of user answers
- Offering relevant insights and recommendations
- Maintaining a helpful and empathetic tone

When processing survey responses:
1. Acknowledge the user's effort in completing the survey
2. Provide meaningful analysis of their responses
3. Offer relevant insights or recommendations when appropriate
4. Ask follow-up questions if clarification would be helpful
5. Maintain a professional yet friendly tone

Please respond in Vietnamese if the user's survey responses are in Vietnamese, otherwise respond in English."""

    def _prepare_ai_prompt_for_survey(self, human_message: str, custom_prompt: Optional[str] = None) -> str:
        """Prepare the AI prompt for survey processing"""
        if custom_prompt:
            return f"{custom_prompt}\n\n{human_message}"
        
        default_prompt = """Please analyze my survey responses and provide thoughtful feedback. 
I would appreciate insights, recommendations, or any relevant observations based on my answers.

"""
        return default_prompt + human_message

    async def _get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        try:
            # This is a placeholder - implement based on your conversation message structure
            # You'll need to adapt this to your actual message model/table
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []

    async def send_survey_response_to_chat(
        self,
        survey_response_text: str,
        conversation_id: str,
        user_id: str,
        websocket_connection=None
    ) -> Dict[str, Any]:
        """
        Send processed survey response to chat as a human message
        
        Args:
            survey_response_text: Formatted survey response text
            conversation_id: Conversation ID
            user_id: User ID
            websocket_connection: Optional WebSocket connection for real-time updates

        Returns:
            Result of chat processing
        """
        logger.info(f"Sending survey response to chat for conversation {conversation_id}")

        try:
            # Send via WebSocket if available
            if websocket_connection and hasattr(websocket_connection, 'send_json'):
                message_data = {
                    'type': 'human_message',
                    'content': survey_response_text,
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'source': 'survey_response',
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket_connection.send_json(message_data)
                logger.info(f"Survey response sent via WebSocket for conversation {conversation_id}")

            # Return success response
            return {
                'success': True,
                'conversation_id': conversation_id,
                'message_sent': True,
                'message_length': len(survey_response_text),
                'sent_via_websocket': websocket_connection is not None,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error sending survey response to chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'conversation_id': conversation_id,
                'message_sent': False
            }
