from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from app.conflict.models import ConflictReport, MergeConflict
from app.conflict.semantic import detect_semantic_conflicts
from app.github_client.client import (
    ensure_repo_cloned,
    get_open_prs,
    get_repo,
    post_comment,
)
from app.llm.openai_compat import OpenAICompatClient
from app.notifications.github_comments import format_conflict_comment
from app.notifications.slack import send_slack_conflict_alert
from app.utils import git_ops
from config import settings

logger = logging.getLogger(__name__)


def _get_llm() -> OpenAICompatClient:
    return OpenAICompatClient(
        api_base=settings.llm_api_base,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


async def _detect_conflicts_between(
    repo_path: str,
    branch_a: str,
    branch_b: str,
    repo_full_name: str,
) -> ConflictReport:
    """Run full conflict detection (merge + semantic) between two branches."""
    start = time.time()
    all_conflicts: list[MergeConflict] = []

    # Phase 1: textual merge conflicts via git merge-tree
    base = None
    try:
        mt_result = await git_ops.merge_tree(repo_path, branch_a, branch_b)

        if mt_result.has_conflicts:
            for fpath in mt_result.conflicting_files:
                all_conflicts.append(
                    MergeConflict(
                        file_path=fpath,
                        conflict_type="merge",
                        branch_a=branch_a,
                        branch_b=branch_b,
                        description=f"Textual merge conflict in {fpath}",
                        severity="high",
                    )
                )
            logger.info(
                "Found %d merge conflicts between %s and %s",
                len(mt_result.conflicting_files),
                branch_a,
                branch_b,
            )
    except Exception:
        logger.exception("merge-tree failed for %s vs %s", branch_a, branch_b)
        base = None

    # Phase 2: semantic conflicts via LLM
    try:
        if base is None:
            base = await git_ops.merge_base(repo_path, branch_a, branch_b)

        diff_a = await git_ops.diff(repo_path, base, branch_a)
        diff_b = await git_ops.diff(repo_path, base, branch_b)

        if diff_a.strip() and diff_b.strip():
            llm = _get_llm()
            semantic = await detect_semantic_conflicts(
                llm,
                branch_a,
                branch_b,
                diff_a,
                diff_b,
                max_diff_lines=settings.max_diff_lines,
            )
            all_conflicts.extend(semantic)
    except Exception:
        logger.exception("Semantic analysis failed for %s vs %s", branch_a, branch_b)

    elapsed_ms = int((time.time() - start) * 1000)

    summary = (
        f"Found {len(all_conflicts)} conflict(s) between "
        f"`{branch_a}` and `{branch_b}`."
    )

    return ConflictReport(
        repo_full_name=repo_full_name,
        branch_a=branch_a,
        branch_b=branch_b,
        conflicts=all_conflicts,
        summary=summary,
        timestamp=datetime.now(timezone.utc),
        scan_duration_ms=elapsed_ms,
    )


async def _notify(
    report: ConflictReport,
    pr_number: int | None = None,
    token: str | None = None,
) -> None:
    """Send conflict report via GitHub comment and Slack."""
    if not report.conflicts:
        logger.info("No conflicts found — skipping notifications")
        return

    repo = get_repo(report.repo_full_name, token)
    comment_body = format_conflict_comment(report)

    if pr_number:
        post_comment(repo, pr_number, comment_body)

    await send_slack_conflict_alert(report)


async def on_push(payload: dict, token: str | None = None) -> None:
    #mar15 TODO: thread token through to get_repo/post_comment for GitHub App auth
    """Handle a push event — compare pushed branch against open PR branches."""
    ref = payload.get("ref", "")
    if not ref.startswith("refs/heads/"):
        return
    pushed_branch = ref.replace("refs/heads/", "")
    repo_full_name = payload["repository"]["full_name"]

    logger.info("Push to %s on %s — running conflict scan", pushed_branch, repo_full_name)

    repo = get_repo(repo_full_name, token)
    repo_path = await ensure_repo_cloned(repo)

    # Compare against open PR branches
    open_prs = get_open_prs(repo)
    for pr in open_prs:
        pr_branch = pr.head.ref
        if pr_branch == pushed_branch:
            continue  # Don't compare branch with itself

        report = await _detect_conflicts_between(
            repo_path,
            f"origin/{pushed_branch}",
            f"origin/{pr_branch}",
            repo_full_name,
        )

        if report.conflicts:
            await _notify(report, pr_number=pr.number, token=token)


#mar15 changed return type to list[ConflictReport] so callers can use conflict data
async def on_pr(payload: dict, token: str | None = None) -> list[ConflictReport]:
    #mar15 TODO: thread token through to get_repo/post_comment for GitHub App auth
    """Handle a pull_request event — compare PR branch against base and other PRs."""
    #mar15 collect all conflict reports to return to caller
    all_reports: list[ConflictReport] = []

    pr_data = payload.get("pull_request", {})
    if not pr_data:
        # Handle issue_comment trigger (on-demand via @conflict-ai)
        issue = payload.get("issue", {})
        pr_url = issue.get("pull_request", {}).get("url")
        if not pr_url:
            return all_reports
        repo_full_name = payload["repository"]["full_name"]
        repo = get_repo(repo_full_name, token)
        pr_number = issue["number"]
        pr_obj = repo.get_pull(pr_number)
        head_branch = pr_obj.head.ref
        base_branch = pr_obj.base.ref
    else:
        repo_full_name = payload["repository"]["full_name"]
        pr_number = pr_data["number"]
        head_branch = pr_data["head"]["ref"]
        base_branch = pr_data["base"]["ref"]

    logger.info(
        "PR #%d on %s: %s → %s — running conflict scan",
        pr_number,
        repo_full_name,
        head_branch,
        base_branch,
    )

    repo = get_repo(repo_full_name, token)
    repo_path = await ensure_repo_cloned(repo)

    # Compare PR branch against base
    report = await _detect_conflicts_between(
        repo_path,
        f"origin/{head_branch}",
        f"origin/{base_branch}",
        repo_full_name,
    )
    all_reports.append(report)
    if report.conflicts:
        await _notify(report, pr_number=pr_number, token=token)

    # Also compare against other open PRs targeting the same base
    open_prs = get_open_prs(repo)
    for other_pr in open_prs:
        if other_pr.number == pr_number:
            continue
        if other_pr.base.ref != base_branch:
            continue

        report = await _detect_conflicts_between(
            repo_path,
            f"origin/{head_branch}",
            f"origin/{other_pr.head.ref}",
            repo_full_name,
        )
        all_reports.append(report)
        if report.conflicts:
            await _notify(report, pr_number=pr_number, token=token)

    return all_reports
