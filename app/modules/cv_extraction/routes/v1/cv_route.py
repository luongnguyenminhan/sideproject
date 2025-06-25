from fastapi import APIRouter, Depends, Header, UploadFile, File

from app.core.base_model import APIResponse
from app.core.config import FERNET_KEY
from app.middleware.translation_manager import _
from app.modules.cv_extraction.schemas.cv import ProcessCVRequest
from app.modules.cv_extraction.repository.cv_repo import CVRepository


route = APIRouter(prefix="/cv", tags=["CV"])


@route.get("/")
async def get_user_info():
    """
    Lấy thông tin người dùng hiện tại.
    """
    return {"message": "User information retrieved successfully."}


@route.post("/process", response_model=APIResponse)
async def process_cv(
    request: ProcessCVRequest,
    cv_repo: CVRepository = Depends(CVRepository),
):
    """
    Xử lý file CV từ URL.
    """

    # Validate that URL is provided
    if not request.cv_file_url:
        return APIResponse(
            error_code=1,
            message=_("cv_file_url_required"),
            data=None,
        )

    return await cv_repo.process_cv(request)


@route.post("/process-file", response_model=APIResponse)
async def process_cv_binary(
    file: UploadFile = File(...),
    cv_repo: CVRepository = Depends(CVRepository),
):
    """
    Xử lý file CV từ binary upload.
    """

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(
        (".pdf", ".docx", ".txt")
    ):
        return APIResponse(
            error_code=1,
            message=_("unsupported_file_type"),
            data=None,
        )

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        return APIResponse(
            error_code=1,
            message=_("failed_to_read_file"),
            data=None,
        )

    # Create request object without URL but with file data
    request = ProcessCVRequest()

    return await cv_repo.process_cv_binary(request, file_content, file.filename)
