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
import sys

import httpx

SERVER_URL = "http://localhost:8000/webhooks/github"
WEBHOOK_SECRET = ""  # Set to match your .env GITHUB_WEBHOOK_SECRET

# Sample payloads modeled after real GitHub webhook events
PUSH_PAYLOAD = {
    "ref": "refs/heads/feature-auth",
    "before": "abc123",
    "after": "def456",
    "repository": {
        "full_name": "test-org/test-repo",
        "clone_url": "https://github.com/test-org/test-repo.git",
    },
    "pusher": {"name": "developer1"},
    "commits": [
        {
            "id": "def456",
            "message": "Add auth middleware, rename validate_token to verify_token",
            "author": {"name": "developer1"},
        }
    ],
}

PR_PAYLOAD = {
    "action": "opened",
    "number": 1,
    "pull_request": {
        "number": 1,
        "title": "Add payment processing endpoints",
        "user": {"login": "developer2"},
        "head": {"ref": "feature-payments", "sha": "abc123"},
        "base": {"ref": "main", "sha": "xyz789"},
        "body": "Adds payment processing with transaction history.",
    },
    "repository": {
        "full_name": "test-org/test-repo",
        "clone_url": "https://github.com/test-org/test-repo.git",
    },
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
