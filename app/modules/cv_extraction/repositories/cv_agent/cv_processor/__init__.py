import logging
import uuid
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from typing import Literal

from app.modules.cv_extraction.repositories.cv_agent.agent_schema import (
	CVState,
	ListInferredItem,
	PersonalInfoItem,
	CVAnalysisResult,
	ListEducationItem,  # Added import
	ListWorkExperienceItem,  # Added import
	ListSkillItem,  # Added import
	ListProjectItem,  # Added import
	ListCertificateItem,  # Added import
	ListInterestItem,  # Added import
	ListKeywordItem,  # Added import
)
from app.modules.cv_extraction.repositories.cv_agent.llm_setup import initialize_llm
from app.modules.cv_extraction.repositories.cv_agent.prompts import (
	CV_CLEANING_PROMPT,
	SECTION_IDENTIFICATION_PROMPT,
	GENERAL_EXTRACTION_SYSTEM_PROMPT,
	EXTRACT_SECTION_PROMPT_TEMPLATE,
	EXTRACT_KEYWORDS_PROMPT,
	CV_SUMMARY_PROMPT,
	INFERENCE_SYSTEM_PROMPT,
	INFERENCE_PROMPT,
)
from app.modules.cv_extraction.repositories.cv_agent.utils import (
	TokenTracker,
	count_tokens,
	calculate_price,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


# Schemas for LLM-based CV Chunking and Classification
class CVChunkWithSection(BaseModel):
	"""A chunk of CV content with its classified section type."""

	chunk_content: str = Field(description='The actual text content of this chunk')
	section: Literal[
		'personal_info',
		'education',
		'work_experience',
		'skills',
		'projects',
		'certificates',
		'interests',
		'other',
	] = Field(description='Section type determined by LLM during chunking')


class LLMChunkingResult(BaseModel):
	"""Result of LLM-based intelligent chunking and classification."""

	chunks: List[CVChunkWithSection] = Field(description='List of intelligently chunked and classified CV sections')


class CVProcessorWorkflow:
	"""
	Manages the LangGraph workflow for CV analysis, including node definitions
	and graph construction based on the PlantUML diagram.
	"""

	def __init__(self, api_key: str):
		self.logger = logging.getLogger(self.__class__.__name__)
		self.llm = initialize_llm(api_key)
		self.token_tracker = TokenTracker()
		self.memory = MemorySaver()  # In-memory checkpointer for state
		self.workflow = self._build_graph()

	# --- Node Definitions ---

	async def input_handler_node(self, state: CVState) -> Dict[str, Any]:
		"""Handles initial input and starts the process."""
		print('InputHandlerNode: Starting CV analysis.')
		# raw_cv_content is expected to be in the initial state
		if not state.get('raw_cv_content'):
			print('InputHandlerNode: No raw_cv_content provided.')
			# Potentially raise an error or set a flag
			return {'raw_cv_content': ''}  # Ensure it's not None for next steps
		return {
			'raw_cv_content': state['raw_cv_content'],
			'messages': [SystemMessage(content='CV analysis process started.')],
		}

	async def cv_parser_node(self, state: CVState) -> Dict[str, Any]:
		"""Cleans and structures the raw CV content."""
		print('CVParserNode: Parsing and cleaning CV content.')
		raw_cv_content = state.get('raw_cv_content', '')

		prompt = CV_CLEANING_PROMPT.format(raw_cv_content=raw_cv_content)
		input_tokens = count_tokens(prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		response = await self.llm.ainvoke(prompt)
		processed_cv_text = response.content

		output_tokens = count_tokens(processed_cv_text, 'gemini')
		self.token_tracker.add_output_tokens(output_tokens)

		print(f'CVParserNode: CV content cleaned. Length: {len(processed_cv_text)}')
		return {
			'processed_cv_text': processed_cv_text,
			'messages': state.get('messages', []) + [AIMessage(content=f'CV parsed. Cleaned text length: {len(processed_cv_text)}')],
		}

	async def section_identifier_node(self, state: CVState) -> Dict[str, Any]:
		"""Identifies sections within the processed CV text."""
		print('SectionIdentifierNode: Identifying CV sections.')
		processed_cv_text = state.get('processed_cv_text', '')

		prompt = SECTION_IDENTIFICATION_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens = count_tokens(prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		response = await self.llm.ainvoke(prompt)
		identified_sections_str = response.content
		output_tokens = count_tokens(identified_sections_str, 'gemini')
		self.token_tracker.add_output_tokens(output_tokens)

		identified_sections = []
		try:
			# Attempt to remove markdown code block fences if present
			cleaned_str = identified_sections_str.strip()
			if cleaned_str.startswith('```json'):
				cleaned_str = cleaned_str[len('```json') :]
			if cleaned_str.startswith('```'):  # General markdown fence
				cleaned_str = cleaned_str[len('```') :]
			if cleaned_str.endswith('```'):
				cleaned_str = cleaned_str[: -len('```')]
			cleaned_str = cleaned_str.strip()

			# Parse the cleaned string as JSON
			if cleaned_str.startswith('[') and cleaned_str.endswith(']'):
				# Use json.loads for safety instead of eval
				import json  # Make sure json is imported

				identified_sections = json.loads(cleaned_str)
				if not isinstance(identified_sections, list) or not all(isinstance(s, str) for s in identified_sections):
					print(f'SectionIdentifierNode: Parsed JSON is not a list of strings: {identified_sections}. Falling back.')
					identified_sections = []  # Reset if not a list of strings

			# Fallback for simple comma-separated strings if JSON parsing fails or wasn't appropriate
			if not identified_sections and not (cleaned_str.startswith('[') and cleaned_str.endswith(']')):
				identified_sections = [s.strip() for s in cleaned_str.split(',') if s.strip()]

		except Exception as e:
			print(f"SectionIdentifierNode: Error parsing identified sections string '{identified_sections_str}': {e}. Defaulting to empty list.")
			identified_sections = []  # Ensure it's an empty list on any error

		# Ensure all items are strings, just in case of mixed types from a lenient parse
		identified_sections = [str(s) for s in identified_sections if isinstance(s, (str, int, float))]

		print(f'SectionIdentifierNode: Identified sections: {identified_sections}')
		return {
			'identified_sections': identified_sections,
			'messages': state.get('messages', []) + [AIMessage(content=f'Identified sections: {", ".join(identified_sections)}')],
		}

	async def llm_chunk_decision_node(self, state: CVState) -> Dict[str, Any]:
		"""Uses LLM to intelligently chunk and classify CV content in one step."""
		print('LLMChunkDecisionNode: Starting intelligent CV chunking and classification.')
		processed_cv_text = state.get('processed_cv_text', '')

		print(f'LLMChunkDecisionNode: Received CV text length: {len(processed_cv_text)}')
		print(f'LLMChunkDecisionNode: CV text preview: {processed_cv_text[:500]}...')
		print(f'LLMChunkDecisionNode: State keys: {list(state.keys())}')

		if not processed_cv_text:
			print('LLMChunkDecisionNode: No processed CV text available.')
			return {
				'chunking_result': LLMChunkingResult(chunks=[]),
				'messages': state.get('messages', []) + [AIMessage(content='No CV content to chunk and classify.')],
			}

		# LLM-based intelligent chunking and classification prompt
		chunking_prompt = f"""
You are an expert CV analyzer. Read the following CV content and intelligently divide it into logical chunks, where each chunk represents a coherent section of the CV.

**Section Types Available:**
- personal_info: Personal details, contact information, profile, summary, bio, introduction
- education: Academic background, degrees, schools, universities, qualifications, studies  
- work_experience: Employment history, professional experience, career, jobs, positions
- skills: Technical skills, competencies, abilities, expertise, languages, technologies
- projects: Personal projects, portfolio, case studies, achievements, works
- certificates: Certifications, licenses, courses, training, credentials, workshops
- interests: Hobbies, activities, personal interests, volunteering, recreational activities
- other: Any content that doesn't fit the above categories

**CV Content:**
{processed_cv_text}

**Instructions:**
1. Analyze the content semantically and divide into logical chunks
2. Each chunk should contain related information that belongs to the same section type
3. Don't break up coherent information across multiple chunks
4. Classify each chunk into the most appropriate section type
5. Ensure personal information is captured completely in one chunk
6. Make sure no important information is lost

**Expected Output Format:**
Return a list of chunks where each chunk has:
- chunk_content: The actual text content
- section: The classified section type

Focus on semantic understanding and logical grouping, not keyword matching.
"""

		input_tokens = count_tokens(chunking_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)
		print(f'LLMChunkDecisionNode: Input tokens: {input_tokens}')

		structured_llm = self.llm.with_structured_output(LLMChunkingResult)
		print(f'LLMChunkDecisionNode: Structured LLM created, invoking chunking...')

		try:
			chunking_result = await structured_llm.ainvoke(chunking_prompt)
			print(f'LLMChunkDecisionNode: LLM response received, type: {type(chunking_result)}')
			print(f'LLMChunkDecisionNode: Raw LLM result: {chunking_result}')

			output_tokens = count_tokens(str(chunking_result), 'gemini')
			self.token_tracker.add_output_tokens(output_tokens)
			print(f'LLMChunkDecisionNode: Output tokens: {output_tokens}')

			print(f'LLMChunkDecisionNode: Created {len(chunking_result.chunks)} intelligent chunks.')
			for i, chunk in enumerate(chunking_result.chunks, 1):
				print(f'  - Chunk {i}: {chunk.section} ({len(chunk.chunk_content)} chars)')

			return_data = {
				'chunking_result': chunking_result,
				'messages': state.get('messages', []) + [AIMessage(content=f'Intelligently chunked CV into {len(chunking_result.chunks)} logical sections using LLM analysis.')],
			}
			print(f'LLMChunkDecisionNode: Returning data with chunking_result type: {type(return_data["chunking_result"])}')
			print(f'LLMChunkDecisionNode: Returning chunking_result with {len(return_data["chunking_result"].chunks)} chunks')
			print(f'LLMChunkDecisionNode: Return data keys: {list(return_data.keys())}')
			return return_data

		except Exception as e:
			print(f'LLMChunkDecisionNode: Error during intelligent chunking: {e}')
			print(f'LLMChunkDecisionNode: Exception type: {type(e).__name__}')
			# Fallback to simple chunking
			fallback_chunks = [CVChunkWithSection(chunk_content=processed_cv_text, section='other')]
			fallback_return = {
				'chunking_result': LLMChunkingResult(chunks=fallback_chunks),
				'messages': state.get('messages', []) + [AIMessage(content=f'Error during intelligent chunking: {e}')],
			}
			print(f'LLMChunkDecisionNode: Returning fallback with {len(fallback_return["chunking_result"].chunks)} chunks')
			return fallback_return

	async def _extract_structured_data(self, cv_text_portion: str, schema: type, section_title: str) -> Optional[BaseModel]:  # Changed return type
		"""Helper to extract data for a given schema using with_structured_output."""
		print(f"InformationExtractorNode: Extracting data for section '{section_title}' with schema {schema.__name__}.")

		system_prompt_with_schema = f'{GENERAL_EXTRACTION_SYSTEM_PROMPT}\n\nThe output MUST be structured according to the following Pydantic schema'

		user_prompt = EXTRACT_SECTION_PROMPT_TEMPLATE.format(section_title=section_title, cv_text_portion=cv_text_portion)

		full_prompt_for_tokens = system_prompt_with_schema + '\n' + user_prompt
		input_tokens = count_tokens(full_prompt_for_tokens, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		structured_llm = self.llm.with_structured_output(schema)

		try:
			# Call the LLM to get structured data
			result_from_llm = await structured_llm.ainvoke([
				SystemMessage(content=system_prompt_with_schema),
				HumanMessage(content=user_prompt),
			])

			actual_instance: Optional[BaseModel] = None
			if isinstance(result_from_llm, list) and len(result_from_llm) == 1 and isinstance(result_from_llm[0], schema):
				# If LLM wraps the single instance in a list, unwrap it.
				actual_instance = result_from_llm[0]
				print(f'Unwrapped instance from list for {section_title}')
			elif isinstance(result_from_llm, schema):
				# LLM returned SchemaInstance directly.
				actual_instance = result_from_llm
			else:
				print(f'Unexpected type from LLM for {section_title} (expected {schema.__name__}, got {type(result_from_llm)}). Value: {result_from_llm}')
				return None  # Return None if type is unexpected

			if actual_instance is not None:
				output_tokens = count_tokens(str(actual_instance), 'gemini')  # Calculate tokens based on the actual instance
				self.token_tracker.add_output_tokens(output_tokens)
				print(f"InformationExtractorNode: Successfully extracted data for '{section_title}' using schema {schema.__name__}.")
			return actual_instance  # Return the direct instance or None
		except Exception as e:
			print(
				f"InformationExtractorNode: Error extracting '{section_title}' with schema {schema.__name__}: {e}",
				exc_info=True,
			)
			return None  # Return None on error

	async def information_extractor_node(self, state: CVState) -> Dict[str, Any]:
		"""Extracts detailed information from CV chunks using LLM directly in this node."""
		print(f'InformationExtractorNode: Starting LLM-based information extraction. state: {state.get("chunking_result")}')
		processed_cv_text = state.get('processed_cv_text', '')
		chunking_result = state.get('chunking_result', LLMChunkingResult(chunks=[]))

		print(f'InformationExtractorNode: Processing CV text of length: {len(processed_cv_text)}')
		print(f'InformationExtractorNode: Found {len(chunking_result.chunks)} chunks from chunking')
		print(f'InformationExtractorNode: Chunking result type: {type(chunking_result)}')
		print(f'InformationExtractorNode: Raw chunking result: {chunking_result}')

		# Initialize with default empty wrapper instances
		extracted_data_update = {
			'personal_info_item': None,
			'education_items': ListEducationItem(),
			'work_experience_items': ListWorkExperienceItem(),
			'skill_items': ListSkillItem(),
			'project_items': ListProjectItem(),
			'certificate_items': ListCertificateItem(),
			'interest_items': ListInterestItem(),
			'other_extracted_data': {},
			'extracted_keywords': ListKeywordItem(),  # Initialize with ListKeywordItem
			'cv_summary': '',
		}

		current_messages = state.get('messages', [])

		# Schema mapping for LLM-based extraction
		type_to_schema_map = {
			'personal_info': (PersonalInfoItem, 'personal_info_item'),
			'education': (ListEducationItem, 'education_items'),
			'work_experience': (ListWorkExperienceItem, 'work_experience_items'),
			'skills': (ListSkillItem, 'skill_items'),
			'projects': (ListProjectItem, 'project_items'),
			'certificates': (ListCertificateItem, 'certificate_items'),
			'interests': (ListInterestItem, 'interest_items'),
		}
		print(f'InformationExtractorNode: Schema mapping configured for {len(type_to_schema_map)} section types')

		# Group chunks by section type
		chunks_by_type = {}
		for chunk in chunking_result.chunks:
			section_type = chunk.section
			if section_type not in chunks_by_type:
				chunks_by_type[section_type] = []
			chunks_by_type[section_type].append(chunk)

		print(f'InformationExtractorNode: Grouped chunks by type:')
		for section_type, chunks in chunks_by_type.items():
			print(f'  - {section_type}: {len(chunks)} chunk(s), total chars: {sum(len(c.chunk_content) for c in chunks)}')

		# Process each section type using LLM directly
		for section_type, chunks in chunks_by_type.items():
			print(f"InformationExtractorNode: Processing section type '{section_type}'")

			if section_type in type_to_schema_map:
				schema, state_key = type_to_schema_map[section_type]

				# Combine content from all chunks of this type
				combined_content = '\n\n'.join([chunk.chunk_content for chunk in chunks])

				print(f'InformationExtractorNode: Processing {len(chunks)} chunks as {section_type}')
				print(f'InformationExtractorNode: Combined content length: {len(combined_content)} characters')
				print(f'InformationExtractorNode: Using schema: {schema.__name__} -> state key: {state_key}')

				# Use LLM directly for extraction with structured output
				extraction_prompt = f"""
You are an expert CV data extractor. Extract structured information from the following {section_type} content.

**Content to Extract From:**
{combined_content}

**Instructions:**
1. Extract ALL relevant information from the content
2. Structure the data according to the expected schema
3. Be comprehensive and don't miss any details
4. If information is missing, use null/empty values appropriately
5. Ensure data is clean and properly formatted

Focus on accuracy and completeness of extraction.
"""

				print(f'InformationExtractorNode: Generating extraction prompt for {section_type}')
				input_tokens = count_tokens(extraction_prompt, 'gemini')
				self.token_tracker.add_input_tokens(input_tokens)
				print(f'InformationExtractorNode: Input tokens for {section_type}: {input_tokens}')

				structured_llm = self.llm.with_structured_output(schema)

				try:
					print(f'InformationExtractorNode: Invoking LLM for {section_type} extraction...')
					extracted_items = await structured_llm.ainvoke(extraction_prompt)
					output_tokens = count_tokens(str(extracted_items), 'gemini')
					self.token_tracker.add_output_tokens(output_tokens)

					print(f'InformationExtractorNode: LLM extraction successful for {section_type}')
					print(f'InformationExtractorNode: Output tokens for {section_type}: {output_tokens}')
					print(f'InformationExtractorNode: Extracted items for {section_type}: {extracted_items}')

					if state_key == 'personal_info_item':
						extracted_data_update[state_key] = extracted_items
						print(f'InformationExtractorNode: Set personal info item: {extracted_data_update[state_key]}')
					else:
						# For list types, assign the whole wrapper object
						extracted_data_update[state_key] = extracted_items
						items_count = len(extracted_items.items) if hasattr(extracted_items, 'items') else 0
						print(f'InformationExtractorNode: Set {state_key} with {items_count} items')
						print(f'InformationExtractorNode: {state_key} content: {extracted_data_update[state_key]}')

					current_messages.append(AIMessage(content=f'LLM extracted {section_type} from {len(chunks)} chunks'))
					print(f'InformationExtractorNode: Added success message for {section_type}')

				except Exception as e:
					print(f'InformationExtractorNode: ERROR extracting {section_type}: {e}')
					print(f'InformationExtractorNode: Exception type: {type(e).__name__}')
					current_messages.append(AIMessage(content=f'Error extracting {section_type}: {e}'))

			else:
				print(f"InformationExtractorNode: Section type '{section_type}' not in schema mapping")
				print(f'InformationExtractorNode: Available schema types: {list(type_to_schema_map.keys())}')
				print(f"InformationExtractorNode: Storing '{section_type}' as other data")
				current_messages.append(AIMessage(content=f"Section type '{section_type}' noted as other data."))

		# --- Keyword Extraction ---
		print('InformationExtractorNode: Starting keyword extraction phase')
		keyword_prompt = EXTRACT_KEYWORDS_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_keywords = count_tokens(keyword_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_keywords)
		print(f'InformationExtractorNode: Keyword extraction input tokens: {input_tokens_keywords}')

		structured_llm_keywords = self.llm.with_structured_output(ListKeywordItem)
		try:
			print('InformationExtractorNode: Invoking LLM for keyword extraction...')
			extracted_keyword_items = await structured_llm_keywords.ainvoke(keyword_prompt)

			if isinstance(extracted_keyword_items, ListKeywordItem):
				extracted_data_update['extracted_keywords'] = extracted_keyword_items
				output_tokens_keywords = count_tokens(str(extracted_keyword_items), 'gemini')
				self.token_tracker.add_output_tokens(output_tokens_keywords)
				print(f'InformationExtractorNode: Keyword extraction successful')
				print(f'InformationExtractorNode: Keyword extraction output tokens: {output_tokens_keywords}')
				print(f'InformationExtractorNode: Extracted {len(extracted_keyword_items.items)} keywords: {extracted_keyword_items.items}')
				current_messages.append(AIMessage(content=f'Extracted {len(extracted_keyword_items.items)} keywords.'))
			else:
				print(f'InformationExtractorNode: ERROR - Keyword extraction returned unexpected type: {type(extracted_keyword_items)}')
				print(f'InformationExtractorNode: Expected ListKeywordItem, got: {extracted_keyword_items}')
				current_messages.append(AIMessage(content='Keyword extraction failed to return expected type.'))
		except Exception as e:
			print(f'InformationExtractorNode: ERROR during keyword extraction: {e}')
			print(f'InformationExtractorNode: Keyword extraction exception type: {type(e).__name__}')
			current_messages.append(AIMessage(content=f'Error during keyword extraction: {e}'))

		# --- CV Summary Generation ---
		print('InformationExtractorNode: Starting CV summary generation')
		summary_prompt = CV_SUMMARY_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_sum = count_tokens(summary_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_sum)
		print(f'InformationExtractorNode: Summary generation input tokens: {input_tokens_sum}')

		try:
			print('InformationExtractorNode: Invoking LLM for summary generation...')
			summary_response = await self.llm.ainvoke(summary_prompt)
			extracted_data_update['cv_summary'] = summary_response.content
			output_tokens_sum = count_tokens(extracted_data_update['cv_summary'], 'gemini')
			self.token_tracker.add_output_tokens(output_tokens_sum)
			print(f'InformationExtractorNode: Summary generation successful')
			print(f'InformationExtractorNode: Summary generation output tokens: {output_tokens_sum}')
			print(f'InformationExtractorNode: Generated summary length: {len(extracted_data_update["cv_summary"])} characters')
			print(f'InformationExtractorNode: Summary preview: {extracted_data_update["cv_summary"][:200]}...')
			current_messages.append(AIMessage(content=f'Generated CV summary.'))
		except Exception as e:
			print(f'InformationExtractorNode: ERROR during summary generation: {e}')
			print(f'InformationExtractorNode: Summary generation exception type: {type(e).__name__}')
			extracted_data_update['cv_summary'] = f'Error generating summary: {str(e)}'

		extracted_data_update['messages'] = current_messages

		# Final summary of extraction results
		print('InformationExtractorNode: Information extraction phase complete')
		print(f'InformationExtractorNode: Total tokens used - Input: {self.token_tracker.input_tokens}, Output: {self.token_tracker.output_tokens}')
		print(f'InformationExtractorNode: Extraction results summary:')
		print(f'  - Personal info: {"Set" if extracted_data_update["personal_info_item"] else "Not set"}')
		print(f'  - Education items: {len(extracted_data_update["education_items"].items) if hasattr(extracted_data_update["education_items"], "items") else 0}')
		print(f'  - Work experience items: {len(extracted_data_update["work_experience_items"].items) if hasattr(extracted_data_update["work_experience_items"], "items") else 0}')
		print(f'  - Skill items: {len(extracted_data_update["skill_items"].items) if hasattr(extracted_data_update["skill_items"], "items") else 0}')
		print(f'  - Project items: {len(extracted_data_update["project_items"].items) if hasattr(extracted_data_update["project_items"], "items") else 0}')
		print(f'  - Certificate items: {len(extracted_data_update["certificate_items"].items) if hasattr(extracted_data_update["certificate_items"], "items") else 0}')
		print(f'  - Interest items: {len(extracted_data_update["interest_items"].items) if hasattr(extracted_data_update["interest_items"], "items") else 0}')
		print(f'  - Keywords: {len(extracted_data_update["extracted_keywords"].items) if hasattr(extracted_data_update["extracted_keywords"], "items") else 0}')
		print(f'  - Summary length: {len(extracted_data_update["cv_summary"])} chars')

		return extracted_data_update

	async def characteristic_inference_node(self, state: CVState) -> Dict[str, Any]:
		"""Infers candidate characteristics based on extracted CV data."""
		print('CharacteristicInferenceNode: Inferring characteristics.')

		# Prepare data for the prompt, accessing .items from wrapper types if necessary
		education_history_items = state.get('education_items')
		work_experience_items = state.get('work_experience_items')
		skill_items = state.get('skill_items')
		project_items = state.get('project_items')
		certificate_items = state.get('certificate_items')
		interest_items = state.get('interest_items')

		inference_prompt_filled = INFERENCE_PROMPT.format(
			personal_info=state.get('personal_info_item'),
			education_history=(education_history_items.items if education_history_items else []),
			work_experience=(work_experience_items.items if work_experience_items else []),
			skills=skill_items.items if skill_items else [],
			projects=project_items.items if project_items else [],
			certificates=certificate_items.items if certificate_items else [],
			interests=interest_items.items if interest_items else [],
			other_sections_data=state.get('other_extracted_data'),
			cv_summary=state.get('cv_summary'),
			extracted_keywords=state.get('extracted_keywords'),
		)
		print(f'Filled inference prompt: {inference_prompt_filled}')
		system_prompt_with_schema = f'{INFERENCE_SYSTEM_PROMPT}\n\nThe output MUST be structured according to the following Pydantic schema'

		full_prompt_for_tokens = system_prompt_with_schema + '\n' + inference_prompt_filled
		input_tokens = count_tokens(full_prompt_for_tokens, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens)

		structured_llm = self.llm.with_structured_output(ListInferredItem)
		try:
			inferred_characteristics_response = await structured_llm.ainvoke(  # type: ignore
				[
					SystemMessage(content=system_prompt_with_schema),
					HumanMessage(content=inference_prompt_filled),
				]
			)
			# The response is already ListInferredItem, no need to access .items here for assignment to state
			inferred_characteristics = inferred_characteristics_response
			output_tokens = count_tokens(str(inferred_characteristics_response), 'gemini')  # Count tokens from the response model
			self.token_tracker.add_output_tokens(output_tokens)
			print(f'CharacteristicInferenceNode: Inferred {len(inferred_characteristics.items) if inferred_characteristics else 0} characteristics.')
		except Exception as e:
			print(f'CharacteristicInferenceNode: Error inferring characteristics: {e}')
			inferred_characteristics = []

		return {
			'inferred_characteristics': inferred_characteristics,
			'messages': state.get('messages', []) + [AIMessage(content=f'Inferred {len(inferred_characteristics.items) if inferred_characteristics else 0} characteristics.')],
		}

	async def output_aggregator_node(self, state: CVState) -> Dict[str, Any]:
		"""Aggregates all data into the final CVAnalysisResult model."""
		print('OutputAggregatorNode: Aggregating final results.')

		# Ensure that the state fields are passed directly if they are already the correct wrapper types
		final_result = CVAnalysisResult(
			raw_cv_content=state.get('raw_cv_content'),
			processed_cv_text=state.get('processed_cv_text'),
			identified_sections=state.get('identified_sections', []),
			personal_information=state.get('personal_info_item'),
			education_history=state.get('education_items'),  # Pass the wrapper object directly
			work_experience_history=state.get('work_experience_items'),  # Pass the wrapper object directly
			skills_summary=state.get('skill_items'),  # Pass the wrapper object directly
			projects_showcase=state.get('project_items'),  # Pass the wrapper object directly
			certificates_and_courses=state.get('certificate_items'),  # Pass the wrapper object directly
			interests_and_hobbies=state.get('interest_items'),  # Pass the wrapper object directly
			other_sections_data=state.get('other_extracted_data', {}),
			cv_summary=state.get('cv_summary'),
			extracted_keywords=state.get('extracted_keywords', []),
			inferred_characteristics=state.get('inferred_characteristics'),  # Pass the wrapper object directly
			llm_token_usage={
				'input_tokens': self.token_tracker.input_tokens,
				'output_tokens': self.token_tracker.output_tokens,
				'total_tokens': self.token_tracker.total_tokens,
				'price_usd': round(
					calculate_price(
						self.token_tracker.input_tokens,
						self.token_tracker.output_tokens,
					),
					6,
				),
			},
		)
		print('OutputAggregatorNode: Final result aggregated.')
		return {
			'final_analysis_result': final_result,
			'messages': state.get('messages', []) + [AIMessage(content='CV analysis complete. Final result aggregated.')],
		}

	def _build_graph(self) -> StateGraph:
		"""Constructs the LangGraph StateGraph for CV processing."""
		print('Building CV analysis workflow graph.')
		workflow = StateGraph(CVState)

		# Add nodes based on the PlantUML diagram
		workflow.add_node('InputHandler', self.input_handler_node)
		workflow.add_node('CVParser', self.cv_parser_node)
		workflow.add_node('LLMChunkDecision', self.llm_chunk_decision_node)
		workflow.add_node('InformationExtractor', self.information_extractor_node)
		workflow.add_node('CharacteristicInference', self.characteristic_inference_node)
		workflow.add_node('OutputAggregator', self.output_aggregator_node)

		# Define edges for the workflow
		workflow.add_edge(START, 'InputHandler')
		workflow.add_edge('InputHandler', 'CVParser')
		workflow.add_edge('CVParser', 'LLMChunkDecision')
		workflow.add_edge('LLMChunkDecision', 'InformationExtractor')
		workflow.add_edge('InformationExtractor', 'CharacteristicInference')
		workflow.add_edge('CharacteristicInference', 'OutputAggregator')  # Added edge
		workflow.add_edge('OutputAggregator', END)

		return workflow.compile(checkpointer=self.memory)

	async def analyze_cv(self, cv_content: str) -> Optional[CVAnalysisResult]:
		"""Public method to process a CV and return the analysis result."""
		print(f'Starting CV analysis for content of length: {len(cv_content)}')
		self.token_tracker.reset()

		thread_id = str(uuid.uuid4())
		config = {'configurable': {'thread_id': thread_id}}

		# Initialize state with wrapper types where appropriate
		initial_state_data = {
			'messages': [],
			'raw_cv_content': cv_content,
			'processed_cv_text': None,
			'chunking_result': LLMChunkingResult(chunks=[]),
			'personal_info_item': None,
			'education_items': ListEducationItem(),
			'work_experience_items': ListWorkExperienceItem(),
			'skill_items': ListSkillItem(),
			'project_items': ListProjectItem(),
			'certificate_items': ListCertificateItem(),
			'interest_items': ListInterestItem(),
			'other_extracted_data': None,
			'extracted_keywords': None,
			'cv_summary': None,
			'inferred_characteristics': ListInferredItem(),
			'token_usage': None,
			'final_analysis_result': None,
		}
		initial_state = CVState(**initial_state_data)

		try:
			final_state_result = await self.workflow.ainvoke(initial_state, config=config)
			if final_state_result and 'final_analysis_result' in final_state_result:
				print('CV analysis completed successfully.')
				return final_state_result['final_analysis_result']
			else:
				print('CV analysis finished but no final_analysis_result found in state.')
				return None
		except Exception as e:
			print(f'Error during CV analysis workflow: {e}')
			error_result = CVAnalysisResult(
				raw_cv_content=cv_content,
				processed_cv_text=initial_state.get('processed_cv_text'),
				cv_summary=f'Error during analysis: {str(e)}',
				llm_token_usage={
					'input_tokens': self.token_tracker.input_tokens,
					'output_tokens': self.token_tracker.output_tokens,
					'total_tokens': self.token_tracker.total_tokens,
					'price_usd': round(
						calculate_price(
							self.token_tracker.input_tokens,
							self.token_tracker.output_tokens,
						),
						6,
					),
				},
			)
			return error_result
