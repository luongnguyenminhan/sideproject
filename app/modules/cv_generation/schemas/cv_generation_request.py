from typing import Optional, List
from pydantic import BaseModel, Field
from app.core.base_model import RequestSchema
from app.modules.cv_extraction.schemas.cv import ProcessCVResponse


class CVGenerationRequest(RequestSchema):
	"""Request schema cho CV generation"""

	cv_data: ProcessCVResponse = Field(description='CV data từ extraction module')
	template_type: Optional[str] = Field(default='modern', description='Loại template: modern, classic, creative')
	custom_prompt: Optional[str] = Field(default=None, description='Custom prompt cho AI')
	output_format: Optional[str] = Field(default='pdf', description='Format output: pdf, latex')
	include_photo: Optional[bool] = Field(default=False, description='Có bao gồm photo không')
	color_theme: Optional[str] = Field(default='blue', description='Màu theme: blue, green, red, black')


class CVTemplateCustomizationRequest(RequestSchema):
	"""Request schema cho custom template"""

	cv_data: ProcessCVResponse = Field(description='CV data từ extraction module')
	customization_requirements: str = Field(description='Yêu cầu customize template')
	base_template: Optional[str] = Field(default='modern', description='Base template')


class CVPreviewRequest(RequestSchema):
	"""Request schema cho preview CV"""

	cv_data: ProcessCVResponse = Field(description='CV data từ extraction module')
	template_type: str = Field(description='Loại template')
	preview_format: Optional[str] = Field(default='html', description='Format preview: html, png')


class CVBatchGenerationRequest(RequestSchema):
	"""Request schema cho batch generation"""

	cv_data_list: List[ProcessCVResponse] = Field(description='List CV data')
	template_type: str = Field(description='Loại template')
	output_format: Optional[str] = Field(default='pdf', description='Format output')
