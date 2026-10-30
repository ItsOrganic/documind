from documind.ingestion.extractors import get_extractor
from fastapi import HTTPException
import codecs
from typing import Literal
from pathlib import Path
from documind.ingestion.errors import UnsupportedFileType
from documind.api.schemas import UploadResponse
from fastapi import UploadFile
from uuid import UUID
from fastapi import APIRouter

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

router = APIRouter()

@router.post("/upload")
async def upload_document(collection_id: UUID, file: UploadFile) -> UploadResponse:
    head = await file.read(SNIFF_BYTES)

    try:
        kind = detect_file_type(file.filename, head)
    except UnsupportedFileType as e:
        raise HTTPException(status_code=415, detail=str(e))
    
    extract = get_extractor(kind).extract(Path)
    
    return UploadResponse(
        collection_id=collection_id,
        filename=file.filename,
        message="Document uploaded successfully"
    )


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
