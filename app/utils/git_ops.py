from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


async def _run(cmd: list[str], cwd: str | None = None) -> GitResult:
    """Run a git command asynchronously and return the result."""
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    result = GitResult(
        returncode=proc.returncode or 0,
        stdout=stdout_bytes.decode(errors="replace"),
        stderr=stderr_bytes.decode(errors="replace"),
    )
    if not result.ok:
        logger.debug("Command failed (rc=%d): %s", result.returncode, result.stderr)
    return result


async def clone_or_fetch(clone_url: str, repo_path: str) -> str:
    """Clone a repo or fetch updates if it already exists. Returns repo_path."""
    if os.path.isdir(os.path.join(repo_path, ".git")):
        await _run(["git", "fetch", "--all", "--prune"], cwd=repo_path)
    else:
        os.makedirs(repo_path, exist_ok=True)
        #mar15 removed --depth=50 so all remote branch refs are available for merge-base
        result = await _run(
            ["git", "clone", clone_url, repo_path]
        )
        if not result.ok:
            raise RuntimeError(f"git clone failed: {result.stderr}")
        #mar15 fetch all remote branches so origin/<branch> refs resolve correctly
        await _run(["git", "fetch", "--all"], cwd=repo_path)
    return repo_path


async def merge_base(repo_path: str, branch_a: str, branch_b: str) -> str:
    """Find the merge base (common ancestor) of two branches."""
    result = await _run(
        ["git", "merge-base", branch_a, branch_b], cwd=repo_path
    )
    if not result.ok:
        raise RuntimeError(f"git merge-base failed: {result.stderr}")
    return result.stdout.strip()


@dataclass
class MergeTreeResult:
    has_conflicts: bool
    stdout: str
    conflicting_files: list[str]


async def merge_tree(
    repo_path: str, branch_a: str, branch_b: str
) -> MergeTreeResult:
    """
    Use git merge-tree to detect merge conflicts without modifying the working tree.
    Requires git 2.38+. Takes two branches (merge base is computed automatically).
    """
    result = await _run(
        ["git", "merge-tree", "--write-tree", branch_a, branch_b],
        cwd=repo_path,
    )
    has_conflicts = result.returncode != 0
    conflicting_files = []
    if has_conflicts:
        # Parse conflict markers from stdout
        for line in result.stdout.splitlines():
            # merge-tree outputs "CONFLICT (content): Merge conflict in <file>"
            if "CONFLICT" in line and "Merge conflict in" in line:
                parts = line.split("Merge conflict in ")
                if len(parts) > 1:
                    conflicting_files.append(parts[1].strip())
    return MergeTreeResult(
        has_conflicts=has_conflicts,
        stdout=result.stdout,
        conflicting_files=conflicting_files,
    )


async def diff(repo_path: str, ref_a: str, ref_b: str) -> str:
    """Get the diff between two refs."""
    result = await _run(
        ["git", "diff", f"{ref_a}...{ref_b}"], cwd=repo_path
    )
    return result.stdout


async def diff_stat(repo_path: str, ref_a: str, ref_b: str) -> str:
    """Get the diff --stat between two refs."""
    result = await _run(
        ["git", "diff", "--stat", f"{ref_a}...{ref_b}"], cwd=repo_path
    )
    return result.stdout


async def log(repo_path: str, branch: str, n: int = 20) -> str:
    """Get recent commit log for a branch."""
    result = await _run(
        ["git", "log", "--oneline", f"-{n}", branch], cwd=repo_path
    )
    return result.stdout


async def branch_list(repo_path: str) -> list[str]:
    """List remote branches."""
    result = await _run(["git", "branch", "-r"], cwd=repo_path)
    branches = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if name and "->" not in name:  # skip HEAD -> origin/main
            branches.append(name)
    return branches


def truncate_diff(diff_text: str, max_lines: int = 4000) -> str:
    """Truncate a diff to max_lines, keeping the most important parts."""
    lines = diff_text.splitlines()
    if len(lines) <= max_lines:
        return diff_text
    # Keep first max_lines lines with a truncation notice
    truncated = lines[:max_lines]
    truncated.append(
        f"\n... [TRUNCATED: {len(lines) - max_lines} lines omitted] ..."
    )
    return "\n".join(truncated)
