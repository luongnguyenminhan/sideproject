from pydantic import Field
from app.core.base_model import RequestSchema, FilterableRequestSchema
from typing import Optional


class FileUploadRequest(RequestSchema):
    """Request schema for file upload metadata"""

    conversation_id: Optional[str] = Field(
        default=None, description="ID of conversation to associate file with"
    )


class FileListRequest(FilterableRequestSchema):
    """Request schema for listing files"""

    file_type: Optional[str] = Field(default=None, description="Filter by file type")
    search: Optional[str] = Field(default=None, description="Search in file names")
    conversation_id: Optional[str] = Field(
        default=None, description="Filter by conversation"
    )
