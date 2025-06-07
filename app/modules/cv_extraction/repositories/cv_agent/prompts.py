"""
This module contains prompts for the CV Analysis LangGraph Agent.
"""

# --- CVParserNode Prompts ---
CV_CLEANING_PROMPT = """
Please clean and structure the following CV content.
Ensure the text is well-formatted, correcting any obvious OCR errors or formatting issues.
Convert any Markdown-like syntax to plain text if necessary for easier parsing by subsequent steps, but preserve the inherent structure (like lists, paragraphs).
The goal is to have a clean, readable text version of the CV.

CV Content:
{raw_cv_content}
"""

# --- SectionIdentifierNode Prompts ---
SECTION_IDENTIFICATION_PROMPT = """
Analyze the following processed CV text and identify the main sections.
Return a list of section titles found in the CV.
Examples of common section titles include: Personal Information, Contact, Summary, Objective, Education, Work Experience, Experience, Skills, Projects, Certifications, Awards, Publications, References, Interests, Hobbies.
Be flexible with naming variations.

Processed CV Text:
{processed_cv_text}

Identified Sections (should be a list of strings):
"""

# --- InformationExtractorNode Prompts ---
# Generic prompt part, to be combined with specific schema instructions
GENERAL_EXTRACTION_SYSTEM_PROMPT = """
You are an expert CV information extractor. Your task is to extract specific information from the provided CV text or a section of it,
and structure it according to the provided Pydantic schema.
Only extract information explicitly present in the text. Do not infer or add information not found.
If a field is optional and the information is not present, omit it or set it to null/None as appropriate for the schema.
For lists of items (like multiple education entries or jobs), ensure each item is a distinct object within the list.
"""

# Specific instructions will be dynamically added when calling with_structured_output,
# but we can define templates for how to ask for extraction for a given section.

EXTRACT_SECTION_PROMPT_TEMPLATE = """
From the following CV text, please extract all information relevant to the '{section_title}' section.
Pay close attention to the schema provided for structuring the output.

CV Text (or relevant portion):
{cv_text_portion}
"""

EXTRACT_KEYWORDS_PROMPT = """
Based on the entire processed CV text provided below, extract a list of relevant keywords.
These keywords should represent the key skills, technologies, roles, and concepts mentioned in the CV.
Return a list of strings.

Processed CV Text:
{processed_cv_text}
"""

CV_SUMMARY_PROMPT = """
Based on the entire processed CV text provided below, generate a concise professional summary of the candidate.
This summary should highlight the candidate's key experiences, skills, and career objectives if apparent.
Aim for 3-5 sentences.

Processed CV Text:
{processed_cv_text}
"""

# --- CharacteristicInferenceNode Prompts ---
INFERENCE_SYSTEM_PROMPT = """
You are an expert career analyst. Based on the structured information extracted from the CV,
your task is to infer characteristics about the candidate.
These characteristics can include potential job roles, key strengths, notable soft skills, technical expertise,
and potential areas for development if evident from the CV.
For each inferred characteristic, provide a statement and, if possible, list evidence or snippets from the CV that support your inference.
Structure your output according to the provided schema.
"""

INFERENCE_PROMPT = """
Here is the structured data extracted from the CV:

Personal Information: {personal_info}
Education History: {education_history}
Work Experience: {work_experience}
Skills: {skills}
Projects: {projects}
Certificates: {certificates}
Interests: {interests}
Other Sections: {other_sections_data}
CV Summary: {cv_summary}
Keywords: {extracted_keywords}

Based on all this information, please infer characteristics about the candidate as per the system prompt and the required output schema.
"""
