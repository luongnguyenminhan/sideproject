from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.modules.cv_extraction.schemas.cv import LLMTokenUsage


class CVGenerationResponse(BaseModel):
    """Response schema cho CV generation"""

    success: bool = Field(description="Trạng thái generation")
    message: Optional[str] = Field(default=None, description="Thông báo")
    pdf_file_url: Optional[str] = Field(default=None, description="URL file PDF")
    html_source: Optional[str] = Field(default=None, description="Source HTML")
    preview_url: Optional[str] = Field(default=None, description="URL preview")
    file_size: Optional[int] = Field(
        default=None, description="Kích thước file (bytes)"
    )
    generation_time: Optional[float] = Field(
        default=None, description="Thời gian generation (seconds)"
    )
    template_used: Optional[str] = Field(
        default=None, description="Template đã sử dụng"
    )
    llm_token_usage: Optional[LLMTokenUsage] = Field(
        default=None, description="Token usage"
    )


class CVTemplateResponse(BaseModel):
    """Response schema cho template"""

    template_id: str = Field(description="ID template")
    template_name: str = Field(description="Tên template")
    template_type: str = Field(description="Loại template")
    description: Optional[str] = Field(default=None, description="Mô tả template")
    preview_image_url: Optional[str] = Field(
        default=None, description="URL preview image"
    )
    latex_source: Optional[str] = Field(default=None, description="Source LaTeX")
    created_at: Optional[str] = Field(default=None, description="Ngày tạo")
    updated_at: Optional[str] = Field(default=None, description="Ngày cập nhật")


class CVPreviewResponse(BaseModel):
    """Response schema cho preview"""

    success: bool = Field(description="Trạng thái preview")
    preview_url: Optional[str] = Field(default=None, description="URL preview")
    preview_format: Optional[str] = Field(default=None, description="Format preview")
    preview_data: Optional[str] = Field(
        default=None, description="Data preview (base64 cho image)"
    )


class CVBatchGenerationResponse(BaseModel):
    """Response schema cho batch generation"""

    success: bool = Field(description="Trạng thái batch generation")
    total_count: int = Field(description="Tổng số CV")
    success_count: int = Field(description="Số CV thành công")
    failed_count: int = Field(description="Số CV thất bại")
    results: List[CVGenerationResponse] = Field(description="Kết quả từng CV")
    batch_id: Optional[str] = Field(default=None, description="ID batch")
    zip_file_url: Optional[str] = Field(
        default=None, description="URL file ZIP chứa tất cả PDF"
    )


class CVTemplateListResponse(BaseModel):
    """Response schema cho list templates"""

    templates: List[CVTemplateResponse] = Field(description="List templates")
    total_count: int = Field(description="Tổng số templates")


class CVGenerationStatusResponse(BaseModel):
    """Response schema cho status generation"""

    status: str = Field(
        description="Trạng thái: pending, processing, completed, failed"
    )
    progress: Optional[float] = Field(default=None, description="Tiến độ (0-100)")
    message: Optional[str] = Field(default=None, description="Thông báo")
    estimated_time: Optional[float] = Field(
        default=None, description="Thời gian ước tính (seconds)"
    )
