# User Experience Specification (UXS)

**Product:** Geidi AI Spend Manager  
**Ticket:** GEIDIMCP-102 | **Parent:** GEIDIMCP-49  
**Version:** 1.0 (proposed) | **Date:** 2026-10-16  
**Status:** Draft for Paul, Nicko, and Finance review

## 1. Experience objective

Enable Geidi decision-makers to answer, in order: **How much did we spend? Is the number complete and verified? What changed? What needs action? Where is the evidence?** The experience must prioritize trustworthy financial decisions over decorative UI.

The existing GEIDIMCP-49 application is the integration target. Screens, routes, terminology, access control, and component libraries below are *proposals*, not verified characteristics of the current codebase.

## 2. Audience and jobs to be done

| Persona | Primary decision | Needs visible immediately | Typical action |
|---|---|---|---|
| Management (Paul) | What is our AI spend and what changed? | Actual costs, comparison period, completeness, exceptions | Review trend; drill into abnormal cost |
| Technical reviewer (Nicko) | Is this data technically and financially traceable? | Sync/import health, variance, sources, audit trail | Investigate and sign off |
| Finance reviewer | Do amounts match statements and company ownership? | Unmatched charges, invoice dates, payment/usage basis | Match, approve, or dispute |
| Billing administrator | What sources need attention? | Failed syncs, missing periods, pending imports | Retry, upload, correct mapping |
| Authorized viewer | What can I safely read? | Clear filtered, permission-safe results | Inspect permitted totals |

**Permissions:** Reuse existing roles where possible; user-specific source documents and API credentials should never be exposed just because a dashboard is visible.

## 3. Information priority model

| Level | Question | Required presentation |
|---|---|---|
| P0 — Truth and trust | What period, currency, accounting basis, and coverage am I viewing? | Persistent page context and data-status label adjacent to headline amount |
| P1 — Decision | What is total actual spend, and how does it compare? | Leading KPI with current/previous comparison, no misleading percent where comparison missing |
| P1 — Action | Which amounts are unmatched, disputed, or missing? | Prominent exception summary and next action |
| P2 — Explanation | Which vendor/category caused the change? | Monthly trend, provider and category breakdown |
| P3 — Evidence | Which record and source support the figure? | Drill-down rows, invoice or provider reference, audit history |

**Non-negotiable:** An incomplete or unreconciled sum cannot look identical to a fully verified actual. Never infer a missing amount as zero. Never add API consumption values to invoices/payments as though they are independent charges.

## 4. Navigation and information architecture

Recommended minimal navigation, subject to existing GEIDIMCP-49 IA:

1. **Overview** — spend and coverage, exceptions, trend.
2. **Billing records** — queryable ledger and source detail.
3. **Imports & sources** — uploaded files, provider connections, sync runs, gaps.
4. **Reconciliation** — matches, exceptions, approvals.
5. **Reports** — monthly actuals and 12-month history, export (only when authorized).
6. **Settings / permissions** — administrator-only account metadata and configurations.

Prefer integrating these as a module in the existing app, not creating parallel navigation or a second product.

## 5. Critical journeys

### Journey A — Management spend review

**Entry:** Overview.  
**Path:** Select month → read verified/incomplete headline → inspect delta → review provider/category breakdown → open exception or line item → view source and method.  
**Success:** User can state total, basis, comparison period, coverage and unresolved exceptions without interpretation from a developer.

### Journey B — Import PDF/CSV invoice

**Entry:** Imports & sources → Upload invoice.  
**Path:** Select authorized billing account → upload validated file → detect duplicate → show extracted fields and confidence/validation flags → edit only permitted fields with traceability → preview total and tax/credits → confirm → queue or post verified record based on approval policy.  
**Success:** Accurate line items and an immutable reference to the original document; no duplicate posting on retry.

### Journey C — Provider API connection/sync

**Entry:** Imports & sources → provider details.  
**Path:** Check access/permissions → configure credential server-side → run connectivity check → select date range → sync → see progress and result counts → inspect errors/gaps.  
**Success:** Attributable billing records or an explicit unsupported/blocked status with file fallback. Never show credentials back to users.

### Journey D — Reconcile unexpected charge

**Entry:** Exception card or Reconciliation.  
**Path:** Select unmatched item → view source evidence + possible matches → compare amount, currency, date and ownership → match/dispute/mark unresolved with reason → log reviewer + timestamp.  
**Success:** No hidden assumptions and changes can be audited.

### Journey E — Review completeness

**Entry:** Overview coverage indicator.  
**Path:** Open coverage detail → see accounts and months covered, missing or partial → filter by source → navigate to failed sync/import.  
**Success:** User knows whether a total is partial, instead of treating incomplete data as complete.

## 6. Screen-by-screen UX priorities

| Screen | First thing visible | Primary action | Secondary detail |
|---|---|---|---|
| Overview | Actual spend **with currency, period, basis, coverage** | Investigate exceptions | Provider/category analysis and 12-month trend |
| Records | Filtered sum + active filters + record count | Inspect record | Source, adjustments, audit |
| Imports & sources | Source status, last refresh, missing coverage | Upload / sync (permission-gated) | Per-run errors and imported records |
| Reconciliation | Unmatched value/count and oldest outstanding | Review next exception | Match candidates and notes |
| Reports | Period and reporting basis; availability | Generate/view report | Month-by-month comparison |
| Account detail | Ownership, source capability, active state | Diagnose source | Configuration metadata; never secrets |

## 7. Core UX rules

- **Explicit labels:** Use “Actual expense,” “API usage cost,” “Payment,” “Credit,” and “Unreconciled,” not generic “Cost” where ambiguity exists.
- **Context attached to every total:** Display currency, month, coverage and calculation basis together.
- **Actionable warnings:** “October missing Anthropic invoice — Upload invoice” rather than “Something went wrong.”
- **No silent substitution:** Missing source = “Unavailable,” not `$0.00`.
- **Useful defaults:** Latest fully closed reporting period where appropriate; current month explicitly marked partial if shown.
- **Filtering:** All monetary KPIs, charts and tables update consistently; show active filters and reset action.
- **Explain calculations:** Drill down to category, records, invoice IDs and adjustments.
- **Non-destructive:** Import corrections and reconciliation decisions preserve audit history; do not silently overwrite original evidence.
- **Disclosure:** Restrict personal or other-venture data; require explicit Paul authorization for personal-account access.
- **No fake certainty:** Extraction uncertainties are flagged for review and never silently promoted to verified amounts.

## 8. States and recovery

| State | User sees | Recovery/action |
|---|---|---|
| Loading | Stable skeleton, same dimensions as finished figures | Avoid flashing `$0` placeholders |
| Empty (no accounts) | “No billing sources configured” | Setup action for authorized admin |
| Empty (no records) | “No records for this period” | Change period or import |
| Partial coverage | Sources/periods missing and which totals are affected | View gaps, upload, retry |
| Sync failure | Provider, last success, error class, retry availability | Retry or use export fallback |
| Bad invoice | Specific invalid fields, original document preserved | Correct or reject |
| Duplicate import | Existing document and amount reference | Open existing record; do not add charge |
| Unauthorized | Access denied without exposing confidential data | Request appropriate access |
| Reconciliation pending | Amount/count, aging, reviewer status | Open queue |
| Verified | Source-linked confirmation and reviewer timestamp | Read audit evidence |

## 9. Accessibility and responsive behavior

- Target WCAG 2.2 AA where feasible; readable contrast and focus states.
- All status colors are backed by text/icon; avoid red/green-only decisions.
- Keyboard-operable filters, menus, uploads and review actions; meaningful screen-reader labels.
- Use semantic currency/time formatting and retain enough decimal precision for source values.
- At narrow widths, preserve **period → completeness → actual total → exceptions → action** order; collapse detail progressively, never hide essential warning context.
- Table content may scroll horizontally when necessary, but actions and source access remain discoverable; offer record-detail view on mobile.
- Explicitly prevent clipped values, overlapping labels and inaccessible modals.

## 10. Success measures and acceptance scenarios

### Experience metrics (targets to validate in UAT)

- Reviewer identifies period, currency, data basis and incomplete coverage without opening a separate page.
- Finance can reach supporting invoice or API source from any included ledger amount in at most two detail interactions.
- Reviewer can identify all unresolved reconciliation items and assigned next actions.
- A duplicated invoice import never inflates the displayed actual.

### UAT scenarios

| ID | Scenario | Pass criteria |
|---|---|---|
| UX-01 | Monthly overview with verified sources | Clear totals, period, basis, currency, source drill-down |
| UX-02 | One provider missing this month | Incomplete flag prominent; no implied zero |
| UX-03 | Usage report plus related invoice | Distinct accounting views; no double count |
| UX-04 | Duplicate upload | Existing record linked; summary unaffected |
| UX-05 | Unmatched charge | Visible exception with clear review path |
| UX-06 | Unsupported vendor API | Actionable export/manual fallback |
| UX-07 | Mobile viewport | Financial headline, coverage, exceptions legible and reachable |
| UX-08 | Restricted role | No access to unauthorized invoices or account secrets |

## 11. Dependencies and open questions

1. Inspect existing GEIDIMCP-49 navigation, roles, data contracts and UI patterns.
2. Agree Finance’s definition of **monthly actual expense** versus usage, payment and credits.
3. Confirm reporting currency, exchange rate policy and billing period timezone.
4. Confirm account inventory and authorization, including any personal or other-venture sources.
5. Confirm approved roles for import correction, reconciliation and sign-off.
6. Decide whether PDF parsing supports scanned invoices and whether manual review is required for every import.

## 12. UXS definition of done

- [ ] Management, Finance, technical reviewer and admin paths validated with representatives.
- [ ] Every financial headline carries period, currency, financial basis and coverage.
- [ ] Missing, partial, failed and disputed data are visually and verbally differentiated.
- [ ] Import, source-sync and reconciliation journeys have recoverable states.
- [ ] Primary routes are keyboard usable and responsive at common mobile/tablet/desktop sizes.
- [ ] All outputs can be traced to permitted source evidence.

---
**Principle:** Make the truth visible first, the exception actionable second, and the evidence one click away.
