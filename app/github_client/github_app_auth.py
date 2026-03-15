import jwt
import time
import httpx
from pathlib import Path
import os


def generate_app_jwt():
    app_id = os.getenv("GITHUB_APP_ID")
    private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")

    private_key = Path(private_key_path).read_text()

    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
        "iss": app_id,
    }

    return jwt.encode(payload, private_key, algorithm="RS256")


async def get_installation_token(installation_id: int):
    jwt_token = generate_app_jwt()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Accept": "application/vnd.github+json",
            },
        )

    resp.raise_for_status()
    return resp.json()["token"]