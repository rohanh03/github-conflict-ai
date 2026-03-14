import logging

from app.conflict.detector import on_push, on_pr
from app.pr_summarizer.summarizer import on_pr_summarize

logger = logging.getLogger(__name__)


async def dispatch_event(event_type: str, payload: dict) -> None:
    """Route GitHub webhook events to the appropriate handler."""
    action = payload.get("action", "")
    logger.info("Dispatching event=%s action=%s", event_type, action)

    try:
        if event_type == "push":
            await on_push(payload)

        elif event_type == "pull_request" and action in (
            "opened",
            "synchronize",
            "reopened",
        ):
            await on_pr(payload)
            await on_pr_summarize(payload)

        elif event_type == "issue_comment" and action == "created":
            body = payload.get("comment", {}).get("body", "")
            if "@conflict-ai" in body.lower():
                # On-demand re-analysis triggered by mention
                if "pull_request" in payload.get("issue", {}):
                    await on_pr(payload)
                logger.info("On-demand analysis triggered via comment")

        else:
            logger.debug("Ignoring event=%s action=%s", event_type, action)

    except Exception:
        logger.exception("Error handling event=%s action=%s", event_type, action)
