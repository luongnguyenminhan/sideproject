"""
Modular Chat Workflow Package

This package contains the refactored and modularized components
of the enhanced chat workflow for EnterViu AI Assistant.

Modules:
- main.py: Main Workflow class and factory functions
- nodes.py: All workflow node functions
- routing.py: Workflow routing logic
- workflow_builder.py: Workflow graph construction
- prompts.py: System prompts and keyword definitions

Usage:
    from .main import Workflow, create_workflow
    from .nodes import WorkflowNodes
    from .routing import WorkflowRouter
    from .workflow_builder import WorkflowBuilder
    from .prompts import DEFAULT_SYSTEM_PROMPT, TOOL_DECISION_SYSTEM_PROMPT
"""

from .main import Workflow, create_workflow
from .nodes import WorkflowNodes
from .routing import WorkflowRouter
from .workflow_builder import WorkflowBuilder
from .prompts import (
	DEFAULT_SYSTEM_PROMPT,
	TOOL_DECISION_SYSTEM_PROMPT,
	ToolDecision,
	SURVEY_KEYWORDS,
	build_enhanced_system_prompt,
	build_tool_decision_prompt,
)

__all__ = [
	'Workflow',
	'create_workflow',
	'WorkflowNodes',
	'WorkflowRouter',
	'WorkflowBuilder',
	'DEFAULT_SYSTEM_PROMPT',
	'TOOL_DECISION_SYSTEM_PROMPT',
	'ToolDecision',
	'SURVEY_KEYWORDS',
	'build_enhanced_system_prompt',
	'build_tool_decision_prompt',
]
