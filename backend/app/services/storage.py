import re
import uuid
from pathlib import Path

from fastapi import HTTPException

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"


def save_case_file(user_id, extension, data):
    folder = UPLOAD_ROOT / _safe_user_folder(user_id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{extension}"
    path = folder / stored_name
    path.write_bytes(data)
    return f"{folder.name}/{stored_name}"


def resolve_stored_file(relative_path):
    if not relative_path or ".." in relative_path.replace("\\", "/"):
        raise HTTPException(status_code=400, detail="Invalid file path")

    root = UPLOAD_ROOT.resolve()
    path = (UPLOAD_ROOT / relative_path).resolve()

    if path != root and root not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded file is missing")

    return path


def delete_stored_file(relative_path):
    if not relative_path:
        return

    try:
        path = resolve_stored_file(relative_path)
    except HTTPException:
        return

    path.unlink(missing_ok=True)


def _safe_user_folder(user_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "", str(user_id))
    return safe or "user"
