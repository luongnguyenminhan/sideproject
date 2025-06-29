"""
Enhanced Chat Workflow for EnterViu AI Assistant

REFACTORED VERSION - This file now imports from modular components.

The original large workflow.py has been split into:
- workflow/main.py: Main Workflow class
- workflow/nodes.py: All node functions
- workflow/routing.py: Routing logic
- workflow/workflow_builder.py: Graph construction
- workflow/prompts.py: System prompts and schemas

This maintains backward compatibility while providing better maintainability.
"""

# Import the refactored Workflow class and factory function
from .workflow.main import Workflow, create_workflow

# Import additional components for backwards compatibility
from .workflow.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    TOOL_DECISION_SYSTEM_PROMPT,
    ToolDecision,
)
from .workflow.nodes import WorkflowNodes
from .workflow.routing import WorkflowRouter
from .workflow.workflow_builder import WorkflowBuilder

# Maintain backward compatibility by exposing the same interface
__all__ = [
    "Workflow",
    "create_workflow",
    "DEFAULT_SYSTEM_PROMPT",
    "TOOL_DECISION_SYSTEM_PROMPT",
    "ToolDecision",
    "WorkflowNodes",
    "WorkflowRouter",
    "WorkflowBuilder",
]


# Legacy class alias for backward compatibility
class EnhancedWorkflow(Workflow):
    """Legacy alias for the refactored Workflow class"""

    pass
