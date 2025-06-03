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
	result = a + b
	logger.info(f'[TOOLS] Adding {a} + {b} = {result}')
	return result


@tool(return_direct=False)
def subtract(a: float, b: float) -> float:
	"""Subtract second number from first number."""
	result = a - b
	logger.info(f'[TOOLS] Subtracting {a} - {b} = {result}')
	return result


@tool(return_direct=False)
def multiply(a: float, b: float) -> float:
	"""Multiply two numbers together."""
	result = a * b
	logger.info(f'[TOOLS] Multiplying {a} * {b} = {result}')
	return result


@tool(return_direct=False)
def divide(a: float, b: float) -> float:
	"""Divide first number by second number."""
	if b == 0:
		return 'Error: Cannot divide by zero'
	result = a / b
	logger.info(f'[TOOLS] Dividing {a} / {b} = {result}')
	return result


# List of available tools
tools = [add, subtract, multiply, divide]


def get_tools(config: Dict[str, Any] = None) -> List:
	"""Get simple calculation tools"""
	return tools


def get_tool_definitions(config: Dict[str, Any] = None) -> List[Dict]:
	"""Get tool definitions for model binding"""
	return []
