from app.conflict.models import ConflictReport

SEVERITY_ICONS = {"high": "Red - High", "medium": "Yellow - Medium", "low": "Blue - Low"}


def format_conflict_comment(report: ConflictReport) -> str:
    """Format a ConflictReport as a GitHub Markdown comment."""
    merge_conflicts = [c for c in report.conflicts if c.conflict_type == "merge"]
    semantic_conflicts = [c for c in report.conflicts if c.conflict_type == "semantic"]

    lines = [
        f"## Conflict Alert\n",
        f"Branch `{report.branch_a}` has **{len(report.conflicts)} potential "
        f"conflict(s)** with `{report.branch_b}`:\n",
    ]

    # Merge conflicts table
    if merge_conflicts:
        lines.append(f"### Merge Conflicts ({len(merge_conflicts)} files)")
        lines.append("| File | Severity | Description |")
        lines.append("|------|----------|-------------|")
        for c in merge_conflicts:
            sev = SEVERITY_ICONS.get(c.severity, c.severity)
            lines.append(f"| `{c.file_path}` | {sev} | {c.description} |")
        lines.append("")

    # Semantic conflicts
    if semantic_conflicts:
        lines.append(f"### Logical Conflicts ({len(semantic_conflicts)} detected)")
        for c in semantic_conflicts:
            lines.append(f"> **{c.description}**\n")
            if c.suggested_fix:
                lines.append("<details>")
                lines.append("<summary>Suggested Fix</summary>\n")
                lines.append(f"{c.suggested_fix}\n")
                lines.append("</details>\n")

    lines.append("---")
    lines.append(
        f"*Scan completed in {report.scan_duration_ms}ms · "
        f"Detected by [github-conflict-ai]*"
    )

    return "\n".join(lines)
