# Technical Design Document (TDD)

**Project:** Geidi AI Cost Tracking and Billing Integration  
**Ticket:** GEIDIMCP-102  
**Parent Ticket:** GEIDIMCP-49  
**Version:** 1.0 — Proposed Technical Design  
**Date:** October 16, 2026  
**Prepared by:** Riel Jake Engaña  
**Technical Reviewer:** Rey Nicko Santos  
**Business Stakeholder:** Paul Ryan  
**Status:** Draft — Pending Technical Review

---

## 1. Technical Overview

### 1.1 Purpose

Develop a reliable billing ingestion and cost reporting integration for Claude/Anthropic and ChatGPT/OpenAI.

The system shall retrieve authorized billing information, process invoices and exports, reconcile financial records, and publish validated expenses into the existing GEIDIMCP-49 AI cost reporting platform.

### 1.2 Technical Objectives

- Support authorized, read-only billing retrieval.
- Provide invoice/CSV import when APIs are unavailable.
- Normalize billing records into a consistent data model.
- Distinguish subscription charges from API usage costs.
- Detect duplicate and potentially overlapping charges.
- Maintain auditable source references.
- Provide monthly actual expenditure and 12-month reporting.
- Integrate with existing GEIDIMCP-49 infrastructure rather than creating an unrelated reporting platform.

### 1.3 Design Principles

1. **Source of truth:** Financial figures must originate from provider billing records or authorized financial documents.
2. **Deterministic processing:** Calculations and reconciliation use explicit rules, not AI-generated estimates.
3. **Read-only vendor access:** No vendor billing modifications.
4. **Traceability:** Every published amount must be traceable to its original source.
5. **No double-counting:** Usage, invoices, payments, and credits must have distinct accounting treatment.
6. **Graceful degradation:** Unsupported APIs must not prevent manual invoice ingestion.

---

## 2. Proposed System Architecture

### 2.1 High-Level Architecture

```text
             EXTERNAL BILLING SOURCES
                       |
        +--------------+--------------+
        |                             |
  OpenAI Platform               Anthropic Console
  Costs API                     Cost Report API
        |                             |
        +--------------+--------------+
                       |
                 API CONNECTORS
                       |
          +------------+------------+
          |                         |
     API Ingestion            File Ingestion
     Scheduled Sync           PDF / CSV Export
          |                         |
          +------------+------------+
                       |
                VALIDATION ENGINE
                       |
             NORMALIZATION ENGINE
                       |
              DEDUPLICATION ENGINE
                       |
             RECONCILIATION ENGINE
                       |
              BILLING DATABASE
                       |
              REPORTING SERVICE
                       |
                GEIDIMCP-49
              AI COST DASHBOARD
```

### 2.2 Architectural Approach

Implement the billing module within the existing GEIDIMCP-49 backend or as an isolated service connected through an internal API.

Avoid creating a new dashboard unless the existing reporting platform cannot support the required information.

**Important:** The current GEIDIMCP-49 technology stack and database schema must be inspected before selecting the final implementation framework.

---

## 3. Technology Stack

The following technologies are proposed and require confirmation against the existing GEIDIMCP-49 architecture.

| Layer | Proposed Technology | Purpose |
|---|---|---|
| Frontend | Existing GEIDIMCP-49 UI | Financial reporting |
| Backend | Existing backend; Python/FastAPI if compatible | Billing services |
| Database | Existing relational DB; PostgreSQL if needed | Billing records |
| HTTP Client | Native HTTP client or supported SDK | Provider API requests |
| PDF Processing | PDF text extraction library | Invoice parsing |
| CSV Processing | Standard CSV parser | Structured export ingestion |
| Scheduling | Existing job scheduler | Periodic retrieval |
| Credential Storage | Existing secrets manager | API credential protection |
| Testing | Framework-compatible test runner | Unit/integration tests |
| Logging | Existing application logging | Operational audit trail |

AI-assisted extraction may be used for unstructured invoices, but monetary values must be independently validated before publication.

---

## 4. External Data Integrations

### 4.1 OpenAI API Cost Integration

**Potential endpoint:**

`GET /v1/organization/costs`

Base URL:

`https://api.openai.com`

Purpose:

Retrieve cost information for authorized OpenAI API organizations.

Requirements:

- Approved administrative credentials.
- Permission to retrieve organization cost data.
- Billing-period filters.
- Pagination handling.
- Timestamp and currency preservation.
- Error handling and synchronization logs.

**Limitation:** OpenAI API costs must not be treated as the complete cost of ChatGPT subscriptions or all Codex activity.

### 4.2 Anthropic API Cost Integration

**Potential endpoint:**

`GET /v1/organizations/cost_report`

Base URL:

`https://api.anthropic.com`

Purpose:

Retrieve supported Anthropic API cost data using authorized administrative credentials.

Requirements:

- Approved Anthropic administrative credentials.
- Account-specific API availability verification.
- Billing-period filtering.
- Pagination handling.
- Provider response validation.
- Preservation of source metadata.

**Limitation:** Anthropic Console/API billing and Claude subscription billing must be treated separately.

### 4.3 Subscription Billing

Sources may include:

- ChatGPT workspace invoices.
- Claude subscription invoices.
- Authorized vendor billing exports.
- Payment statements where appropriate.

Implementation:

1. Authorized user uploads a billing document.
2. System identifies the provider and document type.
3. Relevant monetary fields are extracted.
4. User reviews uncertain information.
5. System validates and stores accepted records.
6. Records become available for reconciliation.

### 4.4 Capability Matrix

| Source | Intended Method | Verification Required |
|---|---|---|
| OpenAI API costs | Official Costs API | Admin credentials and account permissions |
| Anthropic API costs | Official Cost Report API | Admin credentials and supported plan |
| ChatGPT seats/subscriptions | Invoice/export | Billing document availability |
| Claude seats/subscriptions | Invoice/export | Billing document availability |
| Claude Code costs | Relevant supported analytics/billing source | Plan and accounting method |
| Codex costs | Supported usage/billing source or invoices | Whether charges are separately identifiable |

No provider integration should be marked operational without a successful authorized test.

---

## 5. Database Design

### 5.1 Billing Accounts

**Table:** `ai_billing_accounts`

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| provider | VARCHAR | openai / anthropic |
| account_reference | VARCHAR | Provider account reference |
| account_name | VARCHAR | Display name |
| ownership_type | VARCHAR | geidi / personal / other_venture |
| collection_method | VARCHAR | api / invoice / csv |
| currency | VARCHAR(3) | Billing currency |
| is_active | BOOLEAN | Active account |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

Do not store plaintext API credentials in this table.

### 5.2 Billing Sources

**Table:** `ai_billing_sources`

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| account_id | UUID | Linked billing account |
| source_type | VARCHAR | api / pdf / csv / statement |
| source_reference | VARCHAR | Provider/document reference |
| source_hash | VARCHAR | Duplicate-file detection |
| billing_period_start | DATE | Beginning of period |
| billing_period_end | DATE | End of period |
| imported_at | TIMESTAMP | Ingestion timestamp |
| status | VARCHAR | imported / validated / rejected |

Source documents should be kept in access-controlled storage according to company retention policy.

### 5.3 Billing Records

**Table:** `ai_billing_records`

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| account_id | UUID | Linked account |
| source_id | UUID | Source reference |
| external_record_id | VARCHAR | Vendor record identifier |
| expense_category | VARCHAR | subscription / seat / api / credit / adjustment |
| description | TEXT | Charge description |
| period_start | DATE | Cost period start |
| period_end | DATE | Cost period end |
| quantity | DECIMAL | Quantity when applicable |
| amount | DECIMAL(20,6) | Monetary value |
| currency | VARCHAR(3) | ISO currency |
| financial_basis | VARCHAR | invoiced / usage / payment |
| validation_status | VARCHAR | pending / verified / disputed |
| created_at | TIMESTAMP | Record creation |

Important database constraints:

- Monetary values must use decimal arithmetic.
- Repeated imports must be idempotent.
- Unique provider identifiers should be enforced where supported.
- Missing provider identifiers require a documented fallback deduplication key.
- The same transaction must not contribute twice to the same financial reporting total.

### 5.4 Reconciliation Records

**Table:** `ai_billing_reconciliations`

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| billing_record_id | UUID | Billing record |
| financial_reference | VARCHAR | Invoice or payment reference |
| expected_amount | DECIMAL | Expected amount |
| observed_amount | DECIMAL | Matched amount |
| variance | DECIMAL | Difference |
| reconciliation_status | VARCHAR | matched / unmatched / partial |
| reviewed_by | UUID | Authorized reviewer |
| reviewed_at | TIMESTAMP | Review timestamp |

Production schema must also support source-to-record relationships and accounting treatment for invoices containing multiple charge lines.

---

## 6. Backend API Design

Internal endpoints are proposed rather than confirmed existing endpoints.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/ai-billing/accounts` | List authorized billing accounts |
| POST | `/api/ai-billing/imports` | Upload invoice or CSV |
| GET | `/api/ai-billing/imports/{id}` | Retrieve ingestion result |
| POST | `/api/ai-billing/sync/{provider}` | Trigger authorized provider sync |
| GET | `/api/ai-billing/records` | Retrieve normalized records |
| GET | `/api/ai-billing/reconciliation` | Retrieve reconciliation results |
| GET | `/api/ai-billing/summary` | Retrieve consolidated reporting data |
| GET | `/api/ai-billing/trends` | Retrieve historical monthly totals |

Security requirements:

- Authenticated access for all endpoints.
- Role-based authorization for billing operations.
- Restricted sync operations.
- Input validation and upload limits.
- Audit logs for imports, reviews, and synchronization.
- No API secrets in responses.

---

## 7. Billing Ingestion Pipeline

### 7.1 API Ingestion

1. Read approved credential from secure storage.
2. Query provider for a specified period.
3. Handle pagination, timeouts, and rate limits.
4. Validate response structure.
5. Retain raw source metadata securely.
6. Normalize cost records.
7. Upsert records using stable identifiers.
8. Record synchronization status.
9. Flag incomplete periods.
10. Publish verified data for reporting.

### 7.2 File Ingestion

1. Receive authorized PDF/CSV upload.
2. Validate file type and size.
3. Calculate document hash.
4. Detect duplicate uploads.
5. Extract vendor name and billing details.
6. Identify invoice date, billing period, amounts, currency, tax, and credits.
7. Verify line-item and invoice totals.
8. Request manual review for uncertain values.
9. Store normalized data and source reference.
10. Include approved records in reporting.

### 7.3 Error Handling

| Error | Expected Behavior |
|---|---|
| Invalid credentials | Mark integration blocked; require credential review |
| Rate limit | Retry with exponential backoff |
| Timeout | Retry safely without duplicate ingestion |
| Malformed invoice | Require review or reject import |
| Duplicate invoice | Preserve original; prevent duplicate financial posting |
| Missing currency | Flag as incomplete |
| Missing billing period | Require user verification |
| Partial API response | Mark period incomplete |
| Provider service outage | Record failure and retain existing verified data |

---

## 8. Deterministic Cost Calculation

### 8.1 Monthly Expense Total

For a selected billing month:

`Monthly Actual Expense = Sum of eligible invoice charges + approved adjustments - applicable credits`

Rules:

- Only include records assigned to the selected reporting basis.
- Exclude duplicate and disputed records unless explicitly approved.
- Handle refunds and credits consistently.
- Preserve original currencies.
- Apply an approved conversion policy before consolidated cross-currency totals.

### 8.2 Usage vs. Actual Expense

API usage reports may represent consumption rather than money paid during a specific accounting period.

Example:

- Prepaid API credit purchased: $100
- API usage consumed: $30
- Credit balance remaining: $70

The system must not automatically report $130 as actual expenditure.

Separate reporting concepts:

- Invoiced or recognized financial charges
- API consumption costs
- Payments and prepaid balances
- Credits and adjustments

Reconciliation rules must define which values contribute to management's primary expense metric.

### 8.3 Deduplication

Preferred uniqueness key:

`provider + account_id + external_record_id`

Fallback for documents lacking identifiers:

`provider + account_id + invoice_number + billing_period`

For uploaded files, use a cryptographic file hash to detect identical uploads.

File-hash detection alone is insufficient because different files can represent the same financial transaction.

---

## 9. Dashboard Integration

### 9.1 Core Metrics

- Total AI spending for selected period
- OpenAI cost
- Anthropic cost
- Subscription and seat cost
- API consumption cost
- Monthly comparison
- 12-month spending trend
- Unmatched or disputed records
- Missing billing coverage
- Last successful synchronization

### 9.2 Filters

- Provider
- Billing account
- Expense category
- Billing period
- Ownership category
- Reconciliation status

### 9.3 Dashboard Data Contract

The reporting service should provide a standardized response such as:

```json
{
  "period": "2026-10",
  "currency": "USD",
  "actual_expense": "250.00",
  "api_consumption_cost": "85.00",
  "providers": {
    "openai": "150.00",
    "anthropic": "100.00"
  },
  "data_status": "partial",
  "unreconciled_records": 2
}
```

Values above are illustrative only.

The contract must specify whether provider totals use the same financial basis as `actual_expense`.

---

## 10. Security Architecture

### 10.1 Access Control

Roles should include, or map to existing equivalent permissions:

**Billing Administrator**

- Configure authorized billing accounts.
- Manage integration credentials.
- Trigger synchronization.
- Review failed ingestion jobs.

**Finance Reviewer**

- Review transactions.
- Inspect invoices and reconciliation evidence.
- Approve or dispute matched records.

**Reporting Viewer**

- View authorized aggregate financial reports.
- Cannot modify source records or credentials.

### 10.2 Credentials

- Keep vendor credentials in a secrets manager.
- Encrypt credentials at rest and in transit.
- Never expose administrative tokens to frontend clients.
- Apply least-privilege access.
- Support credential rotation and revocation.

### 10.3 Audit Trail

Capture:

- User or service identity
- Action performed
- Timestamp
- Source identifier
- Affected billing record
- Validation or reconciliation result

Do not log raw secrets or unnecessary sensitive billing data.

---

## 11. Testing Strategy

### 11.1 Unit Testing

| Test ID | Scenario | Expected Result |
|---|---|---|
| UT-01 | Valid billing record | Correct normalization |
| UT-02 | Duplicate API record | No duplicate posting |
| UT-03 | Duplicate invoice | Existing charge identified |
| UT-04 | Subscription classification | Correct category |
| UT-05 | API usage classification | Correct category |
| UT-06 | Credit adjustment | Correct signed amount |
| UT-07 | Mixed currencies | Conversion policy enforced |
| UT-08 | Missing required fields | Validation fails safely |

### 11.2 Integration Testing

| Test ID | Scenario | Expected Result |
|---|---|---|
| IT-01 | Authorized OpenAI API call | Valid billing data retrieved |
| IT-02 | Authorized Anthropic API call | Valid billing data retrieved |
| IT-03 | Expired API credentials | Controlled authentication failure |
| IT-04 | Provider pagination | All requested records retrieved |
| IT-05 | PDF invoice import | Correct validated fields |
| IT-06 | CSV import | Correct normalized records |
| IT-07 | Repeated scheduled sync | Idempotent data storage |
| IT-08 | Reporting integration | Totals match validated source records |

Tests requiring live APIs must be explicitly marked blocked when authorized credentials are unavailable.

### 11.3 User Acceptance Testing

**UAT-01:** Finance can verify a displayed expense against the source invoice.

**UAT-02:** Users can distinguish OpenAI and Anthropic costs.

**UAT-03:** Subscription costs are separate from API consumption costs.

**UAT-04:** Duplicate documents do not inflate totals.

**UAT-05:** Missing sources and unresolved discrepancies are visible.

**UAT-06:** The 12-month trend displays supported historical periods and flags unavailable data.

**UAT-07:** Authorized reviewers can trace reported totals to original evidence.

---

## 12. Deployment and Operations

### 12.1 Deployment Requirements

- Integrate into the existing GEIDIMCP-49 deployment process.
- Use approved environment-specific configurations.
- Provision billing database migrations.
- Configure secrets securely.
- Set up synchronization schedules.
- Ensure reporting access controls are active.

### 12.2 Monitoring

Monitor:

- Last successful provider sync
- Failed import jobs
- Missing reporting periods
- Duplicate or disputed records
- Reconciliation variance
- API authentication failures
- Integration health

### 12.3 Recovery

- Preserve verified historical records during provider outages.
- Make sync jobs safely repeatable.
- Allow failed imports to be corrected and retried.
- Maintain migration rollback procedures.
- Protect source documents through approved backup controls.

---

## 13. Implementation Phases

### Phase 1 — Technical Discovery

**Tasks:**

- Inspect GEIDIMCP-49 architecture.
- Locate existing spending schema and reporting endpoints.
- Identify company billing accounts.
- Verify provider API capabilities.
- Confirm access permissions.

**Deliverables:** Architecture assessment and API capability matrix.

### Phase 2 — Billing Ingestion MVP

**Tasks:**

- Implement billing account registration.
- Implement CSV/PDF import.
- Normalize expenses.
- Validate totals.
- Prevent duplicate uploads and records.

**Deliverable:** Working invoice ingestion MVP.

### Phase 3 — Provider API Connectors

**Tasks:**

- Implement supported OpenAI billing retrieval.
- Implement supported Anthropic billing retrieval.
- Handle pagination and rate limits.
- Add secure credential management.
- Support scheduled synchronization.

**Deliverable:** Verified API integrations or documented fallback/blockers.

### Phase 4 — Reconciliation and Reporting

**Tasks:**

- Implement reconciliation workflows.
- Publish monthly totals.
- Support historical trends.
- Add reporting filters.
- Integrate with GEIDIMCP-49.

**Deliverable:** Consolidated AI cost reporting module.

### Phase 5 — Quality Assurance and Handover

**Tasks:**

- Complete unit and integration tests.
- Reconcile sample periods against vendor statements.
- Document source coverage and limitations.
- Conduct reviewer walkthrough.
- Obtain technical and financial acceptance.

**Deliverable:** Tested integration, evidence, and handover documentation.

---

## 14. Technical Risks and Blockers

| Risk | Severity | Mitigation |
|---|---|---|
| Missing administrative credentials | High | Request approved access |
| Unsupported subscription billing APIs | High | Invoice/CSV fallback |
| Existing database incompatibility | Medium | Inspect before migration |
| Duplicate financial charges | High | Idempotency and reconciliation |
| Currency inconsistencies | Medium | Approved FX conversion rules |
| Incomplete historical data | Medium | Partial-period reporting |
| Unvalidated extracted invoice amounts | High | Deterministic checks and review |
| Incorrect expense versus usage classification | High | Explicit financial basis |

---

## 15. Definition of Done

The technical implementation is considered ready for acceptance when:

- [ ] Account inventory and API capability matrix are documented.
- [ ] Supported authorized billing APIs have been tested.
- [ ] Working export-based fallback exists for unsupported sources.
- [ ] Billing data is normalized and traceable.
- [ ] Subscription and API charges are separately classified.
- [ ] Duplicate charges are prevented.
- [ ] Reconciliation evidence matches vendor records.
- [ ] Monthly actuals and 12-month trends are integrated into GEIDIMCP-49.
- [ ] Missing sources and partial periods are clearly identified.
- [ ] Unit and integration tests have passed.
- [ ] Documentation and blockers are handed over.
- [ ] Nicko has reviewed and signed off.

---

## 16. Open Technical Decisions

Before implementation, confirm:

1. Existing GEIDIMCP-49 backend framework.
2. Existing database and billing-related tables.
3. Available API credentials and administrative permissions.
4. Current invoice storage mechanism.
5. Existing scheduled-job infrastructure.
6. Financial currency and conversion policy.
7. Reconciliation data availability.
8. Dashboard API conventions.
9. Audit logging and retention requirements.

These remain open because the existing codebase and deployment configuration have not yet been inspected.

---

## 17. Technical Approval

| Role | Name | Status |
|---|---|---|
| Developer / Delivery Owner | Riel Jake Engaña | Pending |
| Technical Reviewer | Rey Nicko Santos | Pending |
| Business Stakeholder | Paul Ryan | Pending |
| Finance Reviewer | Christine / Finance | Pending |

**Document Status:** Proposed technical design. Implementation feasibility, actual service endpoints, and compatibility must be verified against the running GEIDIMCP-49 environment before development begins.

---

**End of Technical Design Document — GEIDIMCP-102**