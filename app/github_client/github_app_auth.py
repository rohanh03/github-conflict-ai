import jwt
import time
import httpx
from pathlib import Path

#mar15 use settings from config.py instead of os.getenv to pick up .env values via pydantic-settings
from config import settings


def generate_app_jwt():
    app_id = settings.github_app_id
    private_key_path = settings.github_private_key_path

    #mar15 validate config values before use (defaults are 0 and "")
    if not app_id:
        raise RuntimeError("GITHUB_APP_ID is not configured in .env or environment")
    if not private_key_path:
        raise RuntimeError("GITHUB_PRIVATE_KEY_PATH is not configured in .env or environment")

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
