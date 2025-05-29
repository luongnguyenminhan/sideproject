from pydantic import ConfigDict
from app.core.base_model import ResponseSchema
from typing import Dict, Any


class SendMessageResponse(ResponseSchema):
    """Response schema for sending chat messages"""

    model_config = ConfigDict(from_attributes=True)

    user_message: Dict[str, Any]
    ai_message: Dict[str, Any]
