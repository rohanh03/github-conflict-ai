import logging

from fastapi import FastAPI

from app.webhooks.router import router as webhook_router
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="github-conflict-ai",
    description="AI-powered GitHub conflict detection and PR summarization",
    version="0.1.0",
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
