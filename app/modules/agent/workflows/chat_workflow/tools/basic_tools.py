"""
Simple calculation tools for basic workflow
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool(return_direct=False)
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@tool(return_direct=False)
def subtract(a: float, b: float) -> float:
    """Subtract second number from first number."""
    return a - b


@tool(return_direct=False)
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


@tool(return_direct=False)
def divide(a: float, b: float) -> float:
    """Divide first number by second number."""
    if b == 0:
        return float("inf")
    return a / b


# List of available tools
tools = [
    add,
    subtract,
    multiply,
    divide,
]


def get_tools(config: Dict[str, Any] = None) -> List:
    """Get tools for the workflow"""
    return tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
    """Get tool definitions for model binding"""
    # Return tool schema for model binding
    return [tool for tool in tools]
