class UnsupportedFileType(Exception):
    def __init__(self, source_type: str) -> None:
        super().__init__(f"Unsupported file type: {source_type}")