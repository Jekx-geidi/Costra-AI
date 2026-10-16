import httpx
from fastapi import HTTPException, status
from app.config import settings
from app.services.assistant.guard import strip_reasoning

# The hosted endpoint returns occasional transient 500s; one retry hides them.
RETRIES_ON_SERVER_ERROR = 1


def ensure_enabled() -> None:
    if not settings.assistant_enabled or not settings.nvidia_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The COSTRA assistant is not configured",
        )


async def chat_completion(
    messages: list[dict],
    *,
    model: str | None = None,
    max_tokens: int = 900,
    temperature: float = 0.1,
) -> str:
    """Call an OpenAI-compatible /chat/completions endpoint and return the reply text."""
    ensure_enabled()
    payload = {
        "model": model or settings.assistant_model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.assistant_timeout_seconds) as client:
            for attempt in range(1 + RETRIES_ON_SERVER_ERROR):
                response = await client.post(
                    f"{settings.assistant_base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.nvidia_api_key}"},
                    json=payload,
                )
                if response.status_code < 500:
                    break
    except httpx.TimeoutException:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="The assistant took too long to answer")
    except httpx.HTTPError:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="The assistant service is unreachable")

    if response.status_code != 200:
        # Never forward the provider's body: it can echo request details.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The assistant service returned an error ({response.status_code})",
        )

    choice = response.json()["choices"][0]
    return strip_reasoning(choice["message"].get("content") or "")
