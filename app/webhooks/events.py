import logging
from typing import Optional  #mar15 Python 3.9 compat

from app.api.activity_log import log_event  #mar15 wire activity logging for dashboard
from app.conflict.detector import on_push, on_pr
from app.pr_summarizer.summarizer import on_pr_summarize
from app.github_client.github_app_auth import get_installation_token

logger = logging.getLogger(__name__)


async def dispatch_event(event_type: str, payload: dict, installation_id: Optional[int] = None) -> None:
    """Route GitHub webhook events to the appropriate handler."""
    action = payload.get("action", "")
    logger.info("Dispatching event=%s action=%s", event_type, action)

    try:
        token = None
        if installation_id:
            token = await get_installation_token(installation_id)

        #mar15 extract repo name for activity logging
        repo = payload.get("repository", {}).get("full_name", "")

        if event_type == "push":
            await on_push(payload, token)
            #mar15 log push event to activity feed
            log_event(event_type="push", repo=repo, action="push")

        elif event_type == "pull_request" and action in (
            "opened",
            "synchronize",
            "reopened",
        ):
            #mar15 capture conflict reports from on_pr and pass to summarizer
            conflict_reports = await on_pr(payload, token)
            await on_pr_summarize(payload, token=token, conflict_reports=conflict_reports)
            #mar15 log PR event with conflict count to activity feed
            pr_num = payload.get("pull_request", {}).get("number")
            n_conflicts = sum(len(r.conflicts) for r in (conflict_reports or []))
            log_event(
                event_type="pull_request",
                repo=repo,
                pr_number=pr_num,
                action=action,
                conflicts_found=n_conflicts,
            )

        elif event_type == "issue_comment" and action == "created":
            body = payload.get("comment", {}).get("body", "")
            if "@conflict-ai" in body.lower():
                # On-demand re-analysis triggered by mention
                if "pull_request" in payload.get("issue", {}):
                    await on_pr(payload, token)
                logger.info("On-demand analysis triggered via comment")
                #mar15 log comment-triggered analysis
                log_event(event_type="issue_comment", repo=repo, action="mention")

        else:
            logger.debug("Ignoring event=%s action=%s", event_type, action)

    except Exception:
        logger.exception("Error handling event=%s action=%s", event_type, action)
