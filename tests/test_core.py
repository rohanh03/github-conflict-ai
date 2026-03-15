#mar15 unit tests for core modules: models, auth, verify, summarizer, detector, events
"""
Unit tests for github-conflict-ai core functionality.
Run with: pytest tests/test_core.py -v
"""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.conflict.models import ConflictReport, MergeConflict
from app.notifications.github_comments import format_conflict_comment
from app.webhooks.verify import verify_signature


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TestModels:
    """Test Pydantic data models."""

    def test_merge_conflict_creation(self):
        c = MergeConflict(
            file_path="src/auth.py",
            conflict_type="merge",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            description="Textual merge conflict in src/auth.py",
            severity="high",
        )
        assert c.file_path == "src/auth.py"
        assert c.conflict_type == "merge"
        assert c.severity == "high"
        assert c.suggested_fix is None

    def test_merge_conflict_with_suggested_fix(self):
        c = MergeConflict(
            file_path="src/config.py",
            conflict_type="semantic",
            branch_a="origin/feature-a",
            branch_b="origin/feature-b",
            description="Both branches modify DB timeout",
            severity="medium",
            suggested_fix="Consolidate timeout values in config",
        )
        assert c.suggested_fix == "Consolidate timeout values in config"

    def test_conflict_report_creation(self):
        conflict = MergeConflict(
            file_path="src/auth.py",
            conflict_type="merge",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            description="Merge conflict",
            severity="high",
        )
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[conflict],
            summary="Found 1 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=150,
        )
        assert report.repo_full_name == "owner/repo"
        assert len(report.conflicts) == 1
        assert report.scan_duration_ms == 150

    def test_conflict_report_empty(self):
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[],
            summary="No conflicts",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=50,
        )
        assert len(report.conflicts) == 0


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------

class TestVerifySignature:
    """Test HMAC-SHA256 webhook signature verification."""

    def test_valid_signature(self):
        secret = "test-secret"
        payload = b'{"action": "opened"}'
        sig = "sha256=" + hmac.new(
            secret.encode(), payload, hashlib.sha256
        ).hexdigest()
        assert verify_signature(payload, sig, secret) is True

    def test_invalid_signature(self):
        assert verify_signature(b"payload", "sha256=bad", "secret") is False

    def test_empty_signature(self):
        assert verify_signature(b"payload", "", "secret") is False

    def test_empty_secret(self):
        assert verify_signature(b"payload", "sha256=abc", "") is False


# ---------------------------------------------------------------------------
# GitHub comment formatting
# ---------------------------------------------------------------------------

class TestFormatConflictComment:
    """Test markdown comment formatting for conflict reports."""

    def test_merge_conflict_format(self):
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[
                MergeConflict(
                    file_path="src/auth.py",
                    conflict_type="merge",
                    branch_a="origin/feature-a",
                    branch_b="origin/main",
                    description="Textual merge conflict in src/auth.py",
                    severity="high",
                ),
            ],
            summary="Found 1 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=100,
        )
        comment = format_conflict_comment(report)
        assert "## Conflict Alert" in comment
        assert "src/auth.py" in comment
        assert "Merge Conflicts" in comment
        assert "1 files" in comment

    def test_semantic_conflict_format(self):
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/feature-b",
            conflicts=[
                MergeConflict(
                    file_path="src/config.py",
                    conflict_type="semantic",
                    branch_a="origin/feature-a",
                    branch_b="origin/feature-b",
                    description="Both branches change timeout default",
                    severity="medium",
                    suggested_fix="Use a shared config constant",
                ),
            ],
            summary="Found 1 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=200,
        )
        comment = format_conflict_comment(report)
        assert "Logical Conflicts" in comment
        assert "Both branches change timeout default" in comment
        assert "Suggested Fix" in comment

    def test_mixed_conflicts_format(self):
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[
                MergeConflict(
                    file_path="src/auth.py",
                    conflict_type="merge",
                    branch_a="origin/feature-a",
                    branch_b="origin/main",
                    description="Merge conflict",
                    severity="high",
                ),
                MergeConflict(
                    file_path="src/config.py",
                    conflict_type="semantic",
                    branch_a="origin/feature-a",
                    branch_b="origin/main",
                    description="Semantic conflict",
                    severity="low",
                ),
            ],
            summary="Found 2 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=300,
        )
        comment = format_conflict_comment(report)
        assert "Merge Conflicts" in comment
        assert "Logical Conflicts" in comment
        assert "2 potential conflict(s)" in comment


# ---------------------------------------------------------------------------
# PR summary conflict section formatting
# ---------------------------------------------------------------------------

class TestFormatConflictSection:
    """Test the conflict section added to PR summary comments."""

    def test_no_reports(self):
        from app.pr_summarizer.summarizer import _format_conflict_section
        assert _format_conflict_section(None) == ""
        assert _format_conflict_section([]) == ""

    def test_no_conflicts_found(self):
        from app.pr_summarizer.summarizer import _format_conflict_section
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[],
            summary="No conflicts",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=50,
        )
        result = _format_conflict_section([report])
        assert "None detected" in result

    def test_with_conflicts(self):
        from app.pr_summarizer.summarizer import _format_conflict_section
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=[
                MergeConflict(
                    file_path="src/auth.py",
                    conflict_type="merge",
                    branch_a="origin/feature-a",
                    branch_b="origin/main",
                    description="Merge conflict",
                    severity="high",
                ),
                MergeConflict(
                    file_path="src/db.py",
                    conflict_type="semantic",
                    branch_a="origin/feature-a",
                    branch_b="origin/main",
                    description="Semantic conflict",
                    severity="medium",
                ),
            ],
            summary="Found 2 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=200,
        )
        result = _format_conflict_section([report])
        assert "Cross-Branch Conflicts" in result
        assert "**`main`**" in result
        assert "1 merge" in result
        assert "1 semantic" in result
        assert "1 high severity" in result
        assert "`src/auth.py`" in result
        assert "`src/db.py`" in result

    def test_truncates_files_over_five(self):
        from app.pr_summarizer.summarizer import _format_conflict_section
        conflicts = [
            MergeConflict(
                file_path=f"src/file{i}.py",
                conflict_type="merge",
                branch_a="origin/feature-a",
                branch_b="origin/main",
                description=f"Conflict in file{i}",
                severity="high",
            )
            for i in range(7)
        ]
        report = ConflictReport(
            repo_full_name="owner/repo",
            branch_a="origin/feature-a",
            branch_b="origin/main",
            conflicts=conflicts,
            summary="Found 7 conflict(s)",
            timestamp=datetime.now(timezone.utc),
            scan_duration_ms=500,
        )
        result = _format_conflict_section([report])
        assert "and 2 more" in result


# ---------------------------------------------------------------------------
# Semantic conflict LLM parsing
# ---------------------------------------------------------------------------

class TestSemanticConflicts:
    """Test LLM response parsing in semantic conflict detection."""

    @pytest.mark.asyncio
    async def test_parse_valid_json_response(self):
        from app.conflict.semantic import detect_semantic_conflicts

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = json.dumps({
            "conflicts": [
                {
                    "file_path": "src/auth.py",
                    "description": "Both branches modify auth flow",
                    "severity": "high",
                    "suggested_fix": "Coordinate auth changes",
                }
            ]
        })

        result = await detect_semantic_conflicts(
            mock_llm, "branch-a", "branch-b", "diff a", "diff b"
        )
        assert len(result) == 1
        assert result[0].file_path == "src/auth.py"
        assert result[0].conflict_type == "semantic"

    @pytest.mark.asyncio
    async def test_parse_json_in_markdown_block(self):
        from app.conflict.semantic import detect_semantic_conflicts

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = (
            "Here are the conflicts:\n```json\n"
            '{"conflicts": [{"file_path": "x.py", "description": "test", "severity": "low"}]}'
            "\n```"
        )

        result = await detect_semantic_conflicts(
            mock_llm, "a", "b", "diff a", "diff b"
        )
        assert len(result) == 1
        assert result[0].file_path == "x.py"

    @pytest.mark.asyncio
    async def test_handles_invalid_json_gracefully(self):
        from app.conflict.semantic import detect_semantic_conflicts

        mock_llm = AsyncMock()
        mock_llm.complete.return_value = "This is not JSON at all"

        result = await detect_semantic_conflicts(
            mock_llm, "a", "b", "diff a", "diff b"
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_handles_llm_exception_gracefully(self):
        from app.conflict.semantic import detect_semantic_conflicts

        mock_llm = AsyncMock()
        mock_llm.complete.side_effect = RuntimeError("LLM down")

        result = await detect_semantic_conflicts(
            mock_llm, "a", "b", "diff a", "diff b"
        )
        assert result == []


# ---------------------------------------------------------------------------
# Git ops utilities
# ---------------------------------------------------------------------------

class TestTruncateDiff:
    """Test diff truncation utility."""

    def test_short_diff_unchanged(self):
        from app.utils.git_ops import truncate_diff
        diff = "line1\nline2\nline3"
        assert truncate_diff(diff, max_lines=10) == diff

    def test_long_diff_truncated(self):
        from app.utils.git_ops import truncate_diff
        diff = "\n".join(f"line{i}" for i in range(100))
        result = truncate_diff(diff, max_lines=10)
        lines = result.splitlines()
        assert len(lines) == 11  # 10 lines + truncation notice
        assert "TRUNCATED" in lines[-1]
        assert "90 lines omitted" in lines[-1]


# ---------------------------------------------------------------------------
# Event dispatch
# ---------------------------------------------------------------------------

class TestDispatchEvent:
    """Test webhook event routing logic."""

    @pytest.mark.asyncio
    @patch("app.webhooks.events.get_installation_token", new_callable=AsyncMock)
    @patch("app.webhooks.events.on_pr_summarize", new_callable=AsyncMock)
    @patch("app.webhooks.events.on_pr", new_callable=AsyncMock)
    async def test_pr_opened_dispatches_correctly(self, mock_on_pr, mock_summarize, mock_token):
        from app.webhooks.events import dispatch_event

        mock_on_pr.return_value = []
        mock_token.return_value = "fake-token"

        payload = {"action": "opened", "pull_request": {"number": 1}}
        await dispatch_event("pull_request", payload, installation_id=123)

        mock_token.assert_called_once_with(123)
        mock_on_pr.assert_called_once_with(payload, "fake-token")
        mock_summarize.assert_called_once_with(payload, conflict_reports=[])

    @pytest.mark.asyncio
    @patch("app.webhooks.events.get_installation_token", new_callable=AsyncMock)
    @patch("app.webhooks.events.on_push", new_callable=AsyncMock)
    async def test_push_dispatches_correctly(self, mock_on_push, mock_token):
        from app.webhooks.events import dispatch_event

        mock_token.return_value = "fake-token"

        payload = {"ref": "refs/heads/main"}
        await dispatch_event("push", payload, installation_id=123)

        mock_on_push.assert_called_once_with(payload, "fake-token")

    @pytest.mark.asyncio
    @patch("app.webhooks.events.get_installation_token", new_callable=AsyncMock)
    @patch("app.webhooks.events.on_pr", new_callable=AsyncMock)
    async def test_issue_comment_mention_dispatches(self, mock_on_pr, mock_token):
        from app.webhooks.events import dispatch_event

        mock_on_pr.return_value = []
        mock_token.return_value = "fake-token"

        payload = {
            "action": "created",
            "comment": {"body": "Hey @conflict-ai please check"},
            "issue": {"pull_request": {"url": "https://api.github.com/..."}},
        }
        await dispatch_event("issue_comment", payload, installation_id=123)

        mock_on_pr.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_event_ignored(self):
        from app.webhooks.events import dispatch_event
        # Should not raise
        await dispatch_event("ping", {"zen": "hello"})


# ---------------------------------------------------------------------------
# GitHub App JWT auth
# ---------------------------------------------------------------------------

class TestGitHubAppAuth:
    """Test JWT generation and validation."""

    @patch("app.github_client.github_app_auth.settings")
    def test_generate_jwt_missing_app_id_raises(self, mock_settings):
        from app.github_client.github_app_auth import generate_app_jwt
        mock_settings.github_app_id = 0
        mock_settings.github_private_key_path = "/some/path"
        with pytest.raises(RuntimeError, match="GITHUB_APP_ID"):
            generate_app_jwt()

    @patch("app.github_client.github_app_auth.settings")
    def test_generate_jwt_missing_key_path_raises(self, mock_settings):
        from app.github_client.github_app_auth import generate_app_jwt
        mock_settings.github_app_id = 12345
        mock_settings.github_private_key_path = ""
        with pytest.raises(RuntimeError, match="GITHUB_PRIVATE_KEY_PATH"):
            generate_app_jwt()


# ---------------------------------------------------------------------------
# OpenAI compat client defaults
# ---------------------------------------------------------------------------

class TestOpenAICompatClient:
    """Test LLM client fallback behavior."""

    def test_fallback_when_no_api_key(self):
        from app.llm.openai_compat import OpenAICompatClient
        client = OpenAICompatClient()
        assert "huggingface" in client.api_base
        assert client.api_key == "test"

    def test_fallback_when_api_key_but_no_base(self):
        from app.llm.openai_compat import OpenAICompatClient
        client = OpenAICompatClient(api_key="real-key")
        # Should not crash — api_base defaults to hackathon URL
        assert client.api_base is not None
        assert client.api_key == "real-key"

    def test_custom_values_used(self):
        from app.llm.openai_compat import OpenAICompatClient
        client = OpenAICompatClient(
            api_base="https://custom.api/v1",
            api_key="my-key",
            model="gpt-4",
        )
        assert client.api_base == "https://custom.api/v1"
        assert client.api_key == "my-key"
        assert client.model == "gpt-4"
