from __future__ import annotations

import logging
import os

from github import Auth, Github, GithubIntegration
from github.PullRequest import PullRequest
from github.Repository import Repository

from app.utils.git_ops import clone_or_fetch
from config import settings

logger = logging.getLogger(__name__)

_github_client: Github | None = None


def get_github() -> Github:
    """Get an authenticated GitHub client (PAT or App installation)."""
    global _github_client
    if _github_client is not None:
        return _github_client

    if settings.github_token:
        logger.info("Authenticating with personal access token")
        _github_client = Github(auth=Auth.Token(settings.github_token))
    elif settings.github_app_id and settings.github_private_key_path:
        logger.info("Authenticating as GitHub App %d", settings.github_app_id)
        with open(settings.github_private_key_path) as f:
            private_key = f.read()
        auth = Auth.AppAuth(settings.github_app_id, private_key)
        gi = GithubIntegration(auth=auth)
        # Use first installation (hackathon simplification)
        installations = list(gi.get_installations())
        if not installations:
            raise RuntimeError("No GitHub App installations found")
        _github_client = installations[0].get_github_for_installation()
    else:
        raise RuntimeError(
            "No GitHub credentials configured. Set GITHUB_TOKEN or "
            "GITHUB_APP_ID + GITHUB_PRIVATE_KEY_PATH in .env"
        )
    return _github_client


def get_repo(full_name: str) -> Repository:
    """Get a repository object by full name (owner/repo)."""
    return get_github().get_repo(full_name)


def get_open_prs(repo: Repository) -> list[PullRequest]:
    """Get all open pull requests for a repo."""
    return list(repo.get_pulls(state="open"))


def post_comment(repo: Repository, issue_number: int, body: str) -> None:
    """Post a comment on a PR or issue."""
    issue = repo.get_issue(issue_number)
    issue.create_comment(body)
    logger.info("Posted comment on %s#%d", repo.full_name, issue_number)


def get_pr_diff(repo: Repository, pr_number: int) -> str:
    """Get the diff content for a pull request."""
    pr = repo.get_pull(pr_number)
    files = pr.get_files()
    diff_parts = []
    for f in files:
        diff_parts.append(f"--- a/{f.filename}")
        diff_parts.append(f"+++ b/{f.filename}")
        if f.patch:
            diff_parts.append(f.patch)
        diff_parts.append("")
    return "\n".join(diff_parts)


def get_pr_commits(repo: Repository, pr_number: int) -> list[str]:
    """Get commit messages for a PR."""
    pr = repo.get_pull(pr_number)
    return [c.commit.message for c in pr.get_commits()]


async def ensure_repo_cloned(repo: Repository) -> str:
    """Clone or fetch the repo to local disk. Returns the local path."""
    repo_path = os.path.join(settings.repo_clone_dir, repo.full_name)
    clone_url = repo.clone_url
    # Inject token into clone URL for private repos
    if settings.github_token:
        clone_url = clone_url.replace(
            "https://", f"https://x-access-token:{settings.github_token}@"
        )
    return await clone_or_fetch(clone_url, repo_path)
