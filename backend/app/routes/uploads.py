from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.deps import get_current_user
from app.schemas.analysis import UploadRecord
from app.services.case_uploads import (
    get_user_upload,
    list_user_uploads,
    open_user_upload,
    remove_user_upload,
    store_uploaded_case,
)

router = APIRouter(prefix="/uploads", tags=["File Upload"])


@router.post("", response_model=UploadRecord, status_code=201)
async def upload_case(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    _, upload = await store_uploaded_case(file, user["user_id"])
    return upload


@router.get("", response_model=list[UploadRecord])
def get_uploads(
    limit: int = Query(default=20, ge=1, le=50),
    user=Depends(get_current_user),
):
    return list_user_uploads(user["user_id"], limit)


@router.get("/{upload_id}", response_model=UploadRecord)
def get_one_upload(
    upload_id: str,
    user=Depends(get_current_user),
):
    return get_user_upload(upload_id, user["user_id"])


@router.get("/{upload_id}/file")
def download_upload(
    upload_id: str,
    user=Depends(get_current_user),
):
    path, upload = open_user_upload(upload_id, user["user_id"])
    return FileResponse(
        path,
        media_type=upload["content_type"],
        filename=upload["filename"],
    )


@router.delete("/{upload_id}")
def delete_uploaded_case(
    upload_id: str,
    user=Depends(get_current_user),
):
    remove_user_upload(upload_id, user["user_id"])
    return {"message": "Upload removed"}
