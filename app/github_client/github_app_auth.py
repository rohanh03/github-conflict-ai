import jwt
import time
import httpx
from pathlib import Path
import os


def generate_app_jwt():
    app_id = os.getenv("GITHUB_APP_ID")
    private_key_path = os.getenv("GITHUB_PRIVATE_KEY_PATH")

    #mar15 validate env vars before use to avoid TypeError on Path(None)
    if not app_id:
        raise RuntimeError("GITHUB_APP_ID environment variable is not set")
    if not private_key_path:
        raise RuntimeError("GITHUB_PRIVATE_KEY_PATH environment variable is not set")

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
        #mar15 moved raise_for_status inside async with block so response is still valid
        resp.raise_for_status()
        return resp.json()["token"]
