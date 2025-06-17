from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.base_model import APIResponse
from app.exceptions.handlers import handle_exceptions
from app.middleware.translation_manager import _
from app.modules.agentic_rag.repository.global_kb_repo import GlobalKBRepo
from app.modules.agentic_rag.schemas.global_kb_request import (
    CreateGlobalKBRequest,
    UpdateGlobalKBRequest,
    SearchGlobalKBRequest,
)
from app.modules.agentic_rag.schemas.global_kb_response import GlobalKBResponse
from app.utils.minio.minio_handler import minio_handler

route = APIRouter(prefix="/global-kb", tags=["global-kb-admin"])


@route.get("/", response_model=APIResponse)
@handle_exceptions
def list_documents(repo: GlobalKBRepo = Depends()):
    docs = repo.list_documents()
    return APIResponse(
        error_code=0,
        message=_("success"),
        data=[GlobalKBResponse.model_validate(doc) for doc in docs],
    )


@route.get("/{doc_id}", response_model=APIResponse)
@handle_exceptions
def get_document(doc_id: str, repo: GlobalKBRepo = Depends()):
    doc = repo.get_document(doc_id)
    return APIResponse(
        error_code=0, message=_("success"), data=GlobalKBResponse.model_validate(doc)
    )


@route.post("/", response_model=APIResponse)
@handle_exceptions
def create_document(request: CreateGlobalKBRequest, repo: GlobalKBRepo = Depends()):
    doc = repo.create_document(request.model_dump())
    return APIResponse(
        error_code=0, message=_("success"), data=GlobalKBResponse.model_validate(doc)
    )


@route.put("/{doc_id}", response_model=APIResponse)
@handle_exceptions
def update_document(
    doc_id: str, request: UpdateGlobalKBRequest, repo: GlobalKBRepo = Depends()
):
    doc = repo.update_document(doc_id, request.model_dump(exclude_unset=True))
    return APIResponse(
        error_code=0, message=_("success"), data=GlobalKBResponse.model_validate(doc)
    )


@route.delete("/{doc_id}", response_model=APIResponse)
@handle_exceptions
def delete_document(doc_id: str, repo: GlobalKBRepo = Depends()):
    repo.delete_document(doc_id)
    return APIResponse(error_code=0, message=_("success"), data=None)


@route.post("/search", response_model=APIResponse)
@handle_exceptions
def search_documents(
    request: SearchGlobalKBRequest = Depends(), repo: GlobalKBRepo = Depends()
):
    docs = repo.search_documents(request.query, request.top_k, request.category)
    return APIResponse(
        error_code=0,
        message=_("success"),
        data=[GlobalKBResponse.model_validate(doc) for doc in docs],
    )


@route.get("/stats", response_model=APIResponse)
@handle_exceptions
def get_stats(repo: GlobalKBRepo = Depends()):
    stats = repo.stats()
    return APIResponse(error_code=0, message=_("success"), data=stats)


@route.post("/upload", response_model=APIResponse)
@handle_exceptions
async def upload_global_kb_file(
    file: UploadFile = File(...),
    title: str = None,
    category: str = "general",
    tags: str = None,  # comma separated
    repo: GlobalKBRepo = Depends(),
):
    """
    Upload file lên MinIO, lưu URL vào Global KB
    """
    # Upload file lên MinIO
    object_name = await minio_handler.upload_fastapi_file(
        file, meeting_id="global_kb", file_type="document"
    )
    file_url = minio_handler.get_file_url(object_name)
    # Lưu vào DB
    doc_data = {
        "title": title or file.filename,
        "content": file_url,  # hoặc có thể trích xuất text nếu cần
        "category": category,
        "tags": tags.split(",") if tags else [],
        "source": file_url,
    }
    doc = repo.create_document(doc_data)
    return APIResponse(
        error_code=0, message=_("success"), data=GlobalKBResponse.model_validate(doc)
    )


@route.delete("/file/{doc_id}", response_model=APIResponse)
@handle_exceptions
def delete_global_kb_file(doc_id: str, repo: GlobalKBRepo = Depends()):
    doc = repo.get_document(doc_id)
    if doc and doc.source:
        # Xóa file trên MinIO nếu có
        from urllib.parse import urlparse

        object_name = urlparse(doc.source).path.lstrip("/")
        minio_handler.remove_file(object_name)
    repo.delete_document(doc_id)
    return APIResponse(error_code=0, message=_("success"), data=None)
