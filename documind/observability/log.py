import asyncio
import logging
import time
from types import TracebackType
from typing import Self

from openai.types import CompletionUsage


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


class LLMCallLogger:
    """Times one LLM call and logs model, token usage and latency.

    Use as a context manager around the call. Never logs prompt or answer text.
    """

    def __init__(self, endpoint: str, model: str, logger: logging.Logger | None = None) -> None:
        self.endpoint = endpoint
        self.model = model
        self.logger = logger or logging.getLogger("documind.llm")
        self.prompt_tokens: int | None = None
        self.completion_tokens: int | None = None
        self._start = 0.0

    def record_usage(self, usage: CompletionUsage | None) -> None:
        if usage is not None:
            self.prompt_tokens = usage.prompt_tokens
            self.completion_tokens = usage.completion_tokens

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        latency_ms = round((time.perf_counter() - self._start) * 1000)
        fields = (
            f"endpoint={self.endpoint} model={self.model} "
            f"prompt_tokens={self.prompt_tokens} completion_tokens={self.completion_tokens} "
            f"latency_ms={latency_ms}"
        )
        if exc_type is None:
            self.logger.info("llm_call %s", fields)
        elif issubclass(exc_type, (GeneratorExit, asyncio.CancelledError)):
            self.logger.warning("llm_call cancelled %s", fields)
        else:
            self.logger.error("llm_call failed %s error=%s", fields, exc_type.__name__)
