class HeadingStack:
    """Tracks the current heading path while walking a document top to bottom.

    Seeing an h2 drops everything at level 2 or deeper, then pushes the new heading:
    h1 "Setup" -> h2 "Docker" -> h3 "Volumes" -> h2 "Kubernetes"
    gives ["Setup", "Docker", "Volumes"] then ["Setup", "Kubernetes"].
    """

    def __init__(self) -> None:
        self._stack: list[tuple[int, str]] = []

    def push(self, level: int, title: str) -> None:
        while self._stack and self._stack[-1][0] >= level:
            self._stack.pop()
        self._stack.append((level, title))

    def path(self) -> list[str]:
        return [title for _, title in self._stack]
