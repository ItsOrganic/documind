import json
import os

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

from documind.observability.log import LLMCallLogger

router = APIRouter()

client = AsyncOpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "ollama"),
)
model = os.getenv("LLM_MODEL", "llama3.2:1b")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    model: str

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    async def event_stream():
        with LLMCallLogger("/chat/stream", model) as log:
            stream = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": req.message},
                ],
                temperature=0.7,
                stream=True,
                stream_options={"include_usage": True},
                max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
            )
            async for chunk in stream:
                log.record_usage(chunk.usage)
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    yield f"event: token\ndata: {json.dumps(delta)}\n\n"

            yield "event: done\ndata: {}\n\n"
    
    return StreamingResponse(event_stream(), 
    media_type="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"} )


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    with LLMCallLogger("/chat", model) as log:
        completion = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": req.message},
            ],
            temperature=0.7,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
        )
        log.record_usage(completion.usage)

    return ChatResponse(
        response=completion.choices[0].message.content or "",
        model=completion.model,
    )
