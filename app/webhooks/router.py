import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.webhooks.events import dispatch_event
from app.webhooks.verify import verify_signature
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive GitHub webhook events."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if settings.github_webhook_secret:
        if not verify_signature(body, signature, settings.github_webhook_secret):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    repo_name = payload.get("repository", {}).get("full_name", "unknown")

    #mar15 guard against installation being None (not just missing) to avoid AttributeError
    installation = payload.get("installation") or {}
    installation_id = installation.get("id")

    logger.info(
        "Webhook received: event=%s repo=%s installation=%s",
        event_type,
        repo_name,
        installation_id,
    )

    background_tasks.add_task(
        dispatch_event,
        event_type,
        payload,
        installation_id,
    )

    return {"status": "accepted"}
