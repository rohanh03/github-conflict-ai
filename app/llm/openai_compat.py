import logging
import os
import httpx

logger = logging.getLogger(__name__)

class OpenAICompatClient:
    """LLM client compatible with any OpenAI-style chat completions API."""

    def __init__(self, api_base: str = None, api_key: str = None, model: str = "openai/gpt-oss-120b"):
        # Use hackathon server if no key is provided
        hackathon_base = "https://vjioo4r1vyvcozuj.us-east-2.aws.endpoints.huggingface.cloud/v1"
        if not api_key:
            logger.info("No OPENAI_API_KEY found. Using hackathon GPT-OSS server with dummy key.")
            api_base = hackathon_base
            api_key = "test"

        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.http = httpx.AsyncClient(timeout=90.0)

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        logger.info("LLM request: model=%s, prompt_len=%d", self.model, len(user_prompt))
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
        content = resp.json()["choices"][0]["message"]["content"]
        logger.info("LLM response: %d chars", len(content))
        return content