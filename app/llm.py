import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
)
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# max_retries=0: retries are handled by tenacity below, otherwise they would multiply
client = AsyncOpenAI(
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    timeout=60,
    max_retries=0,
)


def _is_retryable(e: BaseException) -> bool:
    if isinstance(e, (RateLimitError, APIConnectionError)):  # 429, network, timeout
        return True
    return isinstance(e, APIStatusError) and e.status_code >= 500


def friendly_error(e: Exception) -> str:
    if isinstance(e, RateLimitError):
        return "Rate limit exceeded, please wait a minute"
    if isinstance(e, AuthenticationError):
        return "Invalid API key"
    if isinstance(e, APIConnectionError):
        return "Could not reach the model"
    return "Model error"


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def complete(messages: list[dict], tools: list[dict] | None = None):
    """One non-streaming model call. Pass tools=None to forbid tool use."""
    kwargs = {"model": settings.llm_model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return await client.chat.completions.create(**kwargs)