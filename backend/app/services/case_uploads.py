from fastapi import HTTPException

from app.db.uploads import delete_upload, get_upload, insert_upload, list_uploads
from app.services.documents import excerpt, read_case_upload
from app.services.storage import delete_stored_file, resolve_stored_file, save_case_file


async def store_uploaded_case(file, user_id):
    case = await read_case_upload(file)
    stored_path = save_case_file(user_id, case["extension"], case["data"])

    try:
        row = insert_upload(
            user_id=user_id,
            filename=case["filename"],
            stored_path=stored_path,
            content_type=case["content_type"],
            extension=case["extension"],
            size_bytes=case["size_bytes"],
            text=case["text"],
        )
    except Exception:
        delete_stored_file(stored_path)
        raise HTTPException(
            status_code=503,
            detail="Could not store the uploaded file"
        )

    upload = to_upload_record(row)
    return case["text"], upload


def list_user_uploads(user_id, limit):
    try:
        rows = list_uploads(user_id, limit)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Uploaded documents are unavailable"
        )

    return [to_upload_record(row, excerpt_only=True) for row in rows]


def get_user_upload(upload_id, user_id):
    row = _fetch_upload(upload_id, user_id)

    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")

    return to_upload_record(row)


def open_user_upload(upload_id, user_id):
    row = _fetch_upload(upload_id, user_id)

    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload = to_upload_record(row)
    path = resolve_stored_file(row[6])
    return path, upload


def remove_user_upload(upload_id, user_id):
    try:
        row = delete_upload(upload_id, user_id)
    except Exception as exc:
        _raise_upload_error(exc)

    if not row:
        raise HTTPException(status_code=404, detail="Upload not found")

    delete_stored_file(row[0])


def to_upload_record(row, excerpt_only=False):
    text = row[4] or ""
    characters = row[7] if excerpt_only else len(text)

    return {
        "id": str(row[0]),
        "filename": row[1],
        "content_type": row[2],
        "size_bytes": row[3],
        "characters": characters,
        "excerpt": excerpt(text),
        "created_at": row[5].isoformat(),
    }


def _fetch_upload(upload_id, user_id):
    try:
        return get_upload(upload_id, user_id)
    except Exception as exc:
        _raise_upload_error(exc)


def _raise_upload_error(exc):
    if "invalid input syntax for type uuid" in str(exc).lower():
        raise HTTPException(status_code=400, detail="Invalid upload id")

    raise HTTPException(
        status_code=503,
        detail="Uploaded documents are unavailable"
    )
