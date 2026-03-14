from typing import Protocol


class LLMClient(Protocol):
    """Abstract interface for LLM completions."""

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str: ...
