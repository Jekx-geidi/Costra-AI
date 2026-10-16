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


class OpenAIConnector(BaseConnector):
    provider = "openai"

    async def _execute(
        self, run_id: uuid.UUID, period_start: date | None, period_end: date | None
    ) -> tuple[str, int]:
        if not settings.openai_billing_enabled:
            return "disabled", 0

        if not settings.openai_admin_api_key:
            return "blocked", 0

        account_result = await self.db.execute(
            select(BillingAccount).where(
                BillingAccount.provider == "openai",
                BillingAccount.is_active == True,
                BillingAccount.ownership_type == "geidi",
            )
        )
        account = account_result.scalar_one_or_none()
        if not account:
            return "blocked", 0

        headers = {
            "Authorization": f"Bearer {settings.openai_admin_api_key}",
            "OpenAI-Organization": settings.openai_org_id,
        }
        params: dict = {}
        if period_start:
            params["start_time"] = int(
                datetime(period_start.year, period_start.month, period_start.day, tzinfo=timezone.utc).timestamp()
            )

        records_processed = 0
        async with httpx.AsyncClient(base_url=settings.openai_costs_base_url, timeout=30) as client:
            for _ in range(20):
                for attempt in range(MAX_ATTEMPTS):
                    resp = await client.get("/organization/costs", headers=headers, params=params)
                    retryable = resp.status_code == 429 or resp.status_code >= 500
                    if retryable and attempt < MAX_ATTEMPTS - 1:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    resp.raise_for_status()  # out of retries or a non-retryable error: fail the run
                    break

                data = resp.json()
                items = data.get("data", [])
                if not items:
                    break

                for item in items:
                    record_id = item.get("id") or f"openai:{item.get('timestamp','')}"
                    amount = normalize_amount(item.get("amount", {}).get("value", "0"))
                    currency = normalize_currency(item.get("amount", {}).get("currency"), account.default_currency)
                    await upsert_billing_record(
                        self.db,
                        account_id=account.id,
                        source_id=None,
                        provider="openai",
                        external_record_id=str(record_id),
                        expense_category="api",
                        financial_basis="usage",
                        description=item.get("project_id"),
                        period_start=period_start,
                        period_end=period_end,
                        quantity=normalize_amount(item.get("usage", {}).get("input_tokens", "0")),
                        amount=amount,
                        currency=currency,
                        validation_status="verified",
                    )
                    records_processed += 1

                next_page = data.get("next_page")
                if not next_page:
                    break
                # Cursor pagination: passing params replaces any query string, so send the cursor as a param.
                params["page"] = next_page

        return "enabled", records_processed
