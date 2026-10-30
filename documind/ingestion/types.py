from dataclasses import dataclass, field


@dataclass
class Block:
    text: str
    page: int | None = None                                 # PDFs
    heading_path: list[str] = field(default_factory=list)   # MD/HTML: ["Setup", "Docker", "Volumes"]

@dataclass
class Chunk:
    index: int
    content: str
    token_count: int
    page: int | None
    heading_path: list[str]
    content_hash: str          # sha256(content), needed for re-upload idempotency late