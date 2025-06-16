from typing import Annotated, Dict, List, Optional, TypedDict, Literal
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

# --- LLM Chunking Models ---


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


# --- Individual Data Item Models for CV Sections ---


class PersonalInfoItem(BaseModel):
	"""Represents extracted personal information from the CV."""

	full_name: Optional[str] = Field(None, description='Full name of the candidate.')
	email: Optional[str] = Field(None, description='Email address.')
	phone_number: Optional[str] = Field(None, description='Contact phone number.')
	linkedin_url: Optional[str] = Field(None, description='URL to LinkedIn profile.')
	github_url: Optional[str] = Field(None, description='URL to GitHub profile.')
	portfolio_url: Optional[str] = Field(None, description='URL to personal portfolio or website.')
	other_url: Optional[List[str]] = Field(
		default_factory=list,
		description='List of other relevant URLs (e.g., personal blog).',
	)
	address: Optional[str] = Field(None, description='Physical address or location (city, country).')
	# other_contact_info: Optional[Dict[str, str]] = Field(default_factory=dict, description="Other contact details, e.g., Skype, Twitter.")


class EducationItem(BaseModel):
	"""Represents an educational qualification extracted from the CV."""

	institution_name: str = Field(..., description='Name of the educational institution.')
	degree_name: Optional[str] = Field(None, description='Degree obtained (e.g., Bachelor of Science, Master of Arts).')
	major: Optional[str] = Field(None, description='Major or field of study.')
	graduation_date: Optional[str] = Field(
		None,
		description='Date of graduation or expected graduation (e.g., YYYY-MM, YYYY).',
	)
	gpa: Optional[str] = Field(
		None,
		description='Grade Point Average or academic score (as string for flexibility).',
	)
	relevant_courses: Optional[List[str]] = Field(default_factory=list, description='List of relevant courses taken.')
	description: Optional[str] = Field(
		None,
		description='Additional details, honors, thesis information, or activities.',
	)


class ListEducationItem(BaseModel):
	items: List[EducationItem] = Field(default_factory=list)


class WorkExperienceItem(BaseModel):
	"""Represents a work experience entry extracted from the CV."""

	company_name: str = Field(..., description='Name of the company or organization.')
	job_title: str = Field(..., description='Position or job title held.')
	start_date: Optional[str] = Field(None, description='Start date of employment (e.g., YYYY-MM).')
	end_date: Optional[str] = Field(None, description="End date of employment (e.g., YYYY-MM, or 'Present').")
	duration: Optional[str] = Field(None, description='Calculated or stated duration of employment.')
	responsibilities_achievements: Optional[List[str]] = Field(
		default_factory=list,
		description='Key responsibilities, accomplishments, and projects.',
	)
	location: Optional[str] = Field(None, description='Location of the employment (city, country).')
	# technologies_used: Optional[List[str]] = Field(default_factory=list, description="Technologies or tools used in this role.")


class ListWorkExperienceItem(BaseModel):
	items: List[WorkExperienceItem] = Field(default_factory=list)


class SkillItem(BaseModel):
	"""Represents a skill extracted from the CV."""

	skill_name: str = Field(..., description='Name of the skill (e.g., Python, Project Management).')
	proficiency_level: Optional[str] = Field(
		None,
		description='Proficiency level (e.g., Beginner, Intermediate, Advanced, Expert).',
	)
	category: Optional[str] = Field(
		None,
		description='Category of the skill (e.g., Programming Language, Software, Soft Skill, Framework).',
	)
	# years_of_experience: Optional[int] = Field(None, description="Years of experience with the skill.")


class ListSkillItem(BaseModel):
	items: List[SkillItem] = Field(default_factory=list)


class ProjectItem(BaseModel):
	"""Represents a project extracted from the CV."""

	project_name: str = Field(..., description='Name or title of the project.')
	description: Optional[str] = Field(
		None,
		description='Detailed description of the project, its purpose, and outcomes.',
	)
	technologies_used: Optional[List[str]] = Field(
		default_factory=list,
		description='List of technologies, tools, or programming languages used.',
	)
	role: Optional[str] = Field(None, description='Your role or contribution to the project.')
	project_url: Optional[str] = Field(
		None,
		description='URL to the project (e.g., GitHub repository, live demo, publication).',
	)
	start_date: Optional[str] = Field(None, description='Start date of the project.')
	end_date: Optional[str] = Field(None, description="End date of the project or if it's ongoing.")


class ListProjectItem(BaseModel):
	items: List[ProjectItem] = Field(default_factory=list)


class CertificateItem(BaseModel):
	"""Represents a certification or course extracted from the CV."""

	certificate_name: str = Field(..., description='Name of the certificate or course.')
	issuing_organization: Optional[str] = Field(None, description='Organization that issued the certificate.')
	issue_date: Optional[str] = Field(None, description='Date the certificate was issued (e.g., YYYY-MM).')
	expiration_date: Optional[str] = Field(None, description='Expiration date, if applicable (e.g., YYYY-MM).')
	credential_id: Optional[str] = Field(None, description='Credential ID or link for verification.')


class ListCertificateItem(BaseModel):
	items: List[CertificateItem] = Field(default_factory=list)


class InterestItem(BaseModel):
	"""Represents an interest or hobby extracted from the CV."""

	interest_name: str = Field(..., description='Name of the interest or hobby.')
	description: Optional[str] = Field(None, description='Brief description or details about the interest.')


class ListInterestItem(BaseModel):
	items: List[InterestItem] = Field(default_factory=list)


class KeywordItem(BaseModel):
	"""Represents a single keyword extracted from the CV."""

	keyword: str = Field(..., description='An extracted keyword or key phrase.')


class ListKeywordItem(BaseModel):
	"""Represents a list of extracted keywords."""

	items: List[KeywordItem] = Field(default_factory=list, description='A list of keywords.')


# --- Inferred Data Models ---


class InferredCharacteristicItem(BaseModel):
	"""Represents an inferred characteristic about the candidate based on the CV."""

	characteristic_type: str = Field(
		...,
		description='Type of characteristic (e.g., Potential Role, Key Strength, Soft Skill, Technical Expertise, Area for Development).',
	)
	statement: str = Field(..., description='The inferred statement or insight about the candidate.')
	evidence: Optional[List[str]] = Field(
		default_factory=list,
		description='Snippets or points from the CV that support this inference.',
	)


class ListInferredItem(BaseModel):
	items: List[InferredCharacteristicItem] = Field(default_factory=list)


# --- CV Analysis Result Model (for final output) ---


class CVAnalysisResult(BaseModel):
	"""
	Comprehensive result of the CV analysis, aggregating all extracted and inferred information.
	This model is intended to be the final output returned to the user or calling service.
	"""

	raw_cv_content: Optional[str] = Field(None, description='The original CV content provided by the user.')
	processed_cv_text: Optional[str] = Field(
		None,
		description='The cleaned and structured text version of the CV used for analysis.',
	)

	identified_sections: List[str] = Field(
		default_factory=list,
		description="List of section titles identified in the CV (e.g., 'Education', 'Work Experience').",
	)

	personal_information: Optional[PersonalInfoItem] = Field(None, description='Extracted personal and contact details.')
	education_history: Optional[ListEducationItem] = Field(
		default_factory=ListEducationItem,
		description='List of extracted educational qualifications.',
	)
	work_experience_history: Optional[ListWorkExperienceItem] = Field(
		default_factory=ListWorkExperienceItem,
		description='List of extracted work experiences.',
	)
	skills_summary: Optional[ListSkillItem] = Field(default_factory=ListSkillItem, description='List of extracted skills.')
	projects_showcase: Optional[ListProjectItem] = Field(
		default_factory=ListProjectItem,
		description='List of extracted personal or academic projects.',
	)
	certificates_and_courses: Optional[ListCertificateItem] = Field(
		default_factory=ListCertificateItem,
		description='List of extracted certifications and courses.',
	)
	interests_and_hobbies: Optional[ListInterestItem] = Field(
		default_factory=ListInterestItem,
		description='List of extracted interests and hobbies.',
	)

	# For any other sections not explicitly modeled above
	# Key: section title (string), Value: list of extracted text blocks
	other_sections_data: Dict[str, List[str]] = Field(
		default_factory=dict,
		description='Data from other identified CV sections not fitting standard categories, stored as raw text blocks per section.',
	)

	cv_summary: Optional[str] = Field(None, description='A brief, LLM-generated summary of the entire CV.')
	extracted_keywords: Optional[ListKeywordItem] = Field(
		default_factory=ListKeywordItem,
		description='List of general keywords extracted from the CV content.',
	)

	inferred_characteristics: Optional[ListInferredItem] = Field(
		default_factory=ListInferredItem,
		description='Inferred characteristics, potential roles, strengths, and insights about the candidate.',
	)

	llm_token_usage: Optional[Dict] = Field(
		None,
		description="Information about the number of tokens used during LLM processing (e.g., {'input_tokens': 500, 'output_tokens': 1500, 'total_tokens': 2000}).",
	)

	class Config:
		title = 'CVAnalysisResult'


# --- LangGraph State Definition ---


class CVState(TypedDict):
	"""
	Defines the state for the CV Analysis LangGraph Agent workflow.
	This state is passed between nodes in the graph, accumulating information
	as the CV is processed.
	"""

	# Core LangGraph message list, can be used for agent's internal monologue or conversational history
	messages: Annotated[List, add_messages]

	# Input and processed CV data
	raw_cv_content: Optional[str]  # Initial input from user/service (Output of InputHandlerNode to ParserNode)
	processed_cv_text: Optional[str]  # Cleaned CV text (Output of ParserNode)

	# Section identification
	identified_sections: Optional[List[str]]  # List of section names (Output of SectionIdentifierNode)

	# LLM-based chunking result (Output of LLMChunkDecisionNode)
	chunking_result: Optional[LLMChunkingResult]

	# Extracted structured data items (Populated by InformationExtractorNode)
	# These fields will hold instances of the Pydantic wrapper models (e.g., ListEducationItem) or singular item models.
	personal_info_item: Optional[PersonalInfoItem]
	education_items: Optional[ListEducationItem]  # Changed from List[EducationItem]
	work_experience_items: Optional[ListWorkExperienceItem]  # Changed from List[WorkExperienceItem]
	skill_items: Optional[ListSkillItem]  # Changed from List[SkillItem]
	project_items: Optional[ListProjectItem]  # Changed from List[ProjectItem]
	certificate_items: Optional[ListCertificateItem]  # Changed from List[CertificateItem]
	interest_items: Optional[ListInterestItem]  # Changed from List[InterestItem]

	# For dynamically identified sections not fitting the predefined models
	# Key: section title, Value: list of raw text blocks from that section
	other_extracted_data: Optional[Dict[str, List[str]]]

	# General extractions (Populated by InformationExtractorNode)
	extracted_keywords: Optional[ListKeywordItem]  # Changed from List[str]
	cv_summary: Optional[str]  # LLM-generated summary of the CV

	# Inferences (Populated by CharacteristicInferenceNode)
	# This field will hold an instance of ListInferredItem.
	inferred_characteristics: Optional[ListInferredItem]  # Changed from List[InferredCharacteristicItem]

	# LLM usage tracking (Updated throughout the graph by various nodes)
	token_usage: Optional[Dict[str, int]]

	# Final aggregated result (Populated by OutputAggregatorNode)
	# This field will hold the comprehensive CVAnalysisResult object.
	final_analysis_result: Optional[CVAnalysisResult]
