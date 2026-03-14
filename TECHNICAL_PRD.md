# Technical PRD: github-conflict-ai

> **Product Name**: github-conflict-ai
> **Type**: AI-powered GitHub App
> **Timeline**: 12-hour hackathon
> **Date**: 2026-03-14
> **Repo Location**: `~/Desktop/github-conflict-ai`

---

## 1. Problem Statement

### The Pain
When multiple developers work on the same codebase across branches, they often don't discover conflicts until merge time — sometimes days or weeks after the conflicting code was written. This leads to:
- **Painful merge conflicts** that take hours to untangle
- **Silent logical conflicts** where code merges cleanly but breaks at runtime (e.g., one branch renames a function another branch calls)
- **Wasted time in meetings** reviewing what PRs do, when an AI could summarize them instantly
- **Junior developers** struggle most — they lack the experience to anticipate conflicts or quickly understand teammates' PRs

### The Solution
An AI-powered GitHub App that:
1. **Proactively detects conflicts** between branches before merge time and notifies developers with fix suggestions
2. **Auto-summarizes PRs** in plain English so anyone can understand what changed without reading every line of code

---

## 2. Target Users

| Persona | Needs |
|---------|-------|
| **Junior developers** | Early warning when their code will conflict; plain-English explanations of teammate PRs |
| **Small teams (2–8 devs)** | Reduce status meetings; automated awareness of what everyone is working on |
| **Team leads** | Quick PR overviews without reading diffs; visibility into cross-branch risks |
| **Open source maintainers** | Auto-summarize external contributor PRs; catch conflicts across parallel feature branches |

---

## 3. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.11+ / FastAPI | Fast to prototype, async-native, great for webhooks |
| **GitHub Integration** | PyGithub + raw webhook handling | PyGithub for API calls; raw webhooks for event ingestion |
| **LLM** | `gpt-oss-120b` via OpenAI-compatible API | Abstracted via interface — any model can be swapped via env config |
| **Notifications** | GitHub PR comments + Slack incoming webhooks | Two channels: in-context (GitHub) + real-time alert (Slack) |
| **Git Operations** | Local git CLI (via `asyncio.create_subprocess_exec`) | `git merge-tree` for conflict detection, `git diff` for analysis |
| **Config** | pydantic-settings + `.env` | Type-safe config, easy to change per environment |

### Dependencies
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
PyGithub>=2.1.0
httpx>=0.25.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

---

## 4. System Architecture

### 4.1 High-Level Flow

```
GitHub Repo
    │
    ├── push event ──────────────┐
    ├── pull_request event ──────┤
    │                            ▼
    │                   ┌─────────────────┐
    │                   │  FastAPI Server  │
    │                   │  /webhooks/github│
    │                   └────────┬────────┘
    │                            │
    │               ┌────────────┼────────────┐
    │               ▼            ▼             ▼
    │     ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │     │   Conflict    │ │    PR    │ │   Webhook    │
    │     │  Detector     │ │Summarizer│ │   Verify     │
    │     └──────┬───────┘ └────┬─────┘ └──────────────┘
    │            │              │
    │     ┌──────┴──────┐      │
    │     ▼             ▼      ▼
    │  ┌────────┐  ┌────────────────┐
    │  │git CLI │  │  LLM Client    │
    │  │merge-  │  │ (gpt-oss-120b) │
    │  │tree,   │  └───────┬────────┘
    │  │diff    │          │
    │  └────────┘          ▼
    │              ┌───────────────┐
    │              │ Notifications │
    │              ├───────┬───────┤
    │              │GitHub │ Slack │
    │              │Comment│ Msg   │
    │              └───────┴───────┘
    │                      │
    └──────────────────────┘  (comments posted back to repo)
```

### 4.2 Project Structure

```
github-conflict-ai/
├── main.py                        # FastAPI app, mounts routers, startup events
├── config.py                      # Settings class (pydantic-settings from .env)
├── requirements.txt
├── .env.example                   # Template with all required env vars
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── webhooks/
│   │   ├── __init__.py
│   │   ├── router.py              # POST /webhooks/github — receives all GitHub events
│   │   ├── verify.py              # HMAC-SHA256 signature verification
│   │   └── events.py              # Routes events to correct handler by type+action
│   ├── conflict/
│   │   ├── __init__.py
│   │   ├── detector.py            # Core conflict detection engine
│   │   ├── semantic.py            # LLM-powered semantic/logical conflict analysis
│   │   └── models.py              # Pydantic: ConflictReport, MergeConflict, BranchPair
│   ├── pr_summarizer/
│   │   ├── __init__.py
│   │   ├── summarizer.py          # Fetches PR diff, generates LLM summary
│   │   └── models.py              # Pydantic: PRSummary
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                # LLMClient Protocol (abstract interface)
│   │   ├── openai_compat.py       # OpenAI-compatible HTTP client via httpx
│   │   └── prompts.py             # All system/user prompt templates
│   ├── github_client/
│   │   ├── __init__.py
│   │   └── client.py              # PyGithub wrapper: auth, clone, branches, comments
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── github_comments.py     # Format ConflictReport/PRSummary → Markdown, post
│   │   └── slack.py               # Format → Slack Block Kit, post via webhook
│   └── utils/
│       ├── __init__.py
│       └── git_ops.py             # Async wrappers: merge-tree, diff, merge-base, log
├── scripts/
│   ├── setup_test_repo.sh         # Creates a local test repo with conflicting branches
│   └── simulate_webhook.py        # Sends fake webhook payloads to local server
└── tests/
    ├── __init__.py
    └── fixtures/                  # Sample webhook payloads, diff outputs
        ├── push_event.json
        ├── pr_event.json
        └── sample_diff.txt
```

---

## 5. Feature Specifications

### 5.1 Feature 1: Branch Conflict Detection (Primary)

#### User Story
> As a developer working on a feature branch, I want to be automatically notified when my commits create conflicts with other active branches, so I can resolve them early instead of at merge time.

#### Trigger Events
| GitHub Event | Action | Behavior |
|---|---|---|
| `push` | any | Compare pushed branch against all open PR branches + main |
| `pull_request` | `opened`, `synchronize`, `reopened` | Compare PR branch against base branch + other open PR branches |

#### Conflict Detection Algorithm

**Phase 1 — Textual Merge Conflicts (git-level)**
```
1. Clone/fetch repo to local disk (shallow, --depth=50)
2. For each (pushed_branch, target_branch) pair:
   a. Find merge base: git merge-base pushed_branch target_branch
   b. Run: git merge-tree --write-tree <base> <pushed> <target>
   c. Exit code 1 = conflicts exist → parse conflict markers from stdout
   d. Extract: conflicting file paths, conflicting hunks
```

**Phase 2 — Semantic/Logical Conflicts (LLM-powered)**
```
1. Get diff from merge-base to each branch tip:
   - diff_a = git diff <base>...<pushed_branch>
   - diff_b = git diff <base>...<target_branch>
2. Truncate diffs to ~4000 lines (prioritize: function signatures, imports, configs)
3. Send to LLM with structured prompt requesting JSON output
4. LLM identifies:
   - Functions renamed/deleted that the other branch calls
   - Incompatible behavioral changes to shared logic
   - Config/constant changes with downstream impact
5. Parse response into MergeConflict objects with conflict_type="semantic"
```

**Phase 3 — Fix Suggestions**
```
1. For each conflict (textual or semantic), send the specific conflicting code to LLM
2. LLM generates a concrete fix suggestion
3. Attach to the ConflictReport
```

#### Data Models
```python
class MergeConflict(BaseModel):
    file_path: str
    conflict_type: Literal["merge", "semantic"]
    branch_a: str
    branch_b: str
    description: str
    severity: Literal["high", "medium", "low"]
    suggested_fix: str | None = None
    lines_affected: tuple[int, int] | None = None

class ConflictReport(BaseModel):
    repo_full_name: str
    branch_a: str
    branch_b: str
    conflicts: list[MergeConflict]
    summary: str                    # LLM-generated overall summary
    timestamp: datetime
    scan_duration_ms: int
```

#### Notification Output

**GitHub PR Comment Format:**
```markdown
## ⚠️ Conflict Alert

Branch `feature-auth` has **3 potential conflicts** with `feature-payments`:

### Merge Conflicts (2 files)
| File | Severity | Description |
|------|----------|-------------|
| `src/api/users.py` | 🔴 High | Both branches modify the `create_user` function |
| `config/settings.py` | 🟡 Medium | Conflicting database config changes |

### Logical Conflicts (1 detected)
> **`feature-auth` renames `validate_token()` → `verify_token()` in `auth.py`,
> but `feature-payments` adds a new call to `validate_token()` in `payment_processor.py`**

<details>
<summary>💡 Suggested Fix</summary>

In `feature-payments`, update `payment_processor.py` line 42:
```python
# Change this:
token = validate_token(request.headers["Authorization"])
# To this:
token = verify_token(request.headers["Authorization"])
```
</details>

---
*🤖 Detected by [github-conflict-ai]*
```

**Slack Message:** Block Kit with header, conflict count, severity badges, and link to the PR comment.

---

### 5.2 Feature 2: Smart PR Summarizer (Secondary)

#### User Story
> As a team member, I want every PR to have an auto-generated plain-English summary so I can quickly understand what it does without reading the entire diff.

#### Trigger Events
| GitHub Event | Action | Behavior |
|---|---|---|
| `pull_request` | `opened`, `synchronize` | Fetch diff, generate summary, post as comment |

#### Summarization Algorithm
```
1. Fetch PR metadata: title, description, author, labels
2. Fetch full diff via GitHub API (or local git diff base...head)
3. Fetch commit messages in the PR
4. Build context payload:
   - File change summary (files added/modified/deleted, lines +/-)
   - Diff content (truncated to ~3000 lines if large)
   - Commit messages
5. Send to LLM with PR_SUMMARY prompt
6. Parse structured response
7. Post as PR comment (or update PR description body if empty)
```

#### LLM Prompt Strategy
```
System: You are a code review assistant. Given a PR diff and metadata,
generate a clear, concise summary for a developer audience. Include:
1. One-line TLDR of what this PR does
2. Key changes grouped by area (backend, frontend, config, tests, etc.)
3. Notable decisions or patterns (e.g., "uses async instead of sync")
4. Potential risks or things reviewers should focus on
5. Complexity rating: Simple / Moderate / Complex

Output as structured markdown.
```

#### Data Models
```python
class PRSummary(BaseModel):
    pr_number: int
    repo_full_name: str
    tldr: str                       # One-line summary
    changes_by_area: dict[str, list[str]]  # e.g. {"Backend": ["Added /users endpoint"]}
    reviewer_notes: list[str]       # Things to watch out for
    complexity: Literal["simple", "moderate", "complex"]
    files_changed: int
    lines_added: int
    lines_removed: int
```

#### Output Format
```markdown
## 📋 PR Summary

**TLDR:** Adds user authentication middleware and JWT token validation.

### Changes
- **Backend:** Added auth middleware in `src/middleware/auth.py`, new `/login` and `/logout` endpoints
- **Config:** Added `JWT_SECRET` and `TOKEN_EXPIRY` to environment config
- **Tests:** 4 new test cases for token validation edge cases

### Reviewer Notes
- ⚠️ `JWT_SECRET` must be set in production env — no default fallback
- Uses `PyJWT` library (new dependency)

**Complexity:** Moderate · 6 files changed · +182 / -12

---
*🤖 Generated by [github-conflict-ai]*
```

---

## 6. LLM Integration Layer

### Architecture
```python
# base.py — abstract interface
class LLMClient(Protocol):
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str: ...

# openai_compat.py — implementation
class OpenAICompatClient:
    """Works with any OpenAI-compatible API endpoint."""
    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.http = httpx.AsyncClient(timeout=60.0)

    async def complete(self, system_prompt, user_prompt, temperature=0.3, max_tokens=2000):
        resp = await self.http.post(
            f"{self.api_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

### Configuration
```bash
# .env
LLM_API_BASE=https://api.example.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-oss-120b
```

To swap models: change these 3 env vars. No code changes needed.

### Prompt Templates (in `prompts.py`)
| Prompt | Used by | Purpose |
|--------|---------|---------|
| `CONFLICT_ANALYSIS_SYSTEM` | `semantic.py` | Detect logical conflicts from two diffs |
| `CONFLICT_FIX_SYSTEM` | `semantic.py` | Generate concrete fix suggestions |
| `PR_SUMMARY_SYSTEM` | `summarizer.py` | Summarize a PR diff in plain English |

---

## 7. GitHub Integration

### Authentication
- **GitHub App** with installation token flow (preferred for hackathon demo)
- **Fallback**: Personal Access Token (simpler setup, works for single-repo demo)

### Webhook Configuration
Subscribe to: `push`, `pull_request`, `issue_comment`

### Webhook Processing
```python
@router.post("/webhooks/github")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    # 1. Verify HMAC signature
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(body, sig, settings.github_webhook_secret):
        raise HTTPException(401)

    # 2. Dispatch to background (GitHub expects 200 within 10s)
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    background_tasks.add_task(dispatch_event, event, payload)
    return {"status": "accepted"}
```

### Event Dispatch Table
| Event | Action | Handler |
|-------|--------|---------|
| `push` | * | `conflict.detector.on_push()` |
| `pull_request` | `opened`, `synchronize`, `reopened` | `conflict.detector.on_pr()` + `pr_summarizer.summarizer.on_pr()` |
| `issue_comment` | `created` (body contains `@conflict-ai`) | On-demand re-analysis |

---

## 8. Configuration

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # GitHub App
    github_app_id: int = 0
    github_private_key_path: str = ""
    github_webhook_secret: str = ""
    github_token: str = ""              # Fallback: personal access token

    # LLM
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-oss-120b"

    # Slack
    slack_webhook_url: str = ""         # Optional — empty = disabled

    # Local
    repo_clone_dir: str = "/tmp/conflict-ai-repos"
    log_level: str = "INFO"
    max_diff_lines: int = 4000          # Truncation limit for LLM input

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

---

## 9. Git Operations Module

All git operations run via `asyncio.create_subprocess_exec` for non-blocking execution.

| Function | Git Command | Purpose |
|----------|------------|---------|
| `clone_or_fetch(url, path)` | `git clone --depth=50` / `git fetch --all` | Get repo locally |
| `merge_base(path, a, b)` | `git merge-base a b` | Find common ancestor |
| `merge_tree(path, base, a, b)` | `git merge-tree --write-tree base a b` | Detect textual conflicts (git 2.38+) |
| `diff(path, a, b)` | `git diff a...b` | Get diff between branches |
| `log(path, branch, n=20)` | `git log --oneline -n branch` | Recent commits |
| `branch_list(path)` | `git branch -r` | List remote branches |

---

## 10. Build Schedule (12 Hours)

| Phase | Hours | Deliverables | Exit Criteria |
|-------|-------|-------------|---------------|
| **Scaffold** | 0–1 | Project structure, `main.py`, `config.py`, `requirements.txt`, `.env.example`, health check | `uvicorn main:app` runs, `GET /health` → 200 |
| **GitHub Core** | 1–3 | Webhook endpoint, signature verification, `github_client`, `git_ops`, test repo script | Webhook received and verified, repo cloned, `git merge-tree` runs |
| **Conflict Engine** | 3–5 | `detector.py`, merge-tree output parsing, `ConflictReport` models | Push to test repo → merge conflicts detected and logged |
| **LLM Integration** | 5–7 | `openai_compat.py`, all prompts, `semantic.py` | Semantic conflicts detected, fix suggestions generated |
| **Notifications** | 7–9 | GitHub comment formatting + posting, Slack message formatting + posting | End-to-end: push → detect → PR comment + Slack alert |
| **PR Summarizer** | 9–10 | `summarizer.py`, PR summary prompt, wire to PR webhook | Open PR → summary comment auto-posted |
| **Polish** | 10–11 | Error handling, logging, README with setup instructions, demo script | App handles edge cases gracefully |
| **Demo** | 11–12 | Live demo run-through, backup recording | Demo works reliably |

---

## 11. Demo Strategy

### Test Repository
`scripts/setup_test_repo.sh` creates a small Python project with:
- **`main` branch**: Flask API with `app.py`, `models.py`, `utils.py`
- **`feature-auth` branch**: Adds auth middleware, **renames** `validate_token()` → `verify_token()` in `utils.py`
- **`feature-payments` branch**: Adds payment routes, **calls** `validate_token()` in `payment_processor.py`

This guarantees:
- A **textual merge conflict** in `app.py` (both branches modify it)
- A **semantic conflict** (renamed function that the other branch still calls)

### Demo Script (5 minutes)
1. Show the test repo on GitHub — two branches, looks fine
2. Push a commit to `feature-auth`
3. Show terminal — webhook received, conflict scan running
4. Switch to GitHub — PR comment appears with conflict report + fix suggestion
5. Show Slack — alert received
6. Open a new PR for `feature-payments`
7. Show the auto-generated PR summary comment

### Fallback Plan
- `scripts/simulate_webhook.py` sends realistic webhook payloads to the local server
- Works without GitHub App auth — just needs the server running
- Pre-record a backup demo video

---

## 12. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| GitHub App auth is complex to set up | Support personal access token as fallback; `simulate_webhook.py` for demo |
| LLM latency makes webhooks timeout | Process all events in `BackgroundTasks`; return 200 immediately |
| Very large diffs overwhelm the LLM | Truncate to `max_diff_lines` (4000); prioritize function signatures + imports |
| `git merge-tree` not available (git < 2.38) | Fall back to `git merge --no-commit` then `git merge --abort` |
| Rate limiting on GitHub API or LLM | Cache results per branch-pair; skip re-analysis if no new commits |
| Slack webhook not configured | Graceful no-op — check if `slack_webhook_url` is set before posting |

---

## 13. Future Enhancements (Post-Hackathon)

- **Web dashboard**: Visualize conflict history, PR summaries, team activity
- **AI code review**: Go beyond summarization to flag bugs, security issues, style problems
- **Auto-label and triage**: Automatically label PRs/issues and suggest reviewers
- **IDE extension**: Show conflict warnings directly in VS Code
- **Monorepo support**: Track conflicts per package/service in a monorepo
- **Persistent storage**: Database for conflict history, analytics, trends
- **Multi-repo**: Monitor conflicts across related repositories

---

## 14. Verification Checklist

1. `uvicorn main:app --reload` starts successfully
2. `GET /health` returns `{"status": "ok"}`
3. `scripts/setup_test_repo.sh` creates test repo with conflicting branches
4. `scripts/simulate_webhook.py` sends push event → server processes it
5. Conflict detector finds textual conflicts via `git merge-tree`
6. LLM identifies semantic conflicts (renamed function)
7. Fix suggestions are generated
8. GitHub PR comment is posted with formatted conflict report
9. Slack notification is sent
10. Opening a PR triggers the Smart PR Summarizer
11. PR summary comment is posted with TLDR, changes by area, and complexity
