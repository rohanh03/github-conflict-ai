#mar15 utility to read/write .env file and reload pydantic settings
"""
Utility to update .env file key-value pairs and reload the global settings.
"""

import os
from pathlib import Path


#mar15 resolve .env path relative to project root
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
ENV_EXAMPLE_PATH = ENV_PATH.parent / ".env.example"


def _read_env_lines() -> list[str]:
    """Read existing .env or bootstrap from .env.example."""
    if ENV_PATH.exists():
        return ENV_PATH.read_text().splitlines()
    if ENV_EXAMPLE_PATH.exists():
        return ENV_EXAMPLE_PATH.read_text().splitlines()
    return []


def update_env(updates: dict[str, str]) -> None:
    """
    Update .env file with the given key=value pairs.
    Existing keys are replaced in-place; new keys are appended.
    After writing, the global settings singleton is reloaded.
    """
    lines = _read_env_lines()
    keys_written = set()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        #mar15 skip blank/comment lines as-is
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        #mar15 parse KEY=VALUE, replace if key is in updates
        if "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                keys_written.add(key)
                continue

        new_lines.append(line)

    #mar15 append any keys not already in the file
    for key, value in updates.items():
        if key not in keys_written:
            new_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n")

    #mar15 reload the global settings singleton after writing
    _reload_settings()


def _reload_settings() -> None:
    """Re-instantiate Settings and replace the module-level singleton."""
    import config
    config.settings = config.Settings()
