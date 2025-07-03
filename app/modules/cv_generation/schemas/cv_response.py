from app.core.base_model import ResponseSchema, APIResponse, PaginatedResponse
from pydantic import Field, ConfigDict


class CVGenerationResponse(ResponseSchema):
	resume_title: str = Field(..., title='Resume Title', description='The title of the CV')
	generated_sections: list[dict] = Field(..., title='Generated Sections', description='The individual sections of the CV')
	generation_time: str = Field(..., title='Generation Time', description='The timestamp when the CV was generated.')
	cv_id: str = Field(..., title='CV ID', description='A unique identifier for the CV')

	model_config = ConfigDict(from_attributes=True)


class CVGenerationListResponse(APIResponse):
	items: list[CVGenerationResponse]

	class Config:
		schema_extra = {'example': {'error_code': 0, 'message': 'success', 'data': {'items': [{'resume_title': "John Doe's Resume", 'generated_sections': [{'title': 'Education', 'content': 'Bachelor of Science in Computer Science from XYZ University (2020-2024)'}, {'title': 'Experience', 'content': 'Software Developer at ABC Corp (2022-Present)'}], 'generation_time': '2025-01-01T10:00:00Z', 'cv_id': '567e4567-e89b-12d3-a456-426614174001'}], 'more_items_available': False}}}
