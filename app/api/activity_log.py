#mar15 in-memory activity log for dashboard webhook event tracking
"""
In-memory capped activity log for recent webhook events.
Used by the dashboard to show live activity without a database.
"""

from collections import deque
from datetime import datetime, timezone
from typing import Optional

#mar15 cap at 100 entries to prevent unbounded memory growth
_activity_log: deque[dict] = deque(maxlen=100)


def log_event(
    event_type: str,
    repo: str = "",
    pr_number: Optional[int] = None,
    action: str = "",
    summary: str = "",
    conflicts_found: int = 0,
) -> None:
    """Append a webhook event to the in-memory log."""
    _activity_log.appendleft({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "repo": repo,
        "pr_number": pr_number,
        "action": action,
        "summary": summary,
        "conflicts_found": conflicts_found,
    })


def get_recent(limit: int = 20) -> list[dict]:
    """Return the most recent activity entries."""
    return list(_activity_log)[:limit]


def get_stats() -> dict:
    """Derive aggregate stats from the activity log."""
    events = list(_activity_log)
    total = len(events)
    prs = sum(1 for e in events if e["event_type"] == "pull_request")
    conflicts = sum(e.get("conflicts_found", 0) for e in events)
    return {
        "total_events": total,
        "prs_analyzed": prs,
        "conflicts_detected": conflicts,
    }
