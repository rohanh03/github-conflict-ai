import logging

from app.conflict.detector import on_push, on_pr
from app.pr_summarizer.summarizer import on_pr_summarize
from app.github_client.github_app_auth import get_installation_token

logger = logging.getLogger(__name__)


async def dispatch_event(event_type: str, payload: dict, installation_id: int | None = None) -> None:
    """Route GitHub webhook events to the appropriate handler."""
    action = payload.get("action", "")
    logger.info("Dispatching event=%s action=%s", event_type, action)

    try:
        token = None
        if installation_id:
            token = await get_installation_token(installation_id)

        if event_type == "push":
            await on_push(payload, token)

        elif event_type == "pull_request" and action in (
            "opened",
            "synchronize",
            "reopened",
        ):
            #mar15 capture conflict reports from on_pr and pass to summarizer
            conflict_reports = await on_pr(payload, token)
            await on_pr_summarize(payload, conflict_reports=conflict_reports)

        elif event_type == "issue_comment" and action == "created":
            body = payload.get("comment", {}).get("body", "")
            if "@conflict-ai" in body.lower():
                # On-demand re-analysis triggered by mention
                if "pull_request" in payload.get("issue", {}):
                    await on_pr(payload, token)
                logger.info("On-demand analysis triggered via comment")

        else:
            logger.debug("Ignoring event=%s action=%s", event_type, action)

    except Exception:
        logger.exception("Error handling event=%s action=%s", event_type, action)
