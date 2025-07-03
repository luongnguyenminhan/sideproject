from app.core.base_model import RequestSchema
from pydantic import Field


class CVGenerateRequest(RequestSchema):
	user_id: str = Field(..., title='User ID', description='ID of the user whose CV is being generated.')
	template_id: str = Field(..., title='Template ID', description='The template to use for CV generation.')
	language_code: str = Field(..., title='Language Code', description="Language code for the CV (e.g., 'en', 'vi').")
	education: list[dict] = Field(..., title='Education Sections', description='List of dictionaries with education details.')
	experience: list[dict] = Field(..., title='Experience Sections', description='List of dictionaries with work experience details.')
	skills: list[str] = Field(..., title='Skills', description='List of skills to include in the CV.')
	certifications: list[dict] = Field(..., title='Certifications', description='List of dictionaries with certification details.')
	projects: list[dict] = Field(..., title='Projects', description='List of dictionaries with project details.')

	class Config:
		schema_extra = {
			'example': {
				'user_id': '123e4567-e89b-12d3-a456-426614174000',
				'template_id': 'standard_cv',
				'language_code': 'en',
				'education': [{'institution': 'University of Example', 'degree': 'Bachelor of Science', 'field_of_study': 'Computer Science', 'start_date': '2020-09-01', 'end_date': '2024-05-31'}],
				'experience': [
					{
						'position': 'Software Developer Intern',
						'company': 'Tech Innovations',
						'location': 'Ho Chi Minh City, Vietnam',
						'start_date': '2023-07-01',
						'end_date': '2023-12-31',
						'responsibilities': 'Developed backend APIs using FastAPI and Python. Worked on improving codebase efficiency and scalability.',
					}
				],
				'skills': ['Python', 'FastAPI', 'SQLAlchemy', 'React', 'Team Collaboration'],
				'certifications': [{'name': 'AWS Certified Developer', 'issuing_organization': 'Amazon Web Services', 'date_issued': '2023-05-01'}],
				'projects': [{'name': 'Opensource AI project', 'description': 'Contribution to an open source AI project', 'date_completed': '2024-04-01', 'responsibilities': 'Contributed to the project by implementing API endpoints and refactoring code.'}],
			}
		}
