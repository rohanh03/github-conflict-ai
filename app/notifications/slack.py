import logging

import httpx

from app.conflict.models import ConflictReport
from config import settings

logger = logging.getLogger(__name__)


async def send_slack_conflict_alert(report: ConflictReport) -> None:
    """Send a conflict alert to Slack via incoming webhook."""
    if not settings.slack_webhook_url:
        logger.debug("Slack webhook not configured — skipping")
        return

    conflict_summary = "\n".join(
        f"- *{c.file_path}* ({c.severity}): {c.description}"
        for c in report.conflicts
    )

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Conflict Alert: {report.repo_full_name}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{len(report.conflicts)} conflict(s)* detected between "
                    f"`{report.branch_a}` and `{report.branch_b}`"
                ),
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": conflict_summary,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Scan completed in {report.scan_duration_ms}ms | github-conflict-ai",
                }
            ],
        },
    ]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.slack_webhook_url, json={"blocks": blocks}
            )
            resp.raise_for_status()
        logger.info("Slack conflict alert sent for %s", report.repo_full_name)
    except Exception:
        logger.exception("Failed to send Slack conflict alert")


async def send_slack_pr_summary(
    repo_full_name: str, pr_number: int, pr_title: str, summary: str
) -> None:
    """Send a PR summary notification to Slack."""
    if not settings.slack_webhook_url:
        return

    # Truncate summary for Slack (max ~3000 chars in a block)
    if len(summary) > 2500:
        summary = summary[:2500] + "\n...(truncated)"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"PR Summary: {repo_full_name}#{pr_number}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{pr_title}*\n\n{summary}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "github-conflict-ai",
                }
            ],
        },
    ]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.slack_webhook_url, json={"blocks": blocks}
            )
            resp.raise_for_status()
        logger.info("Slack PR summary sent for %s#%d", repo_full_name, pr_number)
    except Exception:
        logger.exception("Failed to send Slack PR summary")
