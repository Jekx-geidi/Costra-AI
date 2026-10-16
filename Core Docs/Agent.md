# Agent.md — Repository Agent Instructions

## Mission

Implement **GEIDIMCP-102**, the Claude/Anthropic + ChatGPT/OpenAI billing integration supporting the existing **GEIDIMCP-49** AI spend reporting platform. Treat the BRD/TDD/FER/BER as proposed requirements and validate them against actual repository code.

## Before changing code

1. Inspect the repository structure, package manifests, existing API routes, authentication, database migrations, tests, and deployment.
2. Locate existing GEIDIMCP-49 spending entities and chart/reporting components; reuse them instead of creating a parallel platform.
3. State which facts are confirmed by code and which remain assumptions.
4. Identify the smallest independently testable change and implement it without unrelated refactors.
5. If blocked by missing vendor access, use mocks/fixtures for development and document the limitation; do not claim live integration success.

## Scope and priority

1. Authorized billing-source inventory and capability matrix.
2. Secure PDF/CSV invoice ingestion and deterministic validation.
3. API retrieval from supported vendor billing endpoints with least-privilege credentials.
4. Data model distinguishing account ownership, source, currency, billing period, financial basis, and provenance.
5. Idempotent storage, duplicate detection, credit handling, reconciliation.
6. Integrate validated monthly totals and 12-month trends into existing dashboard.
7. Tests, evidence, operational notes, and reviewer handover.

Do not work on ITQuoter suppliers or quotes as part of this ticket.

## Non-negotiable engineering rules

- **Source fidelity:** Never manufacture invoices, provider records, cost values, API responses, or verification outcomes.
- **Financial integrity:** Separate cash payments, prepaid credits, invoiced charges, and consumed API usage. Never double-count across categories.
- **Authorization:** Use only official, authorized read-only interfaces. Do not bypass provider controls or access personal accounts without Paul's explicit permission.
- **Secrets:** Never put admin keys in client code, commit them, log them, or embed them in test fixtures. `.env` must remain ignored.
- **Money:** Use fixed-precision decimals, explicit currency codes, and documented rounding/FX rules; no floating-point money math.
- **Idempotency:** Repeated imports/syncs must not duplicate financial records. Handle retries and partial pages safely.
- **Provenance:** Every figure needs source account, source document/API reference, timestamps, and validation status.
- **Safety:** Validate file uploads, restrict file access, sanitize logs, and use existing authorization patterns.
- **Compatibility:** Follow the *actual* tech stack and naming conventions; do not introduce FastAPI, React, or PostgreSQL merely because they were suggested in planning documents.

## Backend implementation guardrails

- Isolate vendor connectors from ingestion, normalization, persistence, and reporting services.
- Use robust pagination, timeout handling, bounded retries, and error classification.
- Keep original source data/references accessible under company retention/access policy.
- Mark unsupported or incomplete source periods explicitly.
- Provide invoice/import review before uncertain extracted values become verified totals.
- Match invoice/payment/usage records rather than summing all three types together.

## Frontend implementation guardrails

- Extend existing dashboard patterns and components.
- Show source coverage, last sync, missing data, reconciliation status, and selected currency/period.
- Separate API usage charts from invoiced/actual expense charts where financial basis differs.
- Make upload errors, access-denied states, loading states, and partial data obvious.
- Never expose provider administration credentials or raw sensitive documents publicly.

## Test and review protocol

- Add focused unit tests for invoice parsing, categories, decimals, refunds, duplicate records, and reconciled totals.
- Add integration tests with synthetic fixtures; use real financial source evidence only in authorized private environments.
- Run the project's established formatter/linter/tests and report exact commands/results.
- Document verified work, gaps, blockers, migrations, and manual steps in the handover.
- Do not describe untested features as complete; seek Nicko's review/sign-off for acceptance.

## Response format for coding agents

For each substantial work session, provide: **What changed**, **Files touched**, **Tests run/results**, **Assumptions**, **Blockers**, and **Next step**. Keep descriptions concrete and distinguish implementation from proposals.
