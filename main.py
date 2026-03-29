#mar15 added CORS middleware, setup API router, and static file serving for GitMax frontend
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.setup import router as setup_router
from app.webhooks.router import router as webhook_router
from config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="GitMax",
    description="AI-powered GitHub conflict detection and PR summarization",
    version="0.1.0",
)

#mar15 CORS for frontend dev server on port 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#mar15 register API routers before static mount
app.include_router(webhook_router)
app.include_router(setup_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


#mar15 serve built frontend in production — must be LAST (catch-all)
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
