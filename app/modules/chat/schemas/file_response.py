from pydantic import ConfigDict, Field

## IMPORT NGOÀI MODULE CẦN XỬ LÍ
from app.core.base_model import ResponseSchema
from datetime import datetime
from typing import List, Optional


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
	download_url: Optional[str] = Field(default=None, description='Temporary download URL')


class UploadFileResponse(ResponseSchema):
	"""Response schema for file upload"""

	uploaded_files: List[FileResponse]
	failed_files: List[str] = Field(default_factory=list, description='List of failed file names')
