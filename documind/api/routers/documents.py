import codecs
import hashlib
import os
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

import anyio
from fastapi import APIRouter, HTTPException, UploadFile

from documind.api.schemas import UploadResponse
from documind.ingestion.errors import UnsupportedFileType

FileKind = Literal["pdf", "markdown", "html", "text"]

ALLOWED_EXTENSIONS: dict[str, FileKind] = {
    ".pdf": "pdf",
    ".md": "markdown",
    ".markdown": "markdown",
    ".html": "html",
    ".htm": "html",
    ".txt": "text",
}
SNIFF_BYTES = 4096
WRITE_CHUNK_BYTES = 1024 * 1024

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "storage/uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

router = APIRouter(tags=["documents"])


class FileTooLarge(Exception):
    pass


@router.post("/collections/{collection_id}/documents", status_code=202)
async def upload_document(collection_id: UUID, file: UploadFile) -> UploadResponse:
    filename = file.filename or ""
    head = await file.read(SNIFF_BYTES)

    try:
        kind = detect_file_type(filename, head)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=415, detail=str(e))

    document_id = uuid4()
    # never use the client's filename on disk; it may contain "../"
    path = UPLOAD_DIR / f"{document_id}{Path(filename).suffix.lower()}"

    await file.seek(0)  # the sniff above moved the read position past the first 4 KB
    try:
        size, sha256 = await _save_upload(file, path)
    except FileTooLarge:
        raise HTTPException(
            status_code=413,
            detail=f"file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB",
        )

    return UploadResponse(
        document_id=document_id,
        collection_id=collection_id,
        filename=filename,
        kind=kind,
        size_bytes=size,
        sha256=sha256,
    )


async def _save_upload(file: UploadFile, path: Path) -> tuple[int, str]:
    """Stream the upload to disk, hashing as it goes. Removes the partial file on failure."""
    await anyio.Path(path.parent).mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    try:
        async with await anyio.open_file(path, "wb") as out:
            while chunk := await file.read(WRITE_CHUNK_BYTES):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise FileTooLarge
                digest.update(chunk)
                await out.write(chunk)
    except BaseException:
        await anyio.Path(path).unlink(missing_ok=True)
        raise
    return size, digest.hexdigest()


def detect_file_type(filename: str | None, head: bytes) -> FileKind:
    ext = Path(filename or "").suffix.lower()
    kind = ALLOWED_EXTENSIONS.get(ext)
    if kind is None:
        raise UnsupportedFileType(ext or "no extension")

    if kind == "pdf":
        if not head.startswith(b"%PDF-"):
            raise UnsupportedFileType("file is not a valid PDF")
        return kind

    # Text formats: must decode as UTF-8 and contain no null bytes
    if b"\x00" in head:
        raise UnsupportedFileType(f"{ext} file contains binary data")
    try:
        # incremental decoder: a multibyte character cut off at the end of `head` isn't an error
        codecs.getincrementaldecoder("utf-8")().decode(head, final=False)
    except UnicodeDecodeError:
        raise UnsupportedFileType(f"{ext} file is not valid UTF-8 text")

    return kind
