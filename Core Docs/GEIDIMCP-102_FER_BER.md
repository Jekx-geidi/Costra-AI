# GEIDIMCP-102 — Frontend and Backend Engineering Requirements (FER + BER)

**Project:** Geidi AI Cost Tracking and Billing Integration  
**Parent:** GEIDIMCP-49  
**Version:** 1.0 — Proposed requirements  
**Date:** October 16, 2026  
**Owner:** Riel Jake Engaña  
**Reviewers:** Rey Nicko Santos (technical), Paul Ryan (business)  
**Status:** Draft; implementation and current stack not yet verified

> **Terminology:** In this document, FER means **Frontend Engineering Requirements** and BER means **Backend Engineering Requirements**. These are proposed requirements derived from the GEIDIMCP-102 BRD/TDD, not an assertion that the features already exist.

## 1. Purpose and boundaries

Deliver an auditable AI billing ingestion and reporting capability for authorized **OpenAI/ChatGPT** and **Anthropic/Claude** accounts within the existing GEIDIMCP-49 cost reporting experience. Prefer read-only vendor APIs where officially supported; otherwise use reviewed invoice/CSV imports. Distinguish provider charges from usage estimates and cash payments.

**In scope:** authorized account registry, billing file imports, available vendor cost APIs, validation, categorization, reconciliation, source traceability, monthly actuals, 12-month trends, access controls, error/coverage states.

**Out of scope:** ITQuoter supplier/quote integration, bypassing access restrictions, autonomous vendor billing changes, forcing all AI activity through LiteLLM, access to private accounts without Paul's explicit consent.

**Dependencies to confirm:** GEIDIMCP-49 frontend/backend stack, database schema, auth roles, accounting basis/currency policy, administrative vendor permissions, Finance/Xero availability and file retention rules.

---

## 2. FER — Frontend Engineering Requirements

### 2.1 Pages and views

| ID | Priority | Requirement | Acceptance check |
|---|---|---|---|
| FER-01 | Must | Add an **AI Spend Overview** section within the existing GEIDIMCP-49 UI. | Authorized viewer can navigate without a separate login or duplicated dashboard. |
| FER-02 | Must | Show **monthly actual expense** by provider with a clearly labeled financial basis and currency. | Totals agree with the validated backend summary for the chosen period. |
| FER-03 | Must | Show a **12-month trend**, preserving months with missing/partial coverage. | Missing data is displayed as unavailable/partial, never silently as zero. |
| FER-04 | Must | Distinguish **subscription/seat charges**, **API consumption costs**, **payments/prepaid credit**, and **adjustments**. | User cannot mistake usage amounts for invoices or cash outlays. |
| FER-05 | Must | Provide provider, account, period, category, ownership and reconciliation-status filters. | Filters affect all applicable charts, totals and records consistently. |
| FER-06 | Must | Provide a billing records table with source, date/period, original currency and amount, category, validation and reconciliation status. | Reviewer can trace an included amount to its source. |
| FER-07 | Must | Provide an invoice/CSV upload workflow with progress, parsing preview, validation errors and confirmation. | Invalid or uncertain fields require review before posting. |
| FER-08 | Must | Provide account/source coverage status, last sync time and actionable API/import errors. | Unsupported access is shown as a limitation, not a successful sync. |
| FER-09 | Must | Allow authorized reviewers to inspect source references and resolve/review flagged records within their permissions. | Actions are attributable and reflected after refresh. |
| FER-10 | Must | Enforce UI permission boundaries for viewer, finance reviewer and billing administrator (or existing equivalent roles). | Unauthorized users cannot access sensitive billing screens/actions. |
| FER-11 | Should | Responsive tables, charts and upload controls on mobile and desktop. | No clipped critical amounts or inaccessible form controls at common widths. |
| FER-12 | Should | Export permitted filtered reporting data with clear period, currency and provenance. | Export matches active filters and backend figures. |

### 2.2 Recommended information architecture

- **Overview:** month selector, total verified expense, provider split, category split, 12-month trend, completeness banner.
- **Billing Records:** searchable/filterable table and source-details panel.
- **Imports:** PDF/CSV upload, preview, validation, submit, import history.
- **Integrations:** permitted account connections, source type, sync health, last run and blockers.
- **Reconciliation:** matched/unmatched/partial items, variance and evidence links.

### 2.3 UI states and safety

- **Loading:** show skeleton or clear progress; do not display stale values as newly verified.
- **Empty:** distinguish no charges from no available data.
- **Partial:** visibly label missing providers/months/records.
- **Error:** show safe, actionable messages; never expose tokens, personal billing identifiers unnecessarily or raw stack traces.
- **Accessibility:** keyboard-navigable controls, accessible labels, clear status text alongside color and legible number formatting.
- **Money presentation:** include ISO currency and reporting basis; do not add cross-currency totals without an approved conversion method.

### 2.4 Frontend handoff interfaces (proposed, not confirmed)

| Operation | Suggested route | Notes |
|---|---|---|
| Overview summary | `GET /api/ai-billing/summary` | period, account, category and provider filters |
| 12-month trend | `GET /api/ai-billing/trends` | includes coverage state per month |
| Billing records | `GET /api/ai-billing/records` | server pagination and safe filtering |
| Account registry | `GET /api/ai-billing/accounts` | return only authorized account metadata |
| Upload | `POST /api/ai-billing/imports` | multipart, server-side validation |
| Import review | `GET /api/ai-billing/imports/{id}` | parsing confidence/errors and status |
| Reconciliation | `GET /api/ai-billing/reconciliation` | permission-restricted |
| Trigger sync | `POST /api/ai-billing/sync/{provider}` | administrator only, audited |

Final routes must follow existing project conventions.

---

## 3. BER — Backend Engineering Requirements

### 3.1 Data collection and ingestion

| ID | Priority | Requirement | Acceptance check |
|---|---|---|---|
| BER-01 | Must | Maintain authorized billing account inventory: vendor, organization/workspace, ownership, currency, collection method, billing period, access status. | Account cannot be enabled without ownership and authorization metadata. |
| BER-02 | Must | Verify provider API capability *per actual account/tier* before activating read-only integrations. | Capability matrix documents endpoint, permissions, fields, limitations and fallback. |
| BER-03 | Must | Support official read-only OpenAI organization cost retrieval when authorized and available. | A verified test reconciles representative API results with provider evidence, or records the blocker. |
| BER-04 | Must | Support official read-only Anthropic organization cost retrieval when authorized and available. | Same evidence or documented fallback requirement as BER-03. |
| BER-05 | Must | Support PDF/CSV invoice/export ingestion for subscriptions or unsupported APIs. | A supported invoice/export is parsed, reviewed and stored with source link. |
| BER-06 | Must | Normalize vendor records into a common, typed cost model. | Provider, account, period, category, currency, amount and financial basis are retained. |
| BER-07 | Must | Make repeated API pulls and repeated file imports **idempotent**. | Re-running a sync/import does not increase recognized totals. |
| BER-08 | Must | Reconcile source invoice/charge lines against authorized finance/card/Xero records where accessible. | Matching evidence, variance and unresolved status can be inspected. |
| BER-09 | Must | Separate usage consumption, invoiced charges, payments, prepaid credits, taxes and adjustments. | A credit purchase plus usage does not get summed as two actual expenses. |
| BER-10 | Must | Publish verified monthly actuals and 12-month trend data into existing GEIDIMCP-49 reporting structures. | Reporting totals reproduce underlying eligible ledger entries. |
| BER-11 | Must | Track unavailable sources, incomplete periods, unmatched charges and unknown ownership. | API responses report coverage metadata, not false zeroes. |
| BER-12 | Must | Secure credentials, files and personal billing data with least-privilege access and audit trails. | Unauthorized access is denied; secrets never appear in API responses or logs. |
| BER-13 | Must | Provide retryable, observable jobs with pagination, rate-limit handling and partial-failure tracking. | Retries cannot duplicate charges; failures do not overwrite verified periods. |
| BER-14 | Should | Schedule syncs where approved and supported by providers. | Job execution, last success, failures and next schedule are observable. |
| BER-15 | Must | Retain raw source references and normalization/reconciliation provenance. | A reviewer can reproduce a reported figure from accepted source records. |

### 3.2 Proposed domain model

**BillingAccount:** `id`, `provider`, `account_reference`, `ownership_type`, `collection_method`, `default_currency`, `authorization_status`, timestamps.  
**BillingSource:** `id`, `account_id`, `source_type`, `document/reference`, `content_hash`, period, import/sync status, provenance.  
**BillingRecord:** `id`, `account_id`, `source_id`, `provider_record_id`, `category`, `financial_basis`, `period`, `amount_decimal`, `currency`, `validation_status`, timestamps.  
**Reconciliation:** `id`, `billing_record_id`, `financial_reference`, `matched_amount`, `variance`, `status`, reviewer and timestamp.  
**SyncRun:** `id`, `account_id`, `job_type`, `requested_period`, `started_at`, `finished_at`, `status`, `coverage`, sanitized error summary.  
**AuditEvent:** principal, action, target, timestamp and outcome.

Adapt these to GEIDIMCP-49's existing tables; avoid duplicating pre-existing entities.

### 3.3 Normalization and accounting rules

1. Store monetary figures as **decimal**, never floating point.
2. Retain original transaction currency; convert only using an approved exchange-rate source/date policy with rate provenance.
3. Define and document which billing line types count in **monthly actual expense**; segregate usage estimates and payments.
4. Preserve source period, invoice issue date, payment date and ingestion timestamp as different fields where applicable.
5. Prefer provider-supplied record IDs for deduplication. For imports, combine vendor/account/invoice/line references and hashes; a file hash alone is insufficient.
6. Require human review when PDF extraction cannot confidently prove invoice totals and category.
7. Track revisions and corrections without silently deleting historical accounting evidence.

### 3.4 External integrations and constraints

- **OpenAI:** assess the official organization Costs API (`GET /v1/organization/costs`) for authorized API-platform costs; ChatGPT subscriptions are separate and need their own supported source or invoice fallback.
- **Anthropic:** assess the official organization Cost Report API (`GET /v1/organizations/cost_report`) for authorized API usage charges; Claude subscriptions/seat invoices may need export-based ingestion.
- **Claude Code/Codex:** do not infer billable charges directly from activity metrics; use verified billing evidence and label analytics separately.
- **Finance systems:** reconciliation only with approved accounts and credentials; never assume access to Xero, cards or reimbursement records.
- **LiteLLM/Langfuse:** optional comparison evidence, not exhaustive sources of actual vendor spend.

Verify endpoint availability, response schema, permissions and account-plan suitability during implementation; do not label integrations operational on design alone.

### 3.5 Processing flow

1. Confirm provider account authorization and source type.
2. Fetch from permitted API or accept validated invoice/export upload.
3. Store immutable raw source reference (with access controls).
4. Parse, validate required fields and monetary arithmetic.
5. Normalize line items and category/financial basis.
6. Match stable identifiers to prevent duplicate ingestion.
7. Reconcile against permitted source invoices and finance payments.
8. Flag unknown ownership, variances and incomplete periods.
9. Publish only eligible, labeled results with provenance and coverage.
10. Record operational/audit events for every run and review action.

### 3.6 Security and operations

- Authenticate and authorize every endpoint; use role-appropriate access for uploads, reviews, account setup and sync triggers.
- Store API keys server-side in an approved secret store; restrict token scope, rotate/revoke when needed and never expose in frontend bundles.
- Apply file-size/type limits, safe PDF parsing, malware protections and secure storage retention rules.
- Implement bounded retries/backoff and safe pagination, with provider-specific rate limits.
- Keep existing verified data if a provider fails; mark coverage as stale or partial.
- Log job IDs, source IDs and sanitized errors, without secrets or sensitive invoice content.

---

## 4. End-to-end acceptance tests

| Test | Expected result |
|---|---|
| Import the same subscription invoice twice | One recognized financial charge; second import flagged duplicate. |
| Sync the same vendor API period repeatedly | No duplicate ledger lines; last-sync metadata updates. |
| Provider API denied by permissions | Clear blocker and fallback; existing verified data unchanged. |
| Imported invoice has unreadable total | Manual review required; no silent posting as verified. |
| API usage occurs after prepaid credit purchase | Consumption and payment shown separately; no double-counting. |
| One provider is missing for a month | Dashboard shows partial coverage, not falsely complete totals. |
| Finance amount differs from provider invoice | Variance is displayed and auditable. |
| User lacks billing-admin permission | Cannot view credentials or start sync. |
| Monthly reports viewed on mobile | Important amounts and statuses remain usable/readable. |
| Authorized reviewer follows a reported amount | Original account, document/record and reconciliation evidence available. |

## 5. Delivery sequence and ownership

1. **Discovery:** inspect existing GEIDIMCP-49 code/schema, identify sources, confirm owner access and approved accounting basis.
2. **MVP:** secure manual PDF/CSV ingestion, validation, deduplication, and an overview with partial coverage indicators.
3. **Automation:** add vendor cost APIs for the actual permitted accounts, plus scheduled sync, error logs and source provenance.
4. **Reconciliation:** integrate authorized Finance/Xero matching and credits/accounting rules.
5. **Acceptance:** reconcile sample invoices, demonstrate both provider paths or documented fallback, complete tests and obtain Nicko sign-off.

### Definition of done

- [ ] Source/account inventory and provider capability matrix reviewed.
- [ ] At least one verified ingestion flow per provider, or documented API blocker with working export fallback.
- [ ] Subscription/seat and API costs displayed separately.
- [ ] No double-counting across imports, usage, credits and payment records.
- [ ] Monthly actuals and 12-month trends integrated into GEIDIMCP-49.
- [ ] Incomplete coverage and unresolved reconciliation are visible.
- [ ] Security, authorization, audit and end-to-end test evidence captured.
- [ ] Nicko completes technical/reconciliation review and sign-off.

## 6. Open decisions / blockers to confirm with Paul and Nicko

- Which vendor accounts are company-owned vs personal/other venture?
- Who can approve administrative billing access and invoice sharing?
- Are provider organization-cost endpoints available for the actual paid tiers and accounts?
- Which existing GEIDIMCP-49 backend, tables, identity model and dashboard components must be reused?
- Is the management headline **invoiced expense**, **cash outlay** or another financial metric?
- Which conversion currency and FX methodology should be used?
- How much invoice history and Finance/Xero data can be accessed?
- Which roles can access invoices, per-account costs and exports?

**Document caution:** This is a design/requirements artifact. No live API integrations, database migrations, or reconciliations are claimed completed by this document.
