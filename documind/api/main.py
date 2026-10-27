from fastapi import FastAPI

from documind.api.routers import health

app = FastAPI(title="DocuMind")

app.include_router(health.router)
