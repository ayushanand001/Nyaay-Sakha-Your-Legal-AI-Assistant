import io
import os
import re
import zlib
from pathlib import Path

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".text"}
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".text": "text/plain",
}
DISCLAIMER = (
    "Nyaay Sakha is a supportive tool for legal professionals. "
    "Summaries, similar cases, and outcome indications are not legal advice "
    "and do not replace the judgment of lawyers or judges."
)


async def read_case_upload(file: UploadFile):
    filename = _original_filename(file.filename)
    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Upload a PDF or text file"
        )

    data = await file.read()

    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File is larger than 8 MB"
        )

    _validate_contents(extension, data)
    text = extract_text(extension, data)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the document"
        )

    return {
        "filename": filename,
        "extension": extension,
        "content_type": CONTENT_TYPES[extension],
        "size_bytes": len(data),
        "data": data,
        "text": text.strip(),
    }


def extract_text(extension, data):
    if extension in {".txt", ".text"}:
        return _clean_extracted_text(data.decode("utf-8", errors="replace"))

    text = ""

    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Encrypted PDFs are not supported"
            )

        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except HTTPException:
        raise
    except Exception:
        text = ""

    text = _clean_extracted_text(text)
    if _readable_text(text):
        return text

    fallback = _clean_extracted_text(_extract_pdf_text_fallback(data))
    if _readable_text(fallback):
        return fallback

    return ""


def _clean_extracted_text(text):
    # PostgreSQL rejects NUL bytes, which PDF extractors sometimes emit.
    return (text or "").replace("\x00", "").strip()


def _readable_text(text):
    sample = text[:5000]
    if len(sample) < 40:
        return False
    readable = sum(character.isalpha() or character.isspace() for character in sample)
    return readable / len(sample) >= 0.6


def excerpt(text, limit=400):
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


def _original_filename(filename):
    if not filename:
        raise HTTPException(status_code=400, detail="A file name is required")

    name = Path(filename).name.replace("\x00", "").strip()

    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="A file name is required")

    return name[:255]


def _validate_contents(extension, data):
    if extension == ".pdf":
        if b"%PDF-" not in data[:1024]:
            raise HTTPException(
                status_code=400,
                detail="The file is not a valid PDF"
            )
        return

    if b"\x00" in data:
        raise HTTPException(
            status_code=400,
            detail="The text file contains binary data"
        )


def _extract_pdf_text_fallback(data):
    pieces = []

    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
        raw = match.group(1)
        try:
            decoded = zlib.decompress(raw)
        except zlib.error:
            decoded = raw
        pieces.append(_pdf_literal_strings(decoded))

    text = "\n".join(piece for piece in pieces if piece).strip()

    if text:
        return text

    return _pdf_literal_strings(data)


def _pdf_literal_strings(data):
    parts = []

    for match in re.finditer(rb"\((?:\\.|[^\\)])*\)", data):
        value = match.group(0)[1:-1]
        value = (
            value.replace(rb"\n", b"\n")
            .replace(rb"\r", b"\r")
            .replace(rb"\t", b"\t")
            .replace(rb"\(", b"(")
            .replace(rb"\)", b")")
            .replace(rb"\\\\", b"\\")
        )
        parts.append(value.decode("utf-8", errors="ignore"))

    return " ".join(part.strip() for part in parts if part.strip())
