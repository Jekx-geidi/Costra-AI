"""
Read-only snapshot of COSTRA data that grounds the assistant's answers.

Only data the requesting user could already see in the UI is included, scoped
by the same role levels the routers enforce. No secrets, keys or file paths.
"""
from datetime import date, datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import ROLES
from app.config import settings
from app.models.audit_event import AuditEvent
from app.models.billing_account import BillingAccount
from app.models.billing_record import BillingRecord
from app.models.billing_source import BillingSource
from app.models.reconciliation import Reconciliation
from app.models.sync_run import SyncRun
from app.models.user import User
from app.services.reporting import ReportingService


def _iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def _money(value) -> str | None:
    return None if value is None else f"{value:.2f}"


def _last_months(count: int) -> list[str]:
    today = date.today()
    months = []
    for i in range(count - 1, -1, -1):
        month, year = today.month - i, today.year
        while month <= 0:
            month += 12
            year -= 1
        months.append(f"{year}-{month:02d}")
    return months


async def build_snapshot(db: AsyncSession, user: User) -> dict:
    level = ROLES.get(user.role, -1)
    reporting = ReportingService(db)

    accounts = (await db.execute(select(BillingAccount).order_by(BillingAccount.account_name))).scalars().all()
    account_names = {a.id: a.account_name for a in accounts}

    monthly = []
    for period in _last_months(settings.billing_history_months):
        s = await reporting.get_summary(period)
        monthly.append({
            "period": s.period,
            "data_status": s.data_status,
            "invoiced_total": _money(s.actual_expense),
            "api_consumption": _money(s.api_consumption_cost),
            "subscriptions_and_seats": _money(s.subscription_cost),
            "openai_total": _money(s.providers.openai),
            "anthropic_total": _money(s.providers.anthropic),
            "unreconciled_records": s.unreconciled_records,
            "missing_providers": s.missing_providers,
        })

    status_counts = dict((await db.execute(
        select(BillingRecord.validation_status, func.count()).group_by(BillingRecord.validation_status)
    )).all())
    recent_records = (await db.execute(
        select(BillingRecord).order_by(BillingRecord.created_at.desc()).limit(30)
    )).scalars().all()

    imports = (await db.execute(
        select(BillingSource).order_by(BillingSource.imported_at.desc()).limit(10)
    )).scalars().all()

    syncs = (await db.execute(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(10))).scalars().all()

    snapshot = {
        "today": date.today().isoformat(),
        "current_user": {"email": user.email, "role": user.role},
        "reporting_currency": settings.default_currency,
        "notes": "Monthly totals only count Geidi-owned accounts and exclude disputed records.",
        "billing_accounts": [{
            "name": a.account_name,
            "provider": a.provider,
            "ownership": a.ownership_type,
            "collection_method": a.collection_method,
            "currency": a.default_currency,
            "authorization_status": a.authorization_status,
            "active": a.is_active,
        } for a in accounts],
        "monthly_summaries": monthly,
        "records": {
            "count_by_validation_status": status_counts,
            "most_recent": [{
                "provider": r.provider,
                "account": account_names.get(r.account_id),
                "category": r.expense_category,
                "financial_basis": r.financial_basis,
                "description": r.description,
                "period_start": _iso(r.period_start),
                "period_end": _iso(r.period_end),
                "amount": f"{r.amount:.6f}",
                "currency": r.currency,
                "validation_status": r.validation_status,
                "added_at": _iso(r.created_at),
            } for r in recent_records],
        },
        "invoice_imports": [{
            "account": account_names.get(s.account_id),
            "file_type": s.source_type,
            "status": s.status,
            "billing_period_start": _iso(s.billing_period_start),
            "billing_period_end": _iso(s.billing_period_end),
            "imported_at": _iso(s.imported_at),
        } for s in imports],
        "sync_runs": [{
            "provider": r.provider,
            "status": r.status,
            "capability_status": r.capability_status,
            "records_processed": r.records_processed,
            "started_at": _iso(r.started_at),
            "finished_at": _iso(r.finished_at),
            "error": (r.error_summary or "")[:200] or None,
        } for r in syncs],
        "integrations": {
            "openai": {"billing_sync_enabled": settings.openai_billing_enabled,
                       "admin_key_configured": bool(settings.openai_admin_api_key)},
            "anthropic": {"billing_sync_enabled": settings.anthropic_billing_enabled,
                          "admin_key_configured": bool(settings.anthropic_admin_api_key)},
            "scheduled_sync_enabled": settings.billing_sync_enabled,
            "invoice_upload_enabled": settings.invoice_upload_enabled,
        },
    }

    if level >= ROLES["finance_reviewer"]:
        snapshot["reconciliation"] = {
            "count_by_status": dict((await db.execute(
                select(Reconciliation.reconciliation_status, func.count())
                .group_by(Reconciliation.reconciliation_status)
            )).all()),
        }
    else:
        snapshot["reconciliation"] = "not visible to this user's role"

    if level >= ROLES["billing_admin"]:
        events = (await db.execute(
            select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(25)
        )).scalars().all()
        snapshot["recent_activity"] = [{
            "when": _iso(e.created_at),
            "who": e.principal_email,
            "action": e.action,
            "on": e.resource_type,
            "outcome": e.outcome,
        } for e in events]
    else:
        snapshot["recent_activity"] = "not visible to this user's role"

    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return snapshot
