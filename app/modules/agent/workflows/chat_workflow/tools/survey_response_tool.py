"""
Survey Response Workflow Tool
Integration tool for processing survey responses within the agent workflow
"""

import logging
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SurveyResponseInput(BaseModel):
    """Input schema for survey response processing"""
    survey_data: Dict[str, Any] = Field(..., description="Survey response data")
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    processing_type: str = Field(default="analysis", description="Type of processing: analysis, summary, insights")


class SurveyResponseProcessor:
    """Tool for processing survey responses within the workflow"""

    @staticmethod
    def process_survey_response(
        survey_data: Dict[str, Any],
        conversation_id: str,
        user_id: str,
        processing_type: str = "analysis"
    ) -> str:
        """
        Process survey response and return formatted text for AI analysis
        
        Args:
            survey_data: Survey response data
            conversation_id: Conversation ID
            user_id: User ID
            processing_type: Type of processing requested
            
        Returns:
            Formatted text ready for AI processing
        """
        logger.info(f"Processing survey response for conversation {conversation_id}")
        
        try:
            # Extract answers from survey data
            answers = survey_data.get('answers', {})
            
            if not answers:
                return "No survey responses were provided to analyze."
            
            # Format the survey response
            formatted_response = SurveyResponseProcessor._format_survey_for_ai(
                answers=answers,
                processing_type=processing_type,
                conversation_id=conversation_id
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error processing survey response: {e}")
            return f"Error processing survey response: {str(e)}"

    @staticmethod
    def _format_survey_for_ai(
        answers: Dict[str, Any],
        processing_type: str,
        conversation_id: str
    ) -> str:
        """Format survey answers for AI analysis"""
        
        # Create the appropriate prompt based on processing type
        if processing_type == "summary":
            intro = "Please provide a concise summary of the following survey responses:"
        elif processing_type == "insights":
            intro = "Please analyze the following survey responses and provide key insights:"
        else:  # analysis
            intro = "Please analyze the following survey responses and provide detailed feedback:"
        
        # Format the survey data
        formatted_parts = [
            intro,
            "",
            "**Survey Response Details:**",
            f"- Conversation ID: {conversation_id}",
            f"- Total Questions Answered: {len(answers)}",
            f"- Response Date: {SurveyResponseProcessor._get_current_timestamp()}",
            "",
            "**Responses:**"
        ]
        
        # Format each answer
        for question_id, answer_value in answers.items():
            formatted_answer = SurveyResponseProcessor._format_individual_answer(
                question_id, answer_value
            )
            formatted_parts.append(formatted_answer)
            formatted_parts.append("")
        
        # Add analysis instructions
        formatted_parts.extend([
            "---",
            "**Analysis Instructions:**",
            "- Provide thoughtful analysis of the responses",
            "- Identify patterns or themes in the answers", 
            "- Offer relevant insights or recommendations",
            "- Maintain a helpful and empathetic tone",
            "- Ask clarifying questions if needed"
        ])
        
        return "\n".join(formatted_parts)

    @staticmethod
    def _format_individual_answer(question_id: str, answer_value: Any) -> str:
        """Format a single survey answer"""
        try:
            if isinstance(answer_value, dict):
                # Handle complex answers
                if len(answer_value) == 1 and 'value' in answer_value:
                    return f"**Question {question_id}:** {answer_value['value']}"
                else:
                    answer_parts = []
                    for key, value in answer_value.items():
                        answer_parts.append(f"  - {key}: {value}")
                    return f"**Question {question_id}:**\n" + "\n".join(answer_parts)
            
            elif isinstance(answer_value, list):
                # Handle multiple choice
                answer_list = "\n".join(f"  - {item}" for item in answer_value)
                return f"**Question {question_id}:** (Multiple selections)\n{answer_list}"
            
            else:
                # Handle simple answers
                return f"**Question {question_id}:** {answer_value}"
                
        except Exception as e:
            logger.warning(f"Error formatting answer for question {question_id}: {e}")
            return f"**Question {question_id}:** {str(answer_value)}"

    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current timestamp in readable format"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Tool definition for LangGraph integration
def survey_response_tool(input_data: str) -> str:
    """
    Tool function for processing survey responses in LangGraph workflows
    
    Args:
        input_data: JSON string containing survey response data
        
    Returns:
        Formatted text for AI analysis
    """
    try:
        # Parse input data
        data = json.loads(input_data)
        
        # Extract required fields
        survey_data = data.get('survey_data', {})
        conversation_id = data.get('conversation_id', '')
        user_id = data.get('user_id', '')
        processing_type = data.get('processing_type', 'analysis')
        
        # Process the survey response
        result = SurveyResponseProcessor.process_survey_response(
            survey_data=survey_data,
            conversation_id=conversation_id,
            user_id=user_id,
            processing_type=processing_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in survey_response_tool: {e}")
        return f"Error processing survey response: {str(e)}"


# Export for use in workflow tools
__all__ = ['SurveyResponseProcessor', 'survey_response_tool', 'SurveyResponseInput']
