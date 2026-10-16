# Business Requirements Document (BRD)

**Project:** Geidi AI Cost Tracking and Billing Integration  
**Ticket:** GEIDIMCP-102  
**Parent Ticket:** GEIDIMCP-49  
**Document Version:** 1.0 — Draft for Review  
**Date:** October 16, 2026  
**Prepared by:** Riel Jake Engaña  
**Project Owner:** Geidi IT Services  
**Reviewer:** Rey Nicko Santos  
**Business Stakeholder:** Paul Ryan  
**Priority:** High

---

## 1. Executive Summary

Geidi uses multiple AI services, including Claude/Anthropic and ChatGPT/OpenAI, for development, AI agents, automation, and other business operations.

Currently, AI-related costs may be distributed across different subscriptions, API platforms, billing accounts, and payment methods. This makes it difficult to monitor consolidated AI expenditure, identify spending trends, and reconcile actual costs.

The proposed solution will integrate available vendor billing sources into Geidi's centralized AI Cost Reporting System (GEIDIMCP-49).

The system will collect, categorize, validate, and report AI-related expenses using authorized read-only APIs where supported, with PDF/CSV invoice ingestion as an alternative.

## 2. Business Problem

Geidi needs an accurate and auditable view of its AI spending.

Key challenges include:

- AI subscriptions and API usage are billed separately.
- Multiple accounts may use different payment methods.
- LiteLLM and Langfuse may not capture all AI-related expenses.
- Some billing information may not be accessible through APIs.
- Manual consolidation increases administrative work.
- Duplicate counting may occur when combining provider costs with financial records.
- Personal and company expenses must remain separate.

**Business impact:** Without centralized reporting, Geidi cannot reliably determine its total AI expenditure or assess where spending occurs.

## 3. Business Objectives

| ID | Business Objective |
|---|---|
| BO-01 | Consolidate Claude and OpenAI billing expenses |
| BO-02 | Reduce manual expense consolidation |
| BO-03 | Provide accurate monthly AI expenditure |
| BO-04 | Separate subscription costs from API usage |
| BO-05 | Avoid duplicate financial reporting |
| BO-06 | Provide a 12-month AI spending trend |
| BO-07 | Maintain traceability to original billing sources |
| BO-08 | Support management review and cost optimization |

## 4. Project Scope

### 4.1 In Scope

**Claude / Anthropic**

- Claude subscription billing
- Claude team/workspace seats
- Claude Code-related billing where separately identifiable
- Anthropic Console/API usage costs
- Invoice and export ingestion

**ChatGPT / OpenAI**

- ChatGPT subscription billing
- ChatGPT workspace/seat costs
- Codex-related charges where separately identifiable
- OpenAI API Platform costs
- Invoice and export ingestion

**Centralized Cost Reporting**

- Account and vendor identification
- Billing period tracking
- Currency and expense categorization
- Read-only API integration where supported
- PDF/CSV billing ingestion
- Duplicate detection and reconciliation
- Monthly spending summaries
- Historical spending trends
- Audit and source references
- Integration into GEIDIMCP-49

### 4.2 Out of Scope

- Modifying vendor billing records
- Automated subscription purchases or cancellations
- Unauthorized access to personal AI accounts
- Accessing unsupported or restricted vendor interfaces through security bypasses
- Forcing all AI usage through LiteLLM
- Developing a separate financial accounting platform
- ITQuoter supplier and quotation integration

## 5. Business Requirements

| ID | Requirement | Priority |
|---|---|---|
| BR-01 | Identify authorized AI billing accounts and their ownership | Must |
| BR-02 | Retrieve vendor billing information through officially supported APIs where available | Must |
| BR-03 | Support invoice/CSV import when APIs are unavailable | Must |
| BR-04 | Separate subscriptions, seats, and API-related expenses | Must |
| BR-05 | Preserve provider, account, currency, billing period, and source information | Must |
| BR-06 | Detect potentially duplicated transactions | Must |
| BR-07 | Reconcile vendor charges against financial records where accessible | Must |
| BR-08 | Show monthly actual AI costs | Must |
| BR-09 | Provide a 12-month spending history | Must |
| BR-10 | Distinguish company costs from approved personal-account expenses | Must |
| BR-11 | Display missing, incomplete, or unreconciled data | Must |
| BR-12 | Allow authorized reviewers to inspect original billing evidence | Must |
| BR-13 | Support scheduled API retrieval where the vendor permits it | Should |
| BR-14 | Provide vendor and category spending filters | Should |

## 6. Proposed Business Workflow

**Step 1 — Identify Billing Sources**

Document all authorized OpenAI and Anthropic accounts, billing entities, subscription types, and available access methods.

**Step 2 — Determine Collection Method**

Check whether each source supports an official read-only API, administrative export, PDF invoice, or CSV statement.

**Step 3 — Ingest Billing Records**

Retrieve supported API records or process authorized uploaded billing documents.

**Step 4 — Normalize Financial Data**

Standardize provider names, account identifiers, billing periods, currencies, expense categories, and amounts.

**Step 5 — Validate and Reconcile**

Detect duplicates, compare with financial records where available, identify inconsistencies, and retain original source references.

**Step 6 — Publish Reports**

Publish validated spending records into the existing GEIDIMCP-49 reporting system, clearly distinguishing confirmed values from incomplete or unresolved records.

## 7. Reporting Requirements

The dashboard should provide the following business information:

| Metric | Description |
|---|---|
| Total AI Expenses | Consolidated spending for the selected billing period |
| Claude Expenses | Total Anthropic-related expenses |
| OpenAI Expenses | Total OpenAI-related expenses |
| Subscription Costs | Seat and recurring subscription charges |
| API Costs | Provider-reported API costs |
| Monthly Trend | Spending changes by month |
| 12-Month History | Historical costs over the previous year |
| Unreconciled Charges | Records that cannot yet be matched or verified |
| Data Completeness | Missing accounts, unavailable sources, or incomplete periods |

**Important:** Actual vendor charges, prepaid credits, and usage-based cost metrics must be identified separately to prevent double-counting.

## 8. Security and Data Governance

The solution must:

- Use officially authorized access methods.
- Apply read-only permissions wherever supported.
- Store API credentials securely.
- Restrict billing information to authorized users.
- Require Paul's explicit permission for personal-account access.
- Distinguish Geidi expenses from other ventures.
- Preserve timestamps, source references, and reconciliation results.
- Avoid exposing sensitive billing credentials in reports or logs.

## 9. Dependencies and Potential Blockers

| Dependency / Risk | Impact | Mitigation |
|---|---|---|
| Missing administrative API credentials | Cannot enable automated retrieval | Request approved read-only credentials |
| Unsupported subscription billing APIs | Incomplete automated coverage | Use invoice/export ingestion |
| Unavailable historical invoices | Incomplete 12-month reports | Mark periods as unavailable |
| Multiple payment records | Duplicate cost reporting | Reconciliation and duplicate detection |
| Missing Finance/Xero access | Financial verification delayed | Validate against authorized provider statements first |
| Unclear account ownership | Personal/company costs mixed | Confirm billing ownership and authorization |
| Provider data discrepancies | Unreliable dashboard totals | Flag discrepancies for manual review |

## 10. Project Deliverables

**D-01 — Billing Source Inventory**

A documented list of authorized Claude and OpenAI accounts, billing plans, ownership, and available billing information.

**D-02 — API Capability Matrix**

A comparison of supported billing APIs, required access, limitations, and fallback methods.

**D-03 — Billing Ingestion Integration**

A working process for collecting vendor billing records through supported APIs or authorized file imports.

**D-04 — Data Validation and Reconciliation**

Expense normalization, duplicate handling, and source matching.

**D-05 — Dashboard Integration**

Verified AI cost information published through GEIDIMCP-49.

**D-06 — Testing and Handover Documentation**

Test evidence, known limitations, unresolved blockers, and implementation guidance.

## 11. Acceptance Criteria

The project may be submitted for acceptance when:

1. A capability matrix documents the available and unsupported billing methods for both providers.
2. At least one end-to-end billing ingestion flow has been validated for each provider, using an API or working export fallback as authorized.
3. Recorded billing amounts are reconciled with source invoices or statements.
4. Subscription, seat, and API-related expenses are clearly categorized.
5. Duplicate charges are identified and handled.
6. Personal and non-Geidi expenses are excluded or distinctly classified.
7. The existing GEIDIMCP-49 system displays monthly totals and 12-month historical reporting, with unavailable periods identified.
8. Test evidence and known limitations are documented.
9. Nicko reviews the reconciliation results and provides sign-off.

## 12. Recommended Delivery Phases

### Phase 1 — Discovery and Feasibility

- Inventory billing accounts.
- Identify available vendor APIs.
- Confirm required permissions.
- Document unsupported billing sources.
- Confirm dashboard integration points.

**Output:** Capability matrix, dependency list, and approved implementation approach.

### Phase 2 — Minimum Viable Billing Ingestion

- Implement invoice/CSV ingestion.
- Normalize expenses.
- Establish basic validation.
- Verify sample totals.

**Output:** Working billing ingestion prototype.

### Phase 3 — Automated Integration

- Implement supported read-only billing APIs.
- Add scheduled retrieval where permitted.
- Provide secure error handling and audit logs.

**Output:** Automated data collection for supported sources.

### Phase 4 — Reconciliation and Reporting

- Integrate with existing GEIDIMCP-49 spending records.
- Implement duplicate prevention.
- Publish monthly and historical reports.
- Conduct business validation.

**Output:** Consolidated and auditable AI cost reporting.

## 13. Outstanding Business Decisions

The following require confirmation before implementation is finalized:

- Which Claude and OpenAI accounts belong to Geidi?
- Which accounts have administrative API access?
- Should the first release prioritize PDF/CSV ingestion or automated API retrieval?
- Which existing GEIDIMCP-49 database schema and dashboard interfaces must be reused?
- Which Finance or Xero records are available for reconciliation?
- What is the required reporting currency and conversion policy?
- What historical billing data is accessible?
- Who is authorized to view uploaded invoices and cost reports?

## 14. Current Project Status

**Status:** Requirements and feasibility assessment / Plane ticket remains in Backlog.

**Confirmed from ticket:** Business outcome, required billing categories, implementation expectations, reconciliation requirements, acceptance criteria, and reviewer responsibilities.

**Not yet verified:** Vendor account permissions, actual API availability by Geidi account, billing data access, existing system architecture, completed integrations, and historical billing coverage.

This document defines the intended business requirements. It does not certify that integration or testing has already been completed.

## 15. Approval

| Role | Responsible | Approval |
|---|---|---|
| Business Stakeholder | Paul Ryan | Pending |
| Delivery Owner | Riel Jake Engaña | Pending |
| Technical Reviewer | Rey Nicko Santos | Pending |
| Financial Reconciliation | Christine / Finance | Pending |

---

**End of Business Requirements Document — GEIDIMCP-102**