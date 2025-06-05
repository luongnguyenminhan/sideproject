import logging
import uuid
from typing import Dict, List, Any, Optional
from pydantic import BaseModel  # Added import for BaseModel

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
			print(f"InformationExtractorNode: Error extracting '{section_title}' with schema {schema.__name__}: {e}", exc_info=True)
			return None  # Return None on error

	async def information_extractor_node(self, state: CVState) -> Dict[str, Any]:
		"""Extracts detailed information from CV sections using Pydantic schemas."""
		print('InformationExtractorNode: Starting information extraction.')
		processed_cv_text = state.get('processed_cv_text', '')
		identified_sections = state.get('identified_sections', [])

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
		section_to_schema_map = {
			# Personal information keywords
			('personal information', 'contact', 'about me', 'personal details', 'profile', 'bio', 'introduction', 'summary', 'overview'): (
				PersonalInfoItem,
				'personal_info_item',
			),
			# Education keywords
			('education', 'academic background', 'qualifications', 'academic history', 'studies', 'degrees', 'academic achievements', 'schools', 'university', 'colleges', 'academic qualifications'): (
				ListEducationItem,
				'education_items',
			),
			# Work experience keywords
			(
				'work experience',
				'experience',
				'employment history',
				'professional experience',
				'career history',
				'professional background',
				'job history',
				'work history',
				'positions held',
				'career summary',
				'professional summary',
				'employment',
			): (
				ListWorkExperienceItem,
				'work_experience_items',
			),
			# Skills keywords
			(
				'skills',
				'technical skills',
				'languages',
				'competencies',
				'abilities',
				'expertise',
				'proficiencies',
				'capabilities',
				'core skills',
				'key skills',
				'professional skills',
				'soft skills',
				'hard skills',
				'tech stack',
				'technologies',
			): (
				ListSkillItem,
				'skill_items',
			),
			# Projects keywords
			(
				'projects',
				'personal projects',
				'portfolio',
				'case studies',
				'works',
				'project experience',
				'project history',
				'achievements',
				'key projects',
				'featured projects',
				'research projects',
			): (
				ListProjectItem,
				'project_items',
			),
			# Certifications keywords
			(
				'certifications',
				'courses',
				'licenses',
				'certificates',
				'accreditations',
				'qualifications',
				'professional development',
				'training',
				'workshops',
				'professional certifications',
				'credentials',
			): (
				ListCertificateItem,
				'certificate_items',
			),
			# Interests keywords
			('interests', 'hobbies', 'activities', 'personal interests', 'extracurricular activities', 'volunteering', 'leisure activities', 'passions', 'recreational activities'): (
				ListInterestItem,
				'interest_items',
			),
		}

		current_messages = state.get('messages', [])

		for section_title in identified_sections:
			matched = False
			for keywords, (schema, state_key) in section_to_schema_map.items():
				print(f"Checking section '{section_title}' against keywords: {keywords}")
				if any(keyword in section_title.lower() for keyword in keywords):
					extracted_items = await self._extract_structured_data(processed_cv_text, schema, section_title)
					print(f'Extracted items: {extracted_items}')

					if state_key == 'personal_info_item':
						extracted_data_update[state_key] = extracted_items
						print(f'Extracted personal info: {extracted_data_update[state_key]}')
					else:
						# For list types, assign the whole wrapper object
						extracted_data_update[state_key] = extracted_items
						print(f'Extracted {state_key}: {extracted_data_update[state_key]}')

					current_messages.append(AIMessage(content=f'Extracted items for section: {section_title}'))
					matched = True
					break
			if not matched:
				print(f"InformationExtractorNode: Section '{section_title}' not mapped to a specific schema. Storing as other data.")
				current_messages.append(AIMessage(content=f"Section '{section_title}' noted as other data."))

		# --- Keyword Extraction ---
		print('InformationExtractorNode: Extracting keywords.')
		keyword_prompt = EXTRACT_KEYWORDS_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_keywords = count_tokens(keyword_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_keywords)

		structured_llm_keywords = self.llm.with_structured_output(ListKeywordItem)
		try:
			extracted_keyword_items = await structured_llm_keywords.ainvoke(keyword_prompt)
			if isinstance(extracted_keyword_items, ListKeywordItem):
				extracted_data_update['extracted_keywords'] = extracted_keyword_items
				output_tokens_keywords = count_tokens(str(extracted_keyword_items), 'gemini')
				self.token_tracker.add_output_tokens(output_tokens_keywords)
				print(f'InformationExtractorNode: Extracted keywords: {extracted_keyword_items.items}')
				current_messages.append(AIMessage(content=f'Extracted {len(extracted_keyword_items.items)} keywords.'))
			else:
				print(f'InformationExtractorNode: Keyword extraction did not return ListKeywordItem. Got: {type(extracted_keyword_items)}')
				current_messages.append(AIMessage(content='Keyword extraction failed to return expected type.'))
		except Exception as e:
			print(f'InformationExtractorNode: Error extracting keywords: {e}', exc_info=True)
			current_messages.append(AIMessage(content=f'Error during keyword extraction: {e}'))

		summary_prompt = CV_SUMMARY_PROMPT.format(processed_cv_text=processed_cv_text)
		input_tokens_sum = count_tokens(summary_prompt, 'gemini')
		self.token_tracker.add_input_tokens(input_tokens_sum)
		summary_response = await self.llm.ainvoke(summary_prompt)
		extracted_data_update['cv_summary'] = summary_response.content
		output_tokens_sum = count_tokens(extracted_data_update['cv_summary'], 'gemini')
		self.token_tracker.add_output_tokens(output_tokens_sum)
		current_messages.append(AIMessage(content=f'Generated CV summary.'))

		extracted_data_update['messages'] = current_messages
		print('InformationExtractorNode: Information extraction phase complete.')
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
		workflow.add_node('SectionIdentifier', self.section_identifier_node)
		workflow.add_node('InformationExtractor', self.information_extractor_node)
		workflow.add_node('CharacteristicInference', self.characteristic_inference_node)
		workflow.add_node('OutputAggregator', self.output_aggregator_node)

		# Define edges for the workflow
		workflow.add_edge(START, 'InputHandler')
		workflow.add_edge('InputHandler', 'CVParser')
		workflow.add_edge('CVParser', 'SectionIdentifier')
		workflow.add_edge('SectionIdentifier', 'InformationExtractor')
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
			'identified_sections': None,
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
