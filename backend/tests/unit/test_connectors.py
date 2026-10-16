"""Provider sync connectors, exercised against mocked provider HTTP APIs."""
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select

from app.config import settings
from app.models.billing_account import BillingAccount
from app.models.billing_record import BillingRecord
from app.services.ingestion import anthropic_connector, openai_connector
from app.services.ingestion.anthropic_connector import AnthropicConnector
from app.services.ingestion.openai_connector import OpenAIConnector


def mock_http(monkeypatch, module, handler):
    """Route the connector module's httpx.AsyncClient through a MockTransport."""
    real_client = httpx.AsyncClient
    seen: list[httpx.Request] = []

    def recording(request):
        seen.append(request)
        return handler(request)

    def client_factory(*args, **kwargs):
        return real_client(*args, transport=httpx.MockTransport(recording), **kwargs)

    monkeypatch.setattr(module.httpx, "AsyncClient", client_factory)
    return seen


async def no_sleep(_seconds):
    return None


async def record_count(db) -> int:
    return (await db.execute(select(func.count()).select_from(BillingRecord))).scalar_one()


async def add_account(db, provider: str) -> BillingAccount:
    account = BillingAccount(
        provider=provider, account_reference=f"org-{provider}", account_name=f"Geidi {provider}",
        ownership_type="geidi", collection_method="api", authorization_status="authorized",
    )
    db.add(account)
    await db.commit()
    return account


# --- capability gates -------------------------------------------------------

async def test_sync_endpoint_reports_disabled_capability(client, auth, monkeypatch):
    monkeypatch.setattr(settings, "openai_billing_enabled", False)
    res = await client.post("/api/ai-billing/sync/openai", json={}, headers=auth["billing_admin"])
    assert res.status_code == 200
    body = res.json()
    assert body["capability_status"] == "disabled"
    assert body["status"] == "blocked"
    assert body["records_processed"] == 0


async def test_viewer_cannot_trigger_sync(client, auth):
    for role in ("viewer", "finance_reviewer"):
        res = await client.post("/api/ai-billing/sync/anthropic", json={}, headers=auth[role])
        assert res.status_code == 403, role


async def test_enabled_without_key_or_account_is_blocked(db, monkeypatch):
    monkeypatch.setattr(settings, "openai_billing_enabled", True)
    monkeypatch.setattr(settings, "openai_admin_api_key", "")
    run = await OpenAIConnector(db).sync()
    assert (run.capability_status, run.status) == ("blocked", "blocked")

    monkeypatch.setattr(settings, "openai_admin_api_key", "sk-admin-test")
    run = await OpenAIConnector(db).sync()  # key but no Geidi OpenAI account
    assert (run.capability_status, run.status) == ("blocked", "blocked")


# --- OpenAI -------------------------------------------------------------------

OPENAI_PAGES = {
    None: {"data": [{"id": "cost_1", "amount": {"value": "12.345678", "currency": "usd"}, "project_id": "proj_a"}],
           "next_page": "cursor_2"},
    "cursor_2": {"data": [{"id": "cost_2", "amount": {"value": "0.000001", "currency": "usd"}, "project_id": "proj_b"}],
          "next_page": None},
}


@pytest.fixture
def openai_enabled(monkeypatch):
    monkeypatch.setattr(settings, "openai_billing_enabled", True)
    monkeypatch.setattr(settings, "openai_admin_api_key", "sk-admin-test")
    monkeypatch.setattr(settings, "openai_org_id", "org-test")


async def test_openai_sync_pages_and_is_idempotent(db, monkeypatch, openai_enabled):
    await add_account(db, "openai")
    requests = mock_http(monkeypatch, openai_connector,
                         lambda req: httpx.Response(200, json=OPENAI_PAGES[req.url.params.get("page")]))

    run = await OpenAIConnector(db).sync(period_start=date(2026, 9, 1), period_end=date(2026, 9, 30))
    await db.commit()
    assert (run.status, run.capability_status, run.records_processed) == ("completed", "enabled", 2)
    assert run.error_summary is None
    amounts = (await db.execute(select(BillingRecord.amount).order_by(BillingRecord.amount))).scalars().all()
    assert amounts == [Decimal("0.000001"), Decimal("12.345678")]

    first = requests[0]
    assert first.headers["Authorization"] == "Bearer sk-admin-test"
    assert first.headers["OpenAI-Organization"] == "org-test"
    expected_start = int(datetime(2026, 9, 1, tzinfo=timezone.utc).timestamp())
    assert first.url.params["start_time"] == str(expected_start)
    assert len(requests) == 2
    assert requests[1].url.params["page"] == "cursor_2"
    assert requests[1].url.params["start_time"] == str(expected_start)  # filters kept on later pages

    rerun = await OpenAIConnector(db).sync(period_start=date(2026, 9, 1), period_end=date(2026, 9, 30))
    await db.commit()
    assert rerun.status == "completed"
    assert await record_count(db) == 2  # same rows, no duplicates


async def test_openai_persistent_rate_limit_fails_instead_of_succeeding(db, monkeypatch, openai_enabled):
    await add_account(db, "openai")
    monkeypatch.setattr(openai_connector.asyncio, "sleep", no_sleep)
    requests = mock_http(monkeypatch, openai_connector, lambda req: httpx.Response(429, json={"error": "rate limited"}))

    run = await OpenAIConnector(db).sync()
    assert run.status == "failed"
    assert run.capability_status == "error"
    assert len(requests) == openai_connector.MAX_ATTEMPTS
    assert await record_count(db) == 0


async def test_openai_server_error_is_retried_then_fails(db, monkeypatch, openai_enabled):
    await add_account(db, "openai")
    monkeypatch.setattr(openai_connector.asyncio, "sleep", no_sleep)
    requests = mock_http(monkeypatch, openai_connector, lambda req: httpx.Response(500, text="boom"))
    run = await OpenAIConnector(db).sync()
    assert run.status == "failed"
    assert "500" in run.error_summary
    assert len(requests) == openai_connector.MAX_ATTEMPTS


async def test_openai_transient_error_recovers(db, monkeypatch, openai_enabled):
    await add_account(db, "openai")
    monkeypatch.setattr(openai_connector.asyncio, "sleep", no_sleep)
    responses = iter([httpx.Response(503), httpx.Response(200, json=OPENAI_PAGES["cursor_2"])])
    mock_http(monkeypatch, openai_connector, lambda req: next(responses))
    run = await OpenAIConnector(db).sync()
    assert (run.status, run.records_processed) == ("completed", 1)


async def test_client_error_is_not_retried(db, monkeypatch, openai_enabled):
    await add_account(db, "openai")
    requests = mock_http(monkeypatch, openai_connector, lambda req: httpx.Response(401, json={"error": "bad key"}))
    run = await OpenAIConnector(db).sync()
    assert run.status == "failed"
    assert len(requests) == 1


# --- Anthropic ------------------------------------------------------------------

ANTHROPIC_PAGES = {
    None: {"data": [{"id": "a1", "cost": "40.10", "currency": "USD", "workspace_id": "ws_1"}], "next_page_token": "t2"},
    "t2": {"data": [{"id": "a2", "cost": "9.90", "currency": "USD", "workspace_id": "ws_2"}], "next_page_token": None},
}


async def test_anthropic_sync_pages_and_is_idempotent(db, monkeypatch):
    monkeypatch.setattr(settings, "anthropic_billing_enabled", True)
    monkeypatch.setattr(settings, "anthropic_admin_api_key", "sk-ant-admin-test")
    monkeypatch.setattr(settings, "anthropic_org_id", "org-ant")
    await add_account(db, "anthropic")
    requests = mock_http(monkeypatch, anthropic_connector,
                         lambda req: httpx.Response(200, json=ANTHROPIC_PAGES[req.url.params.get("page_token")]))

    run = await AnthropicConnector(db).sync(period_start=date(2026, 9, 1), period_end=date(2026, 9, 30))
    await db.commit()
    assert (run.status, run.records_processed) == ("completed", 2)
    assert requests[0].url.path == "/v1/organizations/org-ant/cost_report"
    assert requests[0].headers["x-api-key"] == "sk-ant-admin-test"
    assert requests[0].url.params["start_date"] == "2026-09-01"

    total = (await db.execute(select(func.sum(BillingRecord.amount)))).scalar_one()
    assert total == Decimal("50.00")

    await AnthropicConnector(db).sync(period_start=date(2026, 9, 1), period_end=date(2026, 9, 30))
    await db.commit()
    assert await record_count(db) == 2
