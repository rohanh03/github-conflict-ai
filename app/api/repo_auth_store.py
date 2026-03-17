"""
Lightweight SQLite storage for repository-scoped GitHub PAT mappings.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "gitmax.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS repo_auth (
            repo_full_name TEXT PRIMARY KEY,
            github_token TEXT NOT NULL
        )
        """
    )
    return conn


def save_repo_token(repo_full_name: str, github_token: str) -> None:
    """Insert or update the PAT used for a specific repository."""
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO repo_auth (repo_full_name, github_token)
            VALUES (?, ?)
            ON CONFLICT(repo_full_name)
            DO UPDATE SET github_token = excluded.github_token
            """,
            (repo_full_name.strip(), github_token),
        )
        conn.commit()


def get_repo_token(repo_full_name: str) -> str | None:
    """Return the PAT configured for a repo, if one exists."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT github_token FROM repo_auth WHERE repo_full_name = ?",
            (repo_full_name.strip(),),
        ).fetchone()
    return row[0] if row else None


def has_repo_token(repo_full_name: str) -> bool:
    """Whether a repo-scoped PAT exists for the given repository."""
    return get_repo_token(repo_full_name) is not None
