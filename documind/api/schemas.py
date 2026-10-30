from uuid import UUID
from pydantic import BaseModel
class UploadResponse(BaseModel):
    collection_id: UUID
    filename: str
    message: str