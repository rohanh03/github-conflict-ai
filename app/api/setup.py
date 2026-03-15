#mar15 API router for frontend setup wizard, config, health, and activity
"""
Setup & dashboard API endpoints for the GitMax frontend.
"""

import logging
import time
from typing import Optional

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.activity_log import get_recent, get_stats
from app.api.env_writer import update_env
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["setup"])

#mar15 track server start time for uptime calculation
_start_time = time.time()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class AuthSetup(BaseModel):
    mode: str  # "pat" or "app"
    github_token: Optional[str] = ""
    github_app_id: Optional[str] = ""
    github_private_key_path: Optional[str] = ""
    github_webhook_secret: Optional[str] = ""


class LLMSetup(BaseModel):
    llm_api_base: Optional[str] = ""
    llm_api_key: Optional[str] = ""
    llm_model: Optional[str] = ""


class SlackSetup(BaseModel):
    slack_webhook_url: Optional[str] = ""


# ---------------------------------------------------------------------------
# Health & config (read-only)
# ---------------------------------------------------------------------------

@router.get("/health")
async def extended_health():
    """Extended health check with integration status."""
    #mar15 reload settings to reflect any recent .env changes
    from config import settings as s
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - _start_time),
        "github_configured": bool(s.github_token or s.github_app_id),
        "llm_configured": bool(s.llm_api_key),
        "slack_configured": bool(s.slack_webhook_url),
    }


@router.get("/config")
async def get_config():
    """Return current config state (no secrets exposed)."""
    from config import settings as s
    auth_mode = "none"
    if s.github_token:
        auth_mode = "pat"
    elif s.github_app_id:
        auth_mode = "app"

    return {
        "auth_mode": auth_mode,
        "github_configured": bool(s.github_token or s.github_app_id),
        "llm_api_base": s.llm_api_base,
        "llm_model": s.llm_model,
        "slack_configured": bool(s.slack_webhook_url),
    }


# ---------------------------------------------------------------------------
# Setup endpoints (write .env)
# ---------------------------------------------------------------------------

@router.post("/setup/auth")
async def setup_auth(data: AuthSetup):
    """Save GitHub authentication config to .env."""
    try:
        updates = {}
        if data.mode == "pat":
            updates["GITHUB_TOKEN"] = data.github_token or ""
            #mar15 clear app settings when switching to PAT mode
            updates["GITHUB_APP_ID"] = "0"
            updates["GITHUB_PRIVATE_KEY_PATH"] = ""
        elif data.mode == "app":
            updates["GITHUB_APP_ID"] = data.github_app_id or "0"
            updates["GITHUB_PRIVATE_KEY_PATH"] = data.github_private_key_path or ""
            updates["GITHUB_TOKEN"] = ""

        if data.github_webhook_secret:
            updates["GITHUB_WEBHOOK_SECRET"] = data.github_webhook_secret

        update_env(updates)
        return {"success": True, "message": f"GitHub auth ({data.mode}) saved."}
    except Exception as e:
        logger.exception("Failed to save auth config")
        return {"success": False, "message": str(e)}


@router.post("/setup/llm")
async def setup_llm(data: LLMSetup):
    """Save LLM config to .env."""
    try:
        updates = {}
        if data.llm_api_base:
            updates["LLM_API_BASE"] = data.llm_api_base
        if data.llm_api_key:
            updates["LLM_API_KEY"] = data.llm_api_key
        if data.llm_model:
            updates["LLM_MODEL"] = data.llm_model
        update_env(updates)
        return {"success": True, "message": "LLM config saved."}
    except Exception as e:
        logger.exception("Failed to save LLM config")
        return {"success": False, "message": str(e)}


@router.post("/setup/slack")
async def setup_slack(data: SlackSetup):
    """Save Slack webhook URL to .env."""
    try:
        update_env({"SLACK_WEBHOOK_URL": data.slack_webhook_url or ""})
        return {"success": True, "message": "Slack config saved."}
    except Exception as e:
        logger.exception("Failed to save Slack config")
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Test endpoints
# ---------------------------------------------------------------------------

@router.post("/test/github")
async def test_github():
    """Test GitHub connection with current credentials."""
    from config import settings as s
    try:
        token = s.github_token
        if not token:
            return {"success": False, "message": "No GitHub token configured."}

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "message": f"Authenticated as {data.get('login', 'unknown')}",
                    "username": data.get("login"),
                }
            else:
                return {
                    "success": False,
                    "message": f"GitHub API returned {resp.status_code}: {resp.text[:200]}",
                }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/test/llm")
async def test_llm():
    """Test LLM connection with a trivial prompt."""
    from config import settings as s
    try:
        start = time.time()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{s.llm_api_base.rstrip('/')}/chat/completions",
                json={
                    "model": s.llm_model,
                    "messages": [{"role": "user", "content": "Say hello in one word."}],
                    "max_tokens": 10,
                },
                headers={
                    "Authorization": f"Bearer {s.llm_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            elapsed = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": f"LLM responded in {elapsed}ms",
                    "model": s.llm_model,
                    "response_time_ms": elapsed,
                }
            else:
                return {
                    "success": False,
                    "message": f"LLM returned {resp.status_code}: {resp.text[:200]}",
                }
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/test/slack")
async def test_slack():
    """Test Slack webhook by sending a test message."""
    from config import settings as s
    try:
        if not s.slack_webhook_url:
            return {"success": False, "message": "No Slack webhook URL configured."}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                s.slack_webhook_url,
                json={"text": "GitMax test message — Slack integration is working!"},
                timeout=10,
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Test message sent to Slack."}
            else:
                return {
                    "success": False,
                    "message": f"Slack returned {resp.status_code}: {resp.text[:200]}",
                }
    except Exception as e:
        return {"success": False, "message": str(e)}


# ---------------------------------------------------------------------------
# Activity feed
# ---------------------------------------------------------------------------

@router.get("/activity")
async def activity():
    """Return recent webhook activity and aggregate stats."""
    return {
        "events": get_recent(limit=30),
        "stats": get_stats(),
    }
