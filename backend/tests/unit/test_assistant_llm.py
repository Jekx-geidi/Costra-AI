import httpx
import pytest
from fastapi import HTTPException

from app.config import settings
from app.services.assistant import llm


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(settings, "assistant_enabled", True)
    monkeypatch.setattr(settings, "nvidia_api_key", "nvapi-secret")
    monkeypatch.setattr(settings, "assistant_model", "test/model")


def mock_api(monkeypatch, *responses):
    """Serve the given responses (or exceptions) in order; return the recorded requests."""
    queue, seen = list(responses), []
    real_client = httpx.AsyncClient

    def handler(request):
        seen.append(request)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(llm.httpx, "AsyncClient",
                        lambda *a, **kw: real_client(*a, transport=httpx.MockTransport(handler), **kw))
    return seen


def ok(content):
    return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": content}}]})


async def test_success_sends_model_and_key_and_strips_reasoning(monkeypatch):
    seen = mock_api(monkeypatch, ok("<think>scratch</think>Ang total kay 10.00 USD."))
    reply = await llm.chat_completion([{"role": "user", "content": "hi"}], max_tokens=50)
    assert reply == "Ang total kay 10.00 USD."
    assert seen[0].headers["Authorization"] == "Bearer nvapi-secret"
    assert b'"model":"test/model"' in seen[0].content.replace(b" ", b"")
    assert b'"max_tokens":50' in seen[0].content.replace(b" ", b"")


async def test_one_retry_on_server_error(monkeypatch):
    seen = mock_api(monkeypatch, httpx.Response(500), ok("fine"))
    assert await llm.chat_completion([{"role": "user", "content": "hi"}]) == "fine"
    assert len(seen) == 2


async def test_provider_error_body_is_never_forwarded(monkeypatch):
    mock_api(monkeypatch, httpx.Response(401, text="invalid key nvapi-secret for org X"))
    with pytest.raises(HTTPException) as err:
        await llm.chat_completion([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 502
    assert "nvapi" not in err.value.detail and "org X" not in err.value.detail


async def test_timeout_is_504(monkeypatch):
    mock_api(monkeypatch, httpx.ReadTimeout("slow"))
    with pytest.raises(HTTPException) as err:
        await llm.chat_completion([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 504


async def test_network_error_is_502(monkeypatch):
    mock_api(monkeypatch, httpx.ConnectError("down"))
    with pytest.raises(HTTPException) as err:
        await llm.chat_completion([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 502


async def test_not_configured(monkeypatch):
    monkeypatch.setattr(settings, "nvidia_api_key", "")
    with pytest.raises(HTTPException) as err:
        await llm.chat_completion([{"role": "user", "content": "hi"}])
    assert err.value.status_code == 503
