import json
import re
from typing import Dict

import tiktoken


## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.config import (
	CONTEXT_PRICE_PER_MILLION,
	INPUT_PRICE_PER_MILLION,
	OUTPUT_PRICE_PER_MILLION,
)


def calculate_price(input_tokens: int, output_tokens: int, context_tokens: int = 0) -> float:
	"""Calculate total price based on token usage.

	Args:
	    input_tokens (int): Number of input tokens
	    output_tokens (int): Number of output tokens
	    context_tokens (int): Number of context tokens

	Returns:
	    float: Total price in USD
	"""
	input_price = (input_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION
	output_price = (output_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
	context_price = (context_tokens / 1_000_000) * CONTEXT_PRICE_PER_MILLION
	return input_price + output_price + context_price


def parse_json_from_response(response: str) -> Dict:
	"""_summary_

	Args:
	    response (str): _description_

	Returns:
	    Dict: _description_
	"""

	try:
		parsed_response = json.loads(response)
	except json.JSONDecodeError:
		try:
			new_response = response.split('```')[1][5:]
			parsed_response = json.loads(new_response)
		except json.JSONDecodeError:
			pattern = r'(json)\s*({.*})'
			match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)

			if match:
				parsed_response = json.loads(match.group(2))
			else:
				parsed_response = {}
	return parsed_response


def count_tokens(text: str, model: str = 'gpt-4') -> int:
	"""Count the number of tokens in a text string.

	Args:
	    text (str): The text to count tokens for
	    model (str): The model to use for counting tokens

	Returns:
	    int: Number of tokens
	"""
	if not text:
		return 0

	# Handle Gemini models
	if 'gemini' in model.lower():
		# Gemini approximates tokens as ~4 characters per token
		return len(text) // 4

	# Handle Google/Vertex AI models through LiteLLM
	elif model.lower().startswith(('google/', 'vertex_ai/')):
		# Use same approximation for Google models
		return len(text) // 4

	# Handle OpenAI models with tiktoken
	else:
		try:
			encoding = tiktoken.encoding_for_model(model)
			return len(encoding.encode(text))
		except (KeyError, ValueError, ImportError):
			# Fallback for unknown models
			# Average English text is ~4 chars per token
			return len(text) // 4


class TokenTracker:
	def __init__(self):
		self.input_tokens = 0
		self.output_tokens = 0
		self.context_tokens = 0

	@property
	def total_tokens(self):
		return self.input_tokens + self.output_tokens + self.context_tokens

	def add_input_tokens(self, tokens: int):
		self.input_tokens += tokens

	def add_output_tokens(self, tokens: int):
		self.output_tokens += tokens

	def add_context_tokens(self, tokens: int):
		self.context_tokens += tokens

	def reset(self):
		self.input_tokens = 0
		self.output_tokens = 0
		self.context_tokens = 0
