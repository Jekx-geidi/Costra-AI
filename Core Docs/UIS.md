# User Interface & Experience Specification (UIXS)

**Product:** Geidi AI Spend Manager  
**Ticket:** GEIDIMCP-102 | **Parent:** GEIDIMCP-49  
**Version:** 1.0 (proposed) | **Date:** 2026-10-16  
**Status:** Draft UI specification; verify against existing GEIDIMCP-49 design system

> Companion to `UXS.md`. Here, **UIXS** means the combined interface-level design specification: layout, component behavior, presentation hierarchy and interaction details. User workflows and decision priorities are specified in UXS.

## 1. Visual direction

**Information-first enterprise financial UI:** professional, quiet, confident, primarily neutral surfaces. A dashboard is successful when Paul or Finance can immediately distinguish validated spend from incomplete/estimated data and act on exceptions—not when it has the most colorful cards.

- Use existing Geidi typography, logo, tokens and components if available.
- Proposed fallback palette (not verified brand specification): background `#F7F9FC`, surface `#FFFFFF`, ink `#172335`, secondary ink `#526174`, primary `#193B68`, verified `#24745C`, warning `#996500`, critical `#B42332`, border `#DFE5EC`.
- Favor ~65–75% neutral/white visual area; reserve color for actions and semantic state.
- Use consistent spacing: 4 / 8 / 12 / 16 / 24 / 32 px scale, 8–12 px radius, subtle borders; avoid heavy shadows.
- Use clear tabular numerals for currency, align numeric columns right, and never rely on color alone.

## 2. Screen priority and visible hierarchy

### 2.1 Overview: desktop (conceptual wireframe)

```text
+-----------------------------------------------------------------------+
| AI Spend  [Oct 2026 v]  [USD v]  Basis: Actual invoiced  [Export?]    |
| Coverage: PARTIAL | 4/5 sources | Updated 10:30 AM  [View gaps]       |
+-----------------------------------------------------------------------+
| ACTUAL AI EXPENSES         | UNRECONCILED          | CHANGE VS PRIOR    |
| $2,450.00                  | $185.00 / 3 items     | +8.2%              |
| 4/5 sources; partial       | [Review items]        | comparable periods |
+-----------------------------------------------------------------------+
| MONTHLY TREND (12 months)               | PROVIDER / CATEGORY SPLIT  |
| Chart, labels, source status            | Clear legend + totals     |
+-----------------------------------------------------------------------+
| ACTION REQUIRED: Missing invoice; failed sync; unmatched transaction   |
| [Review] [Upload] [Retry permitted source]                              |
+-----------------------------------------------------------------------+
| RECENT BILLING RECORDS: date | vendor | category | amount | status      |
+-----------------------------------------------------------------------+
```

Illustrative amounts above are *sample UI content only*, never real Geidi financial data.

### 2.2 Hierarchy order

1. **Context ribbon:** period, currency, accounting basis, completeness and data timestamp.
2. **Hero value:** actual expense in the largest useful numeric type, with exact status.
3. **Urgent exceptions:** unmatched value/count, missing sources and next action.
4. **Explanation:** trend and spending categories, clearly distinguished from the actual total.
5. **Evidence:** accessible records, invoices, API traces and audit history.

Do not position usage-only cost as a competing unlabeled “total.” When data is incomplete, display “Partial” adjacent to the number, not as a tiny footnote.

## 3. Typography and design tokens

| Token | Proposal | Intended use |
|---|---|---|
| `font.body` | Existing app sans-serif; fallback system UI | Labels, tables, details |
| `font.numeric` | Same font with tabular numerals | Currency, deltas, counts |
| `size.pageTitle` | 24–28 px / semibold | Page title |
| `size.kpiPrimary` | 30–38 px / semibold | Actual expense hero |
| `size.kpiSecondary` | 22–28 px / semibold | Unmatched charges, change |
| `size.body` | 14–16 px | Table and card descriptions |
| `size.meta` | 12–13 px | Timestamps; never sole location for critical warnings |
| `color.surface` | `#FFFFFF` | Cards and record surfaces |
| `color.page` | `#F7F9FC` | Workspace background |
| `color.primary` | `#193B68` | Main actions, links |
| `color.success` | `#24745C` | Verified state with text |
| `color.warning` | `#996500` | Partial, pending |
| `color.danger` | `#B42332` | Sync failed, material dispute |

Tokens are proposed and must be mapped to existing GEIDIMCP-49 tokens before coding. Text contrast must be checked to WCAG AA. Do not use pale warning text on white.

## 4. Primary components

### 4.1 KPI card

**Required:** label, amount, currency, selected period, data basis, completeness/status, optional comparison, drill-down target.

- Headline numbers remain on one line where practical; otherwise resize carefully without clipping.
- Explicit “Partial data” / “Verified” / “Pending review” label appears visibly on or near number.
- Comparison uses both absolute and percentage movement where meaningful; otherwise “Not comparable.”
- Currency symbols alone are not sufficient when multi-currency sources exist; add ISO currency code.
- Cards do not act like buttons unless affordance and keyboard semantics are clear.

### 4.2 Status chips

Use **label + icon + subtle background**. Approved vocabulary:

| Status | Meaning | Treatment |
|---|---|---|
| Verified | Source and validation complete | Muted green + check |
| Partial | Missing source or incomplete period | Amber + information |
| Pending review | Extracted or matched but not approved | Amber/neutral + clock |
| Unmatched | No verified financial match | Amber + alert |
| Disputed | Reviewer identified discrepancy | Muted red + alert |
| Failed sync | Provider retrieval failed | Red + retry/diagnostics |
| Unsupported | Provider lacks supported retrieval path | Neutral + export fallback |
| No data | No records for filter/period | Neutral; not zero |

### 4.3 Alerts and action queue

- Show issue **and** next action; example: “Anthropic invoice missing for October — Upload invoice.”
- Order by impact: financial discrepancy → missing coverage → failed sync → informational notes.
- Alerts link to a filtered destination; do not end in an undifferentiated page.
- Dismiss only low-impact notices; unresolved financial exceptions stay discoverable.

### 4.4 Charts

- Prefer line chart for monthly trend; stacked bars only when provider/category contribution adds useful context.
- Every data point has period, currency, basis and status on tooltip/focus interaction.
- Mark partial months with a visual pattern or textual marker and visible legend.
- Start monetary bar axes at zero when appropriate; no misleading crop.
- Put actual values in an accessible accompanying summary/table.
- Distinguish API usage from invoiced expense in separate series or views, never silently sum them.

### 4.5 Billing records table

Recommended columns:

`Invoice / Record ID | Vendor | Account | Billing period | Category | Amount (currency) | Basis | Reconciliation status | Source | Actions`

- Right-align numbers, fixed precision based on reporting policy, tabular numerals.
- Sticky table header for long datasets; visible filter result count and selected totals.
- Filters: date, provider, category, ownership, status, account, reporting basis.
- Sort must be predictable; show applied sort state.
- Row details reveal source, invoice line items, audit changes and reconciliation evidence.
- Use pagination or virtualization if volumes justify it; never mask incomplete loading as no results.

### 4.6 Invoice upload component

- Accept PDF and CSV as specified in backend policy; show allowed types and file-size limit from real config.
- Show account selection, drag/drop plus file picker, size/type validation and progress.
- Preview extracted vendor, invoice number, period, line amounts, taxes, credits and totals.
- Highlight uncertain fields in context; require a confirm step and preserve original file.
- Warn with link to existing charge for duplicate invoice rather than quietly creating a second charge.
- Avoid exposing uploaded invoice details to unauthorized roles.

### 4.7 Source health component

- Each provider/account displays: supported import method, connection status, last successful sync, last attempted sync, covered periods and next suggested action.
- Distinguish `not configured`, `unsupported`, `unavailable`, `permission denied`, and `temporarily failed`.
- Keep API token input in admin-only secure configuration; never echo raw secret in UI.
- For unsupported API access, show an explicit invoice/CSV fallback.

### 4.8 Reconciliation workspace

Two-pane desktop layout: selected issue queue on the left; comparison/evidence on the right. Show original vendor amount, matched accounting amount, currency, dates, variance, ownership, source IDs and reviewer notes.

Actions: `Match`, `Mark unresolved`, `Dispute`, `Request evidence`, or equivalent existing backend-supported operations. Require confirmation for material financial state changes and leave an audit record.

## 5. Responsive layouts

| Viewport | Layout | Must remain visible |
|---|---|---|
| Desktop `>= 1200px` | Sidebar + multi-column KPI/chart/table layout | Context, hero actual, exceptions, evidence links |
| Tablet `768–1199px` | Collapsible nav; 2-column KPIs; stacked analyses | Coverage, warnings and primary actions |
| Mobile `< 768px` | Single-column, compact sticky context, record details as cards/drawers | Currency, period, basis, completeness, actual total, urgent exception action |

**Mobile order:** period/context → coverage warning → actual spend → exceptions → trend → sources/records. Never truncate critical numbers or hide error status in a collapsed tooltip. Use accessible minimum touch targets ~44×44 px where practical.

## 6. Navigation and page contracts

| Page | Top visible content | Primary interaction | Fallback |
|---|---|---|---|
| Overview | Context, primary actual, completeness, exceptions | Investigate source/exception | Missing coverage explanation |
| Billing records | Filtered sum and result count | Filter/open source record | Clear empty state |
| Imports & sources | Account connection and last-refresh states | Upload or authorized sync | File-based ingestion |
| Reconciliation | Unmatched total and queue aging | Resolve/review exception | Leave unresolved with reason |
| Reports | Selected period, basis and coverage | View exportable summary | Partial-report disclaimer |
| Settings | Ownership, permissions, connection status | Configure authorized account | Explain access requirements |

Reuse route names already in GEIDIMCP-49 when they exist. Do not invent a second auth flow.

## 7. Interaction states and microcopy

| Event | UI text example | Behavior |
|---|---|---|
| No configured source | “No billing sources connected yet.” | Provide setup link only to admin |
| No records | “No billing records for this period.” | Suggest changing date or importing |
| Partial period | “Partial: 1 of 5 billing sources missing.” | Link to source coverage |
| Failed sync | “OpenAI sync failed. Last successful sync: [timestamp].” | Authorized retry plus diagnosis |
| Duplicate upload | “This invoice appears to be already imported.” | Link to existing invoice |
| Parse uncertainty | “Please verify the invoice total before confirming.” | Review highlighted fields |
| Pending review | “3 charges awaiting reconciliation.” | Direct filtered queue link |
| Missing comparative data | “Prior-period comparison unavailable.” | Omit misleading percent |
| Restricted access | “You do not have permission to view this billing record.” | Do not disclose protected metadata |

All timestamps need a user-visible timezone (default proposed: Asia/Manila). Avoid “live” or “real-time” without actually supporting freshness guarantees.

## 8. Accessibility and quality gates

- Keyboard reachable controls and visible focus ring; no hover-only essential details.
- Color must not be the only status signal; meaningful accessible labels for trends and charts.
- Screen readers announce filter changes, upload failures and reconciliation state transitions.
- Ensure text/background contrast meets WCAG 2.2 AA targets.
- Use proper form labels, inline errors and clear recovery instructions.
- Numeric values must not overlap controls at 320px width; test at 320, 375, 768, 1024, 1440px.
- Support zoom to 200% without hiding core financial context.
- Prevent destructive one-click reconciliation updates and optimistic misleading success feedback.
- Loading states preserve approximate layout without inventing amounts.

## 9. Implementation guidance for AI coding agents

1. Read BRD, TDD, FER, BER and `UXS.md` before implementation.
2. Audit existing GEIDIMCP-49 components, tokens, routes, role permissions and backend response contracts.
3. Create a reusable financial-context header (`period`, `currency`, `basis`, `coverage`, `asOf`).
4. Build shared status, KPI, alert, table, source health and review components.
5. Make all displayed numbers derive from verified backend responses; use demo fixtures only in tests or clearly marked mock environments.
6. Implement loading/empty/partial/error/restricted states before visual polish.
7. Test duplicate imports, missing sources and accounting-basis separation end-to-end.
8. Validate mobile and keyboard use before requesting design approval.

## 10. UI acceptance checklist

- [ ] Real and incomplete billing data are unmistakably different.
- [ ] Actual expense is the primary KPI, with period/currency/basis/coverage on screen.
- [ ] Unreconciled amounts and missing periods are easy to locate and actionable.
- [ ] Ledger values link to source evidence within authorized permissions.
- [ ] Tables align currencies and disclose filtering and row counts.
- [ ] Charts distinguish usage from actual expenses and label partial months.
- [ ] Invoice import handles errors, uncertainty and duplication clearly.
- [ ] Screen remains clear and usable at mobile, tablet and desktop sizes.
- [ ] Existing Geidi design tokens and navigation patterns are respected where available.
- [ ] No unauthorized financial information or credentials appear in frontend payloads.

## 11. Decisions for review

- Confirm official Geidi palette, logo, typography, component library.
- Confirm accounting basis, source coverage logic, comparison policy and reporting currency with Finance.
- Confirm which actions and labels map to existing backend-supported states.
- Confirm which roles can open original invoices and initiate reconciliation decisions.
- Confirm whether mobile has approval rights or review-only access.

---
**Design rule:** Highlight trustworthy totals, surface exceptions early, and make every displayed amount explainable.
