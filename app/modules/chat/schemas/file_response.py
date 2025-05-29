from pydantic import ConfigDict
from app.core.base_model import ResponseSchema
from datetime import datetime


class FileResponse(ResponseSchema):
	"""Response schema for file information"""

	model_config = ConfigDict(from_attributes=True)

	id: str
	name: str
	original_name: str
	size: int
	formatted_size: str
	type: str
	upload_date: datetime
	download_count: int
	is_image: bool
	is_video: bool
	is_audio: bool
	is_document: bool
	file_extension: str
