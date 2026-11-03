from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    document_id: UUID
    collection_id: UUID
    filename: str
    kind: str
    size_bytes: int
    sha256: str
