#!/usr/bin/env bash
# Creates a local test repository with conflicting branches for demo purposes.
# Usage: ./scripts/setup_test_repo.sh [target_dir]

set -euo pipefail

TARGET_DIR="${1:-/tmp/conflict-ai-test-repo}"

echo "Creating test repo at: $TARGET_DIR"
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

git init
git checkout -b main

# --- Main branch: base project ---
cat > app.py << 'PYEOF'
from flask import Flask, jsonify, request
from utils import validate_token, get_user_by_id

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/users/<int:user_id>")
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify(user)

if __name__ == "__main__":
    app.run(debug=True)
PYEOF

cat > utils.py << 'PYEOF'
import hashlib

def validate_token(token: str) -> dict:
    """Validate a bearer token and return the decoded payload."""
    if not token or not token.startswith("Bearer "):
        raise ValueError("Invalid token format")
    raw = token.replace("Bearer ", "")
    # Simple hash-based validation for demo
    return {"user_id": int(hashlib.md5(raw.encode()).hexdigest()[:8], 16) % 10000}

def get_user_by_id(user_id: int) -> dict | None:
    """Look up a user by their ID."""
    users = {
        1: {"id": 1, "name": "Alice", "role": "admin"},
        2: {"id": 2, "name": "Bob", "role": "developer"},
        3: {"id": 3, "name": "Charlie", "role": "viewer"},
    }
    return users.get(user_id)

DATABASE_URL = "postgresql://localhost:5432/myapp"
MAX_CONNECTIONS = 10
PYEOF

cat > models.py << 'PYEOF'
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    role: str

@dataclass
class Transaction:
    id: int
    user_id: int
    amount: float
    status: str = "pending"
PYEOF

cat > requirements.txt << 'PYEOF'
flask==3.0.0
gunicorn==21.2.0
PYEOF

git add -A
git commit -m "Initial project setup with Flask API, utils, and models"

# --- Branch: feature-auth ---
git checkout -b feature-auth

# Rename validate_token -> verify_token and add middleware
cat > utils.py << 'PYEOF'
import hashlib
import time

def verify_token(token: str) -> dict:
    """Verify a bearer token and return the decoded payload.
    Renamed from validate_token for consistency with JWT terminology."""
    if not token or not token.startswith("Bearer "):
        raise ValueError("Invalid token format")
    raw = token.replace("Bearer ", "")
    return {
        "user_id": int(hashlib.md5(raw.encode()).hexdigest()[:8], 16) % 10000,
        "verified_at": time.time(),
    }

def get_user_by_id(user_id: int) -> dict | None:
    """Look up a user by their ID."""
    users = {
        1: {"id": 1, "name": "Alice", "role": "admin"},
        2: {"id": 2, "name": "Bob", "role": "developer"},
        3: {"id": 3, "name": "Charlie", "role": "viewer"},
    }
    return users.get(user_id)

DATABASE_URL = "postgresql://localhost:5432/myapp"
MAX_CONNECTIONS = 20  # Increased for auth middleware connection pool
PYEOF

# Add auth middleware to app.py
cat > app.py << 'PYEOF'
from flask import Flask, jsonify, request
from utils import verify_token, get_user_by_id
from functools import wraps

app = Flask(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "")
        try:
            payload = verify_token(token)
            request.user = payload
        except ValueError:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/users/<int:user_id>")
@require_auth
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify(user)

@app.route("/me")
@require_auth
def get_me():
    return jsonify({"user_id": request.user["user_id"]})

if __name__ == "__main__":
    app.run(debug=True)
PYEOF

git add -A
git commit -m "Add auth middleware, rename validate_token to verify_token"

# --- Branch: feature-payments ---
git checkout main
git checkout -b feature-payments

# Add payment processing that uses the OLD validate_token name
cat > payment_processor.py << 'PYEOF'
from utils import validate_token

class PaymentProcessor:
    def __init__(self):
        self.transactions = []

    def process_payment(self, token: str, amount: float) -> dict:
        """Process a payment after validating the user's token."""
        user = validate_token(token)
        transaction = {
            "user_id": user["user_id"],
            "amount": amount,
            "status": "completed",
        }
        self.transactions.append(transaction)
        return transaction

    def get_user_transactions(self, token: str) -> list:
        user = validate_token(token)
        return [t for t in self.transactions if t["user_id"] == user["user_id"]]
PYEOF

# Also modify app.py (will create a merge conflict)
cat > app.py << 'PYEOF'
from flask import Flask, jsonify, request
from utils import validate_token, get_user_by_id
from payment_processor import PaymentProcessor

app = Flask(__name__)
payments = PaymentProcessor()

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/users/<int:user_id>")
def get_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "not found"}), 404
    return jsonify(user)

@app.route("/payments", methods=["POST"])
def create_payment():
    token = request.headers.get("Authorization", "")
    amount = request.json.get("amount", 0)
    result = payments.process_payment(token, amount)
    return jsonify(result), 201

@app.route("/payments", methods=["GET"])
def list_payments():
    token = request.headers.get("Authorization", "")
    return jsonify(payments.get_user_transactions(token))

if __name__ == "__main__":
    app.run(debug=True)
PYEOF

git add -A
git commit -m "Add payment processing endpoints using validate_token"

# Back to main
git checkout main

echo ""
echo "Test repo created at: $TARGET_DIR"
echo ""
echo "Branches:"
echo "  main            - Base Flask API"
echo "  feature-auth    - Renames validate_token -> verify_token, adds auth middleware"
echo "  feature-payments - Adds payment routes using validate_token (OLD name)"
echo ""
echo "Expected conflicts:"
echo "  1. MERGE CONFLICT: app.py modified in both branches"
echo "  2. SEMANTIC CONFLICT: feature-auth renames validate_token() but"
echo "     feature-payments calls validate_token() in payment_processor.py"
