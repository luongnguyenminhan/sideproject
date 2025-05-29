from pydantic import Field
from app.core.base_model import RequestSchema
from typing import Optional


class SendMessageRequest(RequestSchema):
    """Request schema for sending chat messages"""

    conversation_id: str = Field(..., description="ID of the conversation")
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Message content"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for AI service (optional)"
    )
