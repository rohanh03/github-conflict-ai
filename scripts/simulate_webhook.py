#!/usr/bin/env python3
"""
Simulate GitHub webhook events for local testing.
Usage:
    python scripts/simulate_webhook.py push
    python scripts/simulate_webhook.py pull_request
"""

import hashlib
import hmac
import json
#mar15 moved os import to top with other stdlib imports
import os
import sys
import subprocess

import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

SERVER_URL = "http://localhost:8000/webhooks/github"
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

# GitHub repo info
REPO_FULL_NAME = "rohanh03/github-conflict-ai"
REPO_CLONE_URL = f"https://github.com/{REPO_FULL_NAME}.git"
LOCAL_REPO_PATH = Path(__file__).parent.parent  # assumes script is in repo folder
INSTALLATION_ID = int(os.getenv("GITHUB_APP_INSTALLATION_ID", "123456"))


def get_latest_sha(branch: str) -> str:
    """Get the latest commit SHA for a branch in the local git repo."""
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", branch], cwd=LOCAL_REPO_PATH
        )
        return output.decode().strip()
    except subprocess.CalledProcessError:
        print(f"Error: Could not find branch '{branch}' in local repo")
        sys.exit(1)


# Automatically get SHAs
LATEST_SHA = get_latest_sha("feature-test-comment")  # branch you are testing
#mar15 removed redundant MAIN_LATEST_SHA (identical to PREVIOUS_SHA)
MAIN_SHA = get_latest_sha("main")

PUSH_PAYLOAD = {
    #mar15 removed unnecessary f-string (no interpolation)
    "ref": "refs/heads/feature-test-comment",
    "before": MAIN_SHA,
    "after": LATEST_SHA,
    "repository": {
        "full_name": REPO_FULL_NAME,
        "clone_url": REPO_CLONE_URL,
    },
    "installation": {"id": INSTALLATION_ID},
    "pusher": {"name": "alessandroiucci"},
    "commits": [
        {
            "id": LATEST_SHA,
            "message": "Test bot commenting",
            "author": {"name": "alessandroiucci"},
        }
    ],
}

PR_PAYLOAD = {
    "action": "opened",
    "number": 1,
    "pull_request": {
        "number": 1,
        "title": "Test PR for bot",
        "user": {"login": "alessandroiucci"},
        "head": {"ref": "feature-test-comment", "sha": LATEST_SHA},
        "base": {"ref": "main", "sha": MAIN_SHA},
        "body": "Testing bot comments on PR.",
    },
    "repository": {
        "full_name": REPO_FULL_NAME,
        "clone_url": REPO_CLONE_URL,
    },
    "installation": {"id": INSTALLATION_ID},
}

PAYLOADS = {
    "push": PUSH_PAYLOAD,
    "pull_request": PR_PAYLOAD,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PAYLOADS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(PAYLOADS.keys())}>")
        sys.exit(1)

    event_type = sys.argv[1]
    payload = PAYLOADS[event_type]
    body = json.dumps(payload).encode()

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": event_type,
    }

    # Sign the payload if a secret is configured
    if WEBHOOK_SECRET:
        sig = "sha256=" + hmac.new(
            WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        headers["X-Hub-Signature-256"] = sig

    print(f"Sending {event_type} event to {SERVER_URL}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        resp = httpx.post(SERVER_URL, content=body, headers=headers)
        print(f"\nResponse [{resp.status_code}]: {resp.json()}")
    except httpx.ConnectError:
        print(f"\nError: Could not connect to {SERVER_URL}")
        print("Make sure the server is running: uvicorn main:app --reload")
        sys.exit(1)


if __name__ == "__main__":
    main()
