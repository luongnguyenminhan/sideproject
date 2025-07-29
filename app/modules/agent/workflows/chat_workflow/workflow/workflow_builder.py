"""
Workflow Builder for Chat Workflow

This module contains the logic for building and configuring
the enhanced chat workflow graph for EnterViu AI Assistant.

Builder Components:
- Graph construction
- Node registration
- Edge configuration
- Workflow compilation
"""

import logging
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from ..state.workflow_state import AgentState
from ..tools.basic_tools import get_tools
from .nodes import WorkflowNodes
from .routing import WorkflowRouter

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Builder class for constructing the enhanced chat workflow"""

    def __init__(self, workflow_instance):
        """Initialize with reference to main workflow instance"""
        self.workflow = workflow_instance
        self.nodes = WorkflowNodes(workflow_instance)
        self.router = WorkflowRouter(workflow_instance)

    def build_workflow(self) -> StateGraph:
        """Build enhanced workflow with business process management and guardrails"""
        logger.info("[WorkflowBuilder] Building enhanced chat workflow")

        # Create workflow graph
        workflow = StateGraph(AgentState)

        # Get tools and store for runtime updates
        tools = get_tools(self.workflow.config)
        self.workflow._tools = tools
        tool_node = ToolNode(tools)  # noqa: F841

        # Register all nodes
        self._register_nodes(workflow)

        # Configure workflow flow
        self._configure_edges(workflow)

        # Set entry point
        workflow.set_entry_point("input_validation")

        # Compile with memory
        checkpointer = MemorySaver()
        compiled_graph = workflow.compile(checkpointer=checkpointer)

        logger.info("[WorkflowBuilder] Workflow compilation completed")
        return compiled_graph

    def _register_nodes(self, workflow: StateGraph) -> None:
        """Register workflow nodes - simplified to always use tools"""
        logger.info("[WorkflowBuilder] Registering simplified nodes")

        # Create wrapper functions to ensure config parameter is properly handled
        async def input_validation_wrapper(state, config):
            return await self.nodes.input_validation_node(state, config)

        async def business_process_analysis_wrapper(state, config):
            return await self.nodes.business_process_analysis_node(state, config)

        async def agent_with_tools_wrapper(state, config):
            return await self.nodes.agent_with_tools_node(state, config)

        async def tools_wrapper(state, config):
            return await self.nodes.tools_node(state, config)

        async def output_validation_wrapper(state, config):
            return await self.nodes.output_validation_node(state, config)

        # Simplified nodes - always use tools
        workflow.add_node("input_validation", input_validation_wrapper)
        workflow.add_node(
            "business_process_analysis", business_process_analysis_wrapper
        )
        workflow.add_node("agent_with_tools", agent_with_tools_wrapper)
        workflow.add_node("tools", tools_wrapper)
        workflow.add_node("output_validation", output_validation_wrapper)

        logger.info("[WorkflowBuilder] All nodes registered successfully")

    def _configure_edges(self, workflow: StateGraph) -> None:
        """Configure workflow edges - simplified flow always using tools"""
        logger.info("[WorkflowBuilder] Configuring simplified workflow edges")

        # Simplified flow: input -> business analysis -> agent with tools -> tools (if needed) -> output
        workflow.add_edge("input_validation", "business_process_analysis")
        workflow.add_edge("business_process_analysis", "agent_with_tools")

        # Route after agent_with_tools (check for tool calls)
        workflow.add_conditional_edges(
            "agent_with_tools",
            self.router.should_continue_after_agent,
            {"tools": "tools", "end": "output_validation"},
        )

        # After tools execution, go to output validation
        workflow.add_edge("tools", "output_validation")

        # End after output validation
        workflow.add_edge("output_validation", END)

        logger.info(
            "[WorkflowBuilder] Simplified workflow edges configured successfully"
        )
