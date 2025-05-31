"""
Analysis workflow - simplified or deprecated.
Analysis capabilities are now handled through conversation-specific system prompts.
"""
from typing import Dict, Any, AsyncGenerator
from app.modules.agent.workflows.base_workflow import BaseWorkflow


class AnalysisWorkflow(BaseWorkflow):
    """Analysis workflow - use conversation system prompts instead"""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deprecated - use conversation with analysis-focused system prompt"""
        raise NotImplementedError("Use conversation system prompt for analysis instead")

    async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Deprecated - use conversation with analysis-focused system prompt"""
        raise NotImplementedError("Use conversation system prompt for analysis instead")
        yield
