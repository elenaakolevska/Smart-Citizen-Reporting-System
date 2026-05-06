from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES: set[str] = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "application/pdf",
}

ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".pdf"}

MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

STATIC_URL_PREFIX = "/static/uploads"


def validate_upload(filename: str, content_type: str) -> None:
    ext = Path(filename).suffix.lower()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File type '{content_type}' is not allowed. "
                f"Accepted types: jpg, png, pdf."
            ),
        )

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File extension '{ext}' is not allowed. "
                f"Accepted extensions: .jpg, .jpeg, .png, .pdf."
            ),
        )


async def save_upload(file: UploadFile) -> tuple[str, int]:
    validate_upload(file.filename or "", file.content_type or "")

    contents: bytes = await file.read()
    size = len(contents)

    if size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large ({size / 1024 / 1024:.1f} MB). Maximum allowed size is 5 MB.",
        )

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    ext = Path(file.filename or "file").suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_name
    dest.write_bytes(contents)

    file_url = f"{STATIC_URL_PREFIX}/{unique_name}"
    return file_url, size