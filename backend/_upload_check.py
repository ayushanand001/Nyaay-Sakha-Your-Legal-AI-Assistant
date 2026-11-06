import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

import app.services.case_uploads as case_uploads
import app.services.storage as storage
from app.core.deps import get_current_user
from app.main import app
from app.routes import analysis

upload_root = Path(tempfile.mkdtemp())
storage.UPLOAD_ROOT = upload_root
saved = {}


def fake_insert(**kwargs):
    saved.update(kwargs)
    return (
        "11111111-1111-1111-1111-111111111111",
        kwargs["filename"],
        kwargs["content_type"],
        kwargs["size_bytes"],
        kwargs["text"],
        datetime.now(timezone.utc),
        kwargs["stored_path"],
    )


case_uploads.insert_upload = fake_insert
analysis.load_precedents = lambda *args, **kwargs: []

client = TestClient(app)

try:
    anonymous = client.post(
        "/uploads",
        files={"file": ("appeal.txt", b"A case file.", "text/plain")},
    )
    assert anonymous.status_code == 401, anonymous.text

    app.dependency_overrides[get_current_user] = lambda: {"user_id": "user-1"}

    missing = client.post("/uploads")
    assert missing.status_code == 422, missing.status_code

    bad = client.post(
        "/uploads",
        files={"file": ("notes.png", b"not-a-case", "image/png")},
    )
    assert bad.status_code == 400, bad.text

    empty = client.post(
        "/uploads",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert empty.status_code == 400, empty.text

    text = (
        "The petitioner challenged the dismissal order. "
        "The tribunal recorded that the inquiry was complete."
    )
    ok = client.post(
        "/uploads",
        files={"file": ("appeal.txt", text.encode(), "text/plain")},
    )
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["filename"] == "appeal.txt"
    assert "petitioner" in body["excerpt"].lower()
    assert saved["user_id"] == "user-1"
    stored = upload_root / saved["stored_path"]
    assert stored.is_file()
    assert stored.read_bytes() == text.encode()

    analyzed = client.post(
        "/analysis/analyze",
        files={"file": ("second.txt", b"A second case about bail.", "text/plain")},
    )
    assert analyzed.status_code == 200, analyzed.text
    payload = analyzed.json()
    assert payload["upload"]["filename"] == "second.txt"
    assert payload["summary"]["implemented"] is True
    assert "bail" in payload["summary"]["summary"].lower()
    assert payload["similar_cases"]["cases"] == []
    assert payload["prediction"]["outcome"] in {None, "Accepted", "Rejected"}

    print("upload checks passed")
finally:
    app.dependency_overrides.clear()
    shutil.rmtree(upload_root, ignore_errors=True)
