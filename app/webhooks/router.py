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

    # Verify signature if a secret is configured
    if settings.github_webhook_secret:
        if not verify_signature(body, signature, settings.github_webhook_secret):
            logger.warning("Invalid webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    logger.info(
        "Webhook received: event=%s repo=%s",
        event_type,
        payload.get("repository", {}).get("full_name", "unknown"),
    )

    # Process in background so we return 200 within GitHub's 10s timeout
    background_tasks.add_task(dispatch_event, event_type, payload)
    return {"status": "accepted"}
