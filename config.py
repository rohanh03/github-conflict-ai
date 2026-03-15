from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # GitHub App
    github_app_id: int = 0
    github_private_key_path: str = ""
    github_webhook_secret: str = ""
    github_app_installation_id: int | None = None
    github_token: str = ""  # Fallback: personal access token

    # LLM
    #mar15 default to hackathon GPT-OSS server so app works out of the box
    llm_api_base: str = "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1"
    llm_api_key: str = "test"
    llm_model: str = "openai/gpt-oss-120b"

    # Slack
    slack_webhook_url: str = ""  # Optional — empty = disabled

    # Local
    repo_clone_dir: str = "/tmp/conflict-ai-repos"
    log_level: str = "INFO"
    max_diff_lines: int = 4000  # Truncation limit for LLM input

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
