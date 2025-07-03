from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
import os
import json
import logging

from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
from app.modules.cv_generation.schemas.cv_generation_request import (
    CVGenerationRequest,
    CVPreviewRequest,
    CVBatchGenerationRequest,
)
from app.modules.cv_generation.schemas.cv_generation_response import (
    CVGenerationResponse,
    CVPreviewResponse,
    CVTemplateListResponse,
    CVBatchGenerationResponse,
)
from app.modules.cv_generation.services.cv_generation_service import CVGenerationService

route = APIRouter(prefix="/cv-generation", tags=["CV Generation"])


@route.post("/generate", response_model=APIResponse)
@handle_exceptions
async def generate_cv(
    request: CVGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Tạo CV PDF từ CV extraction data

    - **cv_data**: CV data từ extraction module
    - **template_type**: Loại template (modern, classic, creative)
    - **custom_prompt**: Custom prompt cho AI (optional)
    - **color_theme**: Màu theme (blue, green, red, purple, orange, teal, black)
    - **output_format**: Format output (pdf, latex)
    """
    logger.info("🚀 CV Generation Request Started")
    logger.info(
        f"📊 Request details: template_type={request.template_type}, color_theme={request.color_theme}"
    )

    # Log request data (sanitized for privacy)
    try:
        cv_data_summary = {
            "has_cv_data": bool(request.cv_data),
            "cv_data_type": type(request.cv_data).__name__ if request.cv_data else None,
            "cv_data_keys": (
                list(request.cv_data.dict().keys())
                if hasattr(request.cv_data, "dict")
                else "N/A"
            ),
        }
        logger.info(f"📄 CV Data Summary: {json.dumps(cv_data_summary, indent=2)}")
    except Exception as e:
        logger.warning(f"Could not log CV data summary: {e}")

    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    # Generate CV
    logger.info("🔄 Starting CV generation process...")
    result = await cv_service.generate_cv_pdf(
        cv_data=request.cv_data,
        template_type=request.template_type,
        custom_prompt=request.custom_prompt,
        color_theme=request.color_theme,
    )

    # Log comprehensive result
    logger.info("📋 CV Generation Result:")
    try:
        result_summary = {
            "success": result.success,
            "message": result.message,
            "has_pdf_file_url": bool(getattr(result, "pdf_file_url", None)),
            "has_latex_source": bool(getattr(result, "latex_source", None)),
            "file_size": getattr(result, "file_size", None),
            "generation_time": getattr(result, "generation_time", None),
            "template_used": getattr(result, "template_used", None),
            "llm_token_usage": (
                {
                    "input_tokens": (
                        getattr(result.llm_token_usage, "input_tokens", None)
                        if hasattr(result, "llm_token_usage") and result.llm_token_usage
                        else None
                    ),
                    "output_tokens": (
                        getattr(result.llm_token_usage, "output_tokens", None)
                        if hasattr(result, "llm_token_usage") and result.llm_token_usage
                        else None
                    ),
                    "total_tokens": (
                        getattr(result.llm_token_usage, "total_tokens", None)
                        if hasattr(result, "llm_token_usage") and result.llm_token_usage
                        else None
                    ),
                    "price_usd": (
                        getattr(result.llm_token_usage, "price_usd", None)
                        if hasattr(result, "llm_token_usage") and result.llm_token_usage
                        else None
                    ),
                }
                if hasattr(result, "llm_token_usage") and result.llm_token_usage
                else None
            ),
        }
        logger.info(
            f"📊 Result Details: {json.dumps(result_summary, indent=2, default=str)}"
        )
    except Exception as e:
        logger.error(f"❌ Could not log result summary: {e}")
        logger.info(f"📊 Raw Result: {result}")

    # Log LaTeX source (first 500 chars) if available
    if hasattr(result, "latex_source") and result.latex_source:
        latex_preview = (
            result.latex_source[:500] + "..."
            if len(result.latex_source) > 500
            else result.latex_source
        )
        logger.info(f"📝 LaTeX Source Preview: {latex_preview}")

    # Add cleanup task
    background_tasks.add_task(cv_service.cleanup_temp_files)

    response = APIResponse(
        error_code=0 if result.success else 1,
        message=result.message if result.message else _("cv_generation_completed"),
        data=result,
    )

    logger.info(
        f"✅ CV Generation Completed - Success: {result.success}, Error Code: {response.error_code}"
    )
    return response


@route.post("/preview", response_model=APIResponse)
@handle_exceptions
async def preview_cv(request: CVPreviewRequest, db: Session = Depends(get_db)):
    """
    Tạo preview CV (HTML format)

    - **cv_data**: CV data từ extraction module
    - **template_type**: Loại template
    - **preview_format**: Format preview (html, png)
    """
    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    result = await cv_service.generate_cv_preview(
        cv_data=request.cv_data, template_type=request.template_type
    )

    if result["success"]:
        response = CVPreviewResponse(
            success=True, preview_data=result["preview_html"], preview_format="html"
        )
        return APIResponse(
            error_code=0, message=_("preview_generated_successfully"), data=response
        )
    else:
        response = CVPreviewResponse(
            success=False,
            preview_data=f'<html><body><h1>Error</h1><p>{result["error"]}</p></body></html>',
            preview_format="html",
        )
        return APIResponse(
            error_code=1, message=_("preview_generation_failed"), data=response
        )


@route.post("/batch-generate", response_model=APIResponse)
@handle_exceptions
async def batch_generate_cv(
    request: CVBatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Tạo multiple CV PDFs cùng lúc

    - **cv_data_list**: List CV data từ extraction module
    - **template_type**: Loại template
    - **output_format**: Format output (pdf, latex)
    """
    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    results = []
    success_count = 0
    failed_count = 0

    for i, cv_data in enumerate(request.cv_data_list):
        try:
            result = await cv_service.generate_cv_pdf(
                cv_data=cv_data,
                template_type=request.template_type,
                filename=f"cv_batch_{i + 1}",
            )
            results.append(result)

            if result.success:
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            failed_result = CVGenerationResponse(
                success=False, message=f"Individual CV generation failed: {str(e)}"
            )
            results.append(failed_result)
            failed_count += 1

    # Add cleanup task
    background_tasks.add_task(cv_service.cleanup_temp_files)

    batch_response = CVBatchGenerationResponse(
        success=success_count > 0,
        total_count=len(request.cv_data_list),
        success_count=success_count,
        failed_count=failed_count,
        results=results,
    )

    return APIResponse(
        error_code=0 if batch_response.success else 1,
        message=_("batch_generation_completed").format(
            success=success_count, failed=failed_count
        ),
        data=batch_response,
    )


@route.get("/templates", response_model=APIResponse)
@handle_exceptions
async def get_available_templates(db: Session = Depends(get_db)):
    """
    Lấy danh sách templates có sẵn
    """
    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    result = await cv_service.get_available_templates()

    response = CVTemplateListResponse(
        templates=result["templates"], total_count=result["total_count"]
    )

    return APIResponse(
        error_code=0, message=_("templates_retrieved_successfully"), data=response
    )


@route.get("/system-info", response_model=APIResponse)
@handle_exceptions
async def get_system_info(db: Session = Depends(get_db)):
    """
    Lấy thông tin về HTML to PDF conversion system và capabilities
    """
    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    info = cv_service.get_html_system_info()

    return APIResponse(
        error_code=0 if info.get("weasyprint_available", False) else 1,
        message=_("system_info_retrieved_successfully"),
        data=info,
    )


@route.get("/download/{filename}")
@handle_exceptions
async def download_cv(filename: str):
    """
    Download CV PDF file

    - **filename**: Tên file PDF (không cần extension)
    """
    # Ensure filename ends with .pdf
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    file_path = os.path.join("temp_cvs", filename)

    if not os.path.exists(file_path):
        return APIResponse(error_code=1, message=_("cv_file_not_found"), data=None)

    return FileResponse(path=file_path, filename=filename, media_type="application/pdf")


@route.delete("/cleanup", response_model=APIResponse)
@handle_exceptions
async def cleanup_temp_files(db: Session = Depends(get_db)):
    """
    Cleanup temporary files
    """
    # Initialize service with database session
    cv_service = CVGenerationService(db=db)

    cv_service.cleanup_temp_files()

    return APIResponse(
        error_code=0,
        message=_("temp_files_cleaned_successfully"),
        data={"cleaned": True},
    )
