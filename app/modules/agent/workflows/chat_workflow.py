"""
Simplified chat workflow implementation.
Most functionality moved to LangGraphService for conversation-based processing.
"""
from typing import Dict, Any, AsyncGenerator
from app.modules.agent.workflows.base_workflow import BaseWorkflow


class ChatWorkflow(BaseWorkflow):
    """Simplified chat workflow - delegates to LangGraphService"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chat workflow - delegates to conversation workflow repo"""
        # This is now handled by ConversationWorkflowRepo
        raise NotImplementedError("Use ConversationWorkflowRepo.execute_chat_workflow instead")

    async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming chat workflow - delegates to conversation workflow repo"""
        # This is now handled by ConversationWorkflowRepo
        raise NotImplementedError("Use ConversationWorkflowRepo.execute_streaming_chat_workflow instead")
        yield  # Required for generator function
