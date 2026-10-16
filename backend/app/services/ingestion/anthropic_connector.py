import asyncio
import uuid
from datetime import date, datetime, timezone
import httpx
from sqlalchemy import select
from app.config import settings
from app.models.billing_account import BillingAccount
from app.services.ingestion.base_connector import BaseConnector
from app.services.normalization import normalize_amount, normalize_currency
from app.services.deduplication import upsert_billing_record

MAX_ATTEMPTS = 3


class AnthropicConnector(BaseConnector):
    provider = "anthropic"

    async def _execute(
        self, run_id: uuid.UUID, period_start: date | None, period_end: date | None
    ) -> tuple[str, int]:
        if not settings.anthropic_billing_enabled:
            return "disabled", 0

        if not settings.anthropic_admin_api_key:
            return "blocked", 0

        account_result = await self.db.execute(
            select(BillingAccount).where(
                BillingAccount.provider == "anthropic",
                BillingAccount.is_active == True,
                BillingAccount.ownership_type == "geidi",
            )
        )
        account = account_result.scalar_one_or_none()
        if not account:
            return "blocked", 0

        headers = {
            "x-api-key": settings.anthropic_admin_api_key,
            "anthropic-version": "2023-06-01",
        }
        params: dict = {}
        if period_start:
            params["start_date"] = period_start.isoformat()
        if period_end:
            params["end_date"] = period_end.isoformat()

        records_processed = 0
        async with httpx.AsyncClient(base_url=settings.anthropic_api_base_url, timeout=30) as client:
            page_token: str | None = None
            for _ in range(20):
                if page_token:
                    params["page_token"] = page_token

                for attempt in range(MAX_ATTEMPTS):
                    resp = await client.get(
                        f"/organizations/{settings.anthropic_org_id}/cost_report",
                        headers=headers,
                        params=params,
                    )
                    retryable = resp.status_code == 429 or resp.status_code >= 500
                    if retryable and attempt < MAX_ATTEMPTS - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    resp.raise_for_status()  # out of retries or a non-retryable error: fail the run
                    break

                data = resp.json()
                entries = data.get("data", [])
                if not entries:
                    break

                for entry in entries:
                    record_id = entry.get("id") or f"anthropic:{entry.get('period','')}"
                    amount = normalize_amount(entry.get("cost", "0"))
                    currency = normalize_currency(entry.get("currency"), account.default_currency)
                    await upsert_billing_record(
                        self.db,
                        account_id=account.id,
                        source_id=None,
                        provider="anthropic",
                        external_record_id=str(record_id),
                        expense_category="api",
                        financial_basis="usage",
                        description=entry.get("workspace_id"),
                        period_start=period_start,
                        period_end=period_end,
                        quantity=None,
                        amount=amount,
                        currency=currency,
                        validation_status="verified",
                    )
                    records_processed += 1

                page_token = data.get("next_page_token")
                if not page_token:
                    break

        return "enabled", records_processed
