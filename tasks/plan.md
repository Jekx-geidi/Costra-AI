# Implementation Plan: GEIDIMCP-102 — Geidi AI Spend Manager

## Overview

Greenfield full-stack build of the Geidi AI Cost Tracking and Billing Integration system (COSTRA). The backend is Python/FastAPI with async SQLAlchemy + psycopg3 and Alembic migrations. The frontend is Vue 3 + Vite + Pinia + Tailwind. Specs live in `Core Docs/` (BRD.md, TDD.md, GEIDIMCP-102_FER_BER.md). No code exists yet — only documentation and two `.env` template files.

Tasks are tracked in `tasks/todo.md`. This document holds architecture decisions, risk table, and open questions.

---

## Architecture Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Async FastAPI + psycopg3 (native async)** | PostgreSQL + async from the start; psycopg3 is the TDD-specified driver. |
| 2 | **SQLAlchemy 2.0 ORM (mapped_column, DeclarativeBase)** | Modern async ORM; decimal column type enforced at the ORM layer to satisfy the "no floats for money" rule. |
| 3 | **Pydantic v2 schemas** | FastAPI default; model_validator for cross-field checks. |
| 4 | **Alembic for migrations** | Single initial migration covering all 6 tables; future changes are additive. |
| 5 | **python-jose + passlib for JWT** | Standard FastAPI auth pattern; roles embedded in JWT claim. |
| 6 | **Role enum: viewer / finance_reviewer / billing_admin** | Maps directly to FER-10 / TDD §10.1. |
| 7 | **DECIMAL(20,6) for all monetary columns** | TDD §8 and BER §3.3: never float. |
| 8 | **Dedup key: provider + account_id + external_record_id** | TDD §8.3 primary; fallback is provider + account_id + invoice_number + billing_period (file imports). |
| 9 | **Idempotent upserts via ON CONFLICT DO UPDATE** | BER-07: repeated API pulls or file re-imports must not inflate totals. |
| 10 | **AuditEvent written in the same transaction as every mutating operation** | TDD §10.3: every write is attributable. |
| 11 | **Coverage metadata per month (complete / partial / unavailable)** | FER-03 / BER-11: missing months shown as unavailable, never silently as zero. |
| 12 | **API secrets stored only in env / secrets manager; never returned in responses** | TDD §10.2 / BER §3.6. |
| 13 | **Vue 3 Composition API + `<script setup>`** | Current Vue idiom; consistent with Pinia stores. |
| 14 | **Axios with request/response interceptors** | Centralises auth token injection and 401 redirect. |
| 15 | **Chart.js via vue-chartjs** | Lightweight; sufficient for 12-month bar/line trend (FER-03). |
| 16 | **Vite proxy `/api` → `http://localhost:8000`** | Avoids CORS in dev; mirrors prod reverse-proxy pattern. |

---

## Dependency Graph

```
PostgreSQL (external)
    │
psycopg3 + SQLAlchemy 2.0
    │
app/models/ (6 ORM models)      ← T1
    │
Alembic 001_initial              ← T2
    │
app/config.py + database.py     ← T1 (same task)
    │
app/schemas/ (pydantic v2)       ← T3
    │
app/auth/ (JWT + role deps)      ← T4
    │
    ├── accounts router + service    ← T5
    ├── imports router + file proc   ← T6
    ├── sync router + connectors     ← T7
    ├── records router + norm/dedup  ← T8
    ├── reconciliation router + svc  ← T9
    └── reporting router (sum/trend) ← T10
              │
         Unit tests                  ← T11
              │
         ══════════ frontend boundary
              │
         src/api/ + axios             ← T12
              │
         src/stores/ (pinia)          ← T13
              │
         src/router/ (guards)         ← T14
              │
    ┌─────────┼──────────────────────┐
   T15       T16        T17         T18
  Login   Overview  BillingRec   Imports
              │         │
            T19: Integrations + Reconciliation views
```

---

## Strict Rules (from Core Docs)

- Monetary amounts: `DECIMAL(20,6)` — never `float` or `Numeric` without precision
- Idempotent ingestion: `INSERT … ON CONFLICT DO UPDATE` keyed on stable identifiers
- Financial basis: `invoiced | usage | payment | credit | adjustment` — separate columns/filters, never summed without explicit basis selection
- Coverage metadata: every monthly reporting row carries `coverage_status: complete | partial | unavailable`
- Audit trail: `AuditEvent` written in the **same DB transaction** as every insert/update/delete
- Secrets: provider API keys read from env only; never serialized to any schema response
- Personal/non-Geidi accounts: `ownership_type` field; reports filter by `ownership_type = geidi` by default

---

## Task List

See `tasks/todo.md` for the live checklist. Summary of phases:

### Phase 1 — Backend Foundation (T1–T4)
T1 · Project scaffold + models + config  
T2 · Alembic migration (001_initial)  
T3 · Pydantic schemas  
T4 · JWT auth + role dependencies  
**Checkpoint A**

### Phase 2 — Backend Feature Slices (T5–T10)
T5 · Billing accounts CRUD  
T6 · File import pipeline (PDF/CSV)  
T7 · Provider sync connectors (OpenAI + Anthropic)  
T8 · Billing records + normalization + deduplication  
T9 · Reconciliation service + router  
T10 · Reporting service (summary + 12-month trends)  
**Checkpoint B**

### Phase 3 — Backend Tests (T11)
T11 · Unit tests for normalization, dedup, cost calculation rules  
**Checkpoint C**

### Phase 4 — Frontend Foundation (T12–T14)
T12 · Vite project scaffold + Tailwind + axios client  
T13 · Pinia stores (auth, accounts, records, reporting)  
T14 · Vue Router with auth guards  
**Checkpoint D**

### Phase 5 — Frontend Views (T15–T19)
T15 · Login view  
T16 · Overview view (summary cards + 12-month trend chart + coverage banner)  
T17 · Billing Records view (filterable table + source detail panel)  
T18 · Imports view (upload + preview + validation + history)  
T19 · Integrations view + Reconciliation view  
**Checkpoint E (final)**

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI/Anthropic cost API endpoints unavailable for Geidi's account tier | High | Connectors return `capability_blocked` status; file import path always available |
| PDF extraction ambiguity (totals can't be proven) | High | Require human review before posting; `validation_status = pending` until confirmed |
| psycopg3 async driver version conflicts | Medium | Pin versions in requirements.txt; test migration on clean venv |
| DECIMAL precision loss via JSON serialization | Medium | Serialize monetary fields as strings in Pydantic schemas; document convention |
| Duplicate financial charge if dedup key is absent in provider response | High | Fallback key documented; `UNIQUE` constraint on dedup hash column |
| Vue Chart.js responsive layout on mobile | Low | Use `maintainAspectRatio: false` with container constraints (FER-11) |

---

## Open Questions (to confirm with Paul / Nicko before T7)

1. Which Geidi Claude/OpenAI accounts have administrative API access?
2. Is the headline management metric **invoiced expense**, **cash outlay**, or API consumption?
3. Reporting currency and FX conversion policy (AUD? USD?)?
4. Which Finance/Xero records are accessible for reconciliation (T9)?
5. Who may view uploaded invoice files (access control on storage)?
6. Is scheduled sync (BER-14) required for MVP or Phase 3?

---

## Definition of Done (project-wide)

Every task clears this bar before it is marked complete:

- [ ] Acceptance criteria all checked
- [ ] `pytest` (backend) or `npm run build` (frontend) exits 0
- [ ] No monetary field uses `float` anywhere in models, schemas, or service logic
- [ ] No API key or secret appears in any HTTP response body or log line
- [ ] AuditEvent written for every mutating operation
- [ ] Idempotent: re-running the same operation produces the same DB state
