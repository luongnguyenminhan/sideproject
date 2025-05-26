"""Conversation summary schemas"""

from pydantic import BaseModel, Field


class ConversationSummaryRequest(BaseModel):
	"""Request model for conversation summary"""

	prompt: str = Field(..., description='Conversation transcript to summarize')
	email: str | None = Field(None, description='Optional email to send the summary to')

	class Config:
		json_schema_extra = {'example': {'prompt': "John: Hi team, let's discuss our project timeline...", 'email': 'user@example.com'}}
