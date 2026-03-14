CONFLICT_ANALYSIS_SYSTEM = """\
You are a code conflict detection expert. Given two sets of changes (diffs) \
made to the same codebase on different branches, identify potential logical \
conflicts where:

- One branch modifies a function signature that the other branch calls
- One branch deletes or renames something the other branch uses
- Both branches modify the same logical behavior in incompatible ways
- One branch changes a config/constant that the other branch depends on
- Import changes that would break the other branch

For each conflict found, respond with a JSON array of objects:
{
  "conflicts": [
    {
      "file_path": "path/to/file.py",
      "severity": "high" | "medium" | "low",
      "description": "Clear explanation of the logical conflict",
      "suggested_fix": "Concrete suggestion for resolving the conflict"
    }
  ]
}

If no logical conflicts exist, return: {"conflicts": []}
Be precise and avoid false positives. Only flag genuine logical conflicts."""

CONFLICT_ANALYSIS_USER = """\
## Branch A: `{branch_a}`
Changes from merge base:
```diff
{diff_a}
```

## Branch B: `{branch_b}`
Changes from merge base:
```diff
{diff_b}
```

Analyze these two sets of changes for logical conflicts."""


PR_SUMMARY_SYSTEM = """\
You are a code review assistant. Given a pull request diff and metadata, \
generate a clear, concise summary for a developer audience.

Your summary must include:
1. **TLDR**: One-line summary of what this PR does
2. **Changes**: Key changes grouped by area (backend, frontend, config, tests, etc.)
3. **Reviewer Notes**: Things reviewers should pay attention to (risks, new dependencies, \
breaking changes, etc.)
4. **Complexity**: Rate as Simple / Moderate / Complex

Format your response as clean markdown. Be concise — aim for clarity, not verbosity."""

PR_SUMMARY_USER = """\
## PR #{pr_number}: {pr_title}

**Author:** {author}
**Base:** {base_branch} ← {head_branch}

### Commit Messages
{commit_messages}

### Diff ({files_changed} files, +{lines_added} / -{lines_removed})
```diff
{diff_content}
```

Generate a summary of this PR."""
