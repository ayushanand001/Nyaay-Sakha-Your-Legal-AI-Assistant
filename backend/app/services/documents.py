import io
import os
import re
import zlib

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".text"}
DISCLAIMER = (
    "Nyaay Sakha is a supportive tool for legal professionals. "
    "Summaries, similar cases, and outcome indications are not legal advice "
    "and do not replace the judgment of lawyers or judges."
)


async def read_case_upload(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A file name is required")

    extension = os.path.splitext(file.filename)[1].lower()

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

    text = extract_text(extension, data)

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the document"
        )

    return file.filename, text


def extract_text(extension, data):
    if extension in {".txt", ".text"}:
        return data.decode("utf-8", errors="replace").strip()

    try:
        from pypdf import PdfReader
    except ImportError:
        return _extract_pdf_text_fallback(data).strip()

    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages).strip()


def excerpt(text, limit=400):
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[:limit].rstrip() + "..."


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
            .replace(rb"\\", b"\\")
        )
        parts.append(value.decode("utf-8", errors="ignore"))

    return " ".join(part.strip() for part in parts if part.strip())
