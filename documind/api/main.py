from fastapi import FastAPI

from documind.api.routers import chat, documents, health
from documind.observability.log import setup_logging

setup_logging()

app = FastAPI(title="DocuMind")

app.include_router(health.router)
app.include_router(chat.router)