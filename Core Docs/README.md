# Geidi AI Spend Manager

**Plane ticket:** GEIDIMCP-102  
**Parent:** GEIDIMCP-49  
**Status:** Proposed implementation; validate against the existing repository before coding.

## Overview

Geidi AI Spend Manager consolidates authorized Claude/Anthropic and ChatGPT/OpenAI billing information into the GEIDIMCP-49 AI cost reporting system. It aims to support accurate monthly expenses, subscription/API cost separation, reconciliation, auditability, and a 12-month trend.

## Scope

- Inventory authorized billing accounts, ownership, plan, payment source, and permissions.
- Retrieve costs from supported read-only vendor APIs where available.
- Import approved PDF/CSV billing documents when direct API access is unsupported.
- Normalize provider, account, dates, amount, currency, category, and financial basis.
- Prevent duplicates; reconcile invoices, charges, payments, reimbursements, and usage data without double-counting.
- Publish verified totals and show missing, unmatched, or partial periods.

**Out of scope:** ITQuoter supplier/quote integrations, security-control bypasses, purchasing/canceling subscriptions, and routing all AI traffic through LiteLLM.

## Status and architecture

This documentation describes a **design**, not a verified implementation. The existing GEIDIMCP-49 repository, deployment, database, and API routes have not been inspected.

Proposed flow:

```text
OpenAI Costs API ----\
Anthropic Cost API ---+--> Ingestion --> Validation --> Normalization
PDF/CSV invoices ----/                               |
                                      Deduplication / Reconciliation
                                                    |
                                      Auditable billing records
                                                    |
                                      GEIDIMCP-49 dashboard
```

The previously discussed **React/Vite + FastAPI + PostgreSQL** stack is a *proposal only*. Prefer the parent project's existing stack, authentication, storage, and UI patterns.

## Getting started

1. Inspect the current GEIDIMCP-49 codebase and identify the actual framework, services, and database schema.
2. Review the GEIDIMCP-102 BRD, TDD, FER, and BER, and reconcile differences with existing code.
3. Copy a sanitized `.env.example` to `.env` **only after** verifying the variable names used by the application.
4. Obtain explicit authorization for any organization credentials or personal-account records.
5. Implement a sample PDF/CSV import first if API credentials are unavailable.
6. Validate imported totals against source statements before publishing to the dashboard.
7. Add provider API connectors and scheduled sync only where supported and authorized.

### Proposed environment variables (not confirmed in code)

```dotenv
# Backend example (adapt to existing conventions)
DATABASE_URL=
OPENAI_ADMIN_API_KEY=
ANTHROPIC_ADMIN_API_KEY=
OPENAI_BILLING_ENABLED=false
ANTHROPIC_BILLING_ENABLED=false
INVOICE_UPLOAD_ENABLED=true
DEFAULT_CURRENCY=USD
REPORTING_TIMEZONE=Asia/Manila

# React/Vite example, only if used in this repo
VITE_API_BASE_URL=http://localhost:8000/api
```

Never commit actual `.env` files, private invoices, or secrets. Keep sensitive credentials server-side.

## Source coverage

| Source | Intended ingestion | Caveat |
| --- | --- | --- |
| OpenAI API costs | Authorized organization costs API | Not equivalent to ChatGPT subscription invoicing |
| Anthropic API costs | Authorized organization cost report API | Not equivalent to all Claude subscriptions |
| ChatGPT and Claude subscriptions | Approved invoice/export upload | Requires review and appropriate access |
| Codex / Claude Code | Verified provider-specific records | Determine whether already included elsewhere |

Never assume an API is enabled on a given Geidi account without testing permissions.

## Reporting and financial integrity

Keep **invoiced charges**, **payments/prepaid credit purchases**, and **usage/consumption costs** distinct. Do not add them together as one total. Use decimal arithmetic, preserve original currency, and apply a documented FX policy before any consolidated conversion. Record original evidence, import timestamps, validation states, and reconciliation decisions.

## Testing and acceptance

- Unit tests for parsing, classification, normalization, deduplication, credits, and period handling.
- Integration tests for authorized API retrieval, pagination, retries, upload safety, and idempotency.
- Reconciliation test against at least one real, authorized source statement per supported provider or a documented export fallback.
- Dashboard totals trace to source records; incomplete months and unmatched charges are labeled.
- Technical/financial review and Nicko's acceptance sign-off are recorded.

## Ownership and open questions

**Delivery:** Riel Jake  
**Review:** Rey Nicko  
**Business decisions:** Paul; coordinate with Christine/Finance as appropriate.

Before implementation, confirm project architecture, account inventory, API permissions, invoice retention, reporting currency, available finance records, and sign-off process.

For repository-wide agent rules see [Agent.md](Agent.md); for Claude-specific instructions see [Claude.md](Claude.md).
