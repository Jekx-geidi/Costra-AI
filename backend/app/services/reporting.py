import calendar
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.billing_record import BillingRecord
from app.models.billing_account import BillingAccount
from app.schemas.reporting import SummaryResponse, TrendResponse, MonthTrend, ProviderTotals
from app.config import settings


def _parse_period(period: str) -> tuple[date, date]:
    year, month = int(period[:4]), int(period[5:7])
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _month_label(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


class ReportingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_summary(self, period: str) -> SummaryResponse:
        period_start, period_end = _parse_period(period)
        currency = settings.default_currency

        base_query = (
            select(BillingRecord)
            .join(BillingAccount, BillingRecord.account_id == BillingAccount.id)
            .where(
                BillingAccount.ownership_type == "geidi",
                BillingRecord.validation_status != "disputed",
                BillingRecord.period_start >= period_start,
                BillingRecord.period_start <= period_end,
            )
        )

        result = await self.db.execute(base_query)
        records = result.scalars().all()

        invoiced = Decimal("0")
        api_consumption = Decimal("0")
        subscription_cost = Decimal("0")
        openai_total: Decimal | None = None
        anthropic_total: Decimal | None = None
        providers_seen: set[str] = set()
        unreconciled = 0

        for r in records:
            providers_seen.add(r.provider)
            if r.financial_basis == "invoiced":
                invoiced += r.amount
            if r.financial_basis == "usage":
                api_consumption += r.amount
            if r.expense_category in ("subscription", "seat"):
                subscription_cost += r.amount
            if r.provider == "openai":
                openai_total = (openai_total or Decimal("0")) + r.amount
            elif r.provider == "anthropic":
                anthropic_total = (anthropic_total or Decimal("0")) + r.amount
            if r.validation_status == "pending":
                unreconciled += 1

        missing_providers = []
        for p in ("openai", "anthropic"):
            if p not in providers_seen:
                missing_providers.append(p)

        data_status = "complete" if not missing_providers else "partial" if records else "unavailable"

        return SummaryResponse(
            period=period,
            currency=currency,
            actual_expense=invoiced,
            api_consumption_cost=api_consumption,
            subscription_cost=subscription_cost,
            providers=ProviderTotals(openai=openai_total, anthropic=anthropic_total, currency=currency),
            data_status=data_status,
            unreconciled_records=unreconciled,
            missing_providers=missing_providers,
        )

    async def get_trends(self, months: int = 12) -> TrendResponse:
        today = date.today()
        currency = settings.default_currency
        trend_months: list[MonthTrend] = []

        for i in range(months - 1, -1, -1):
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1
            period_start, period_end = _parse_period(f"{year}-{month:02d}")
            label = _month_label(year, month)

            query = (
                select(func.sum(BillingRecord.amount))
                .join(BillingAccount, BillingRecord.account_id == BillingAccount.id)
                .where(
                    BillingAccount.ownership_type == "geidi",
                    BillingRecord.financial_basis == "invoiced",
                    BillingRecord.validation_status == "verified",
                    BillingRecord.period_start >= period_start,
                    BillingRecord.period_start <= period_end,
                )
            )
            result = await self.db.execute(query)
            total = result.scalar_one_or_none()

            if total is None:
                coverage = "unavailable"
            else:
                coverage_query = (
                    select(func.count(func.distinct(BillingRecord.provider)))
                    .join(BillingAccount, BillingRecord.account_id == BillingAccount.id)
                    .where(
                        BillingAccount.ownership_type == "geidi",
                        BillingRecord.period_start >= period_start,
                        BillingRecord.period_start <= period_end,
                    )
                )
                cov_result = await self.db.execute(coverage_query)
                provider_count = cov_result.scalar_one_or_none() or 0
                coverage = "complete" if provider_count >= 2 else "partial"

            trend_months.append(MonthTrend(
                period=label,
                actual_expense=total,
                coverage_status=coverage,
                currency=currency,
            ))

        return TrendResponse(months=trend_months, currency=currency)
