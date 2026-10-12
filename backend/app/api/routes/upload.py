"""
Upload API routes for CSV/XLSX dataset files.
"""

from typing import Optional
from fastapi import APIRouter, File, Header, Response, UploadFile, status
from app.schemas.dataset import DatasetUploadResponse
from app.services.upload_service import upload_service

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "",
    response_model=DatasetUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and validate a time-series dataset file",
)
async def upload_file(
    response: Response,
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
) -> DatasetUploadResponse:
    content = await file.read()
    response_data, active_session_id = upload_service.process_upload(
        raw_filename=file.filename or "uploaded_dataset",
        content=content,
        session_id=x_session_id,
    )

    if active_session_id:
        response.headers["X-Session-ID"] = active_session_id

    return response_data
