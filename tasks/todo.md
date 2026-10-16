# GEIDIMCP-102 — Task List

> Architecture decisions, risks, and open questions: see `tasks/plan.md`.  
> Strict rules (decimal money, idempotent upserts, audit trail, no secrets in responses): enforced on every task.

---

## Phase 1 — Backend Foundation

### ~~Task 1: Project scaffold, ORM models, and config~~ ✅ DONE
**Description:** Create the full backend directory structure, `requirements.txt`, `pyproject.toml`, `app/config.py` (pydantic-settings from `backend.env`), `app/database.py` (async SQLAlchemy engine + session factory), and all six ORM models (`BillingAccount`, `BillingSource`, `BillingRecord`, `Reconciliation`, `SyncRun`, `AuditEvent`). All monetary columns must be `DECIMAL(20,6)`. No float types permitted anywhere.

**Acceptance criteria:**
- [ ] `backend/` directory exists with `requirements.txt`, `pyproject.toml`, `alembic.ini`, and `app/` package
- [ ] `app/config.py` loads all variables from `backend.env` via pydantic-settings; missing required vars raise a startup error
- [ ] `app/database.py` exposes `async_engine`, `AsyncSessionLocal`, and `get_db` dependency
- [ ] All six models defined in `app/models/`: `BillingAccount`, `BillingSource`, `BillingRecord`, `Reconciliation`, `SyncRun`, `AuditEvent`
- [ ] Every monetary column is `DECIMAL(20,6)` — confirmed by grep: zero occurrences of `Float` or `float` in models
- [ ] `app/main.py` starts with `uvicorn` and returns `{"status": "ok"}` at `GET /health`

**Verification:**
- [x] `cd backend && python -m pytest --collect-only` exits 0 (no import errors)
- [x] `python -c "from app.models import BillingAccount; print('ok')"` prints `ok`
- [x] Grep for `Float` in `app/models/` returns zero results

**Dependencies:** None

**Files likely touched:**
- `backend/requirements.txt`
- `backend/pyproject.toml`
- `backend/app/__init__.py`, `main.py`, `config.py`, `database.py`
- `backend/app/models/__init__.py`, `billing_account.py`, `billing_source.py`, `billing_record.py`, `reconciliation.py`, `sync_run.py`, `audit_event.py`

**Estimated scope:** Large (10+ files, all new)

---

### ~~Task 2: Alembic migration — 001_initial~~ ✅ DONE
**Description:** Configure Alembic with `alembic.ini` and `alembic/env.py` pointing at the async engine. Write migration `001_initial_schema` that creates all six tables with correct column types, foreign keys, indexes, and UNIQUE constraints for dedup keys. Down revision drops all tables cleanly.

**Acceptance criteria:**
- [ ] `alembic upgrade head` applies without error on a clean PostgreSQL database
- [ ] All six tables exist with correct column types (`DECIMAL(20,6)` for money, `UUID` PKs, `TIMESTAMP` for timestamps)
- [ ] `ai_billing_records` has UNIQUE constraint on `(provider, account_id, external_record_id)` for API dedup
- [ ] `ai_billing_sources` has UNIQUE constraint on `source_hash` for file dedup
- [ ] `alembic downgrade base` drops all six tables cleanly
- [ ] `alembic current` shows head revision after upgrade

**Verification:**
- [x] `alembic upgrade head` exits 0
- [x] `psql -c "\dt"` lists all six tables _(verified 2026-10-16: verified via information_schema: 6 tables + `users`)_
- [x] `alembic downgrade base && alembic upgrade head` round-trips cleanly _(verified 2026-10-16: run on the `_test` database)_

**Dependencies:** Task 1

**Files likely touched:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`

**Estimated scope:** Medium (3–4 files)

---

### ~~Task 3: Pydantic v2 schemas~~ ✅ DONE
**Description:** Define all request/response schemas in `app/schemas/`. Monetary fields must serialize as `str` (not `float`) in JSON responses to preserve decimal precision. Schemas cover all six entities plus reporting contracts (`SummaryResponse`, `TrendResponse` with coverage status per month).

**Acceptance criteria:**
- [ ] `app/schemas/` contains schemas for `billing_account`, `billing_source`, `billing_record`, `reconciliation`, `sync_run`, `reporting`
- [ ] All monetary fields use `Decimal` type in Python and serialize to JSON string (not number)
- [ ] `SummaryResponse` includes `period`, `currency`, `actual_expense` (str), `api_consumption_cost` (str), `providers` dict, `data_status` (`complete|partial|unavailable`), `unreconciled_records` count
- [ ] `TrendResponse` includes per-month coverage_status (`complete|partial|unavailable`) — never omits unavailable months
- [ ] No schema contains `api_key`, `secret`, or credential fields
- [ ] `model_config = ConfigDict(from_attributes=True)` on all ORM-backed schemas

**Verification:**
- [x] `python -c "from app.schemas.reporting import SummaryResponse; print('ok')"` prints `ok`
- [x] `python -m pytest --collect-only` exits 0
- [x] Grep for `float` in `app/schemas/` returns zero results

**Dependencies:** Task 1

**Files likely touched:**
- `backend/app/schemas/__init__.py`
- `backend/app/schemas/billing_account.py`, `billing_source.py`, `billing_record.py`, `reconciliation.py`, `sync_run.py`, `reporting.py`

**Estimated scope:** Medium (6 files)

---

### ~~Task 4: JWT authentication and role-based dependencies~~ ✅ DONE
**Description:** Implement `app/auth/` with JWT token creation/validation using `python-jose`, password hashing with `passlib`, a `User` model and seed (admin user), and FastAPI dependency functions `require_viewer`, `require_finance_reviewer`, `require_billing_admin`. Add `POST /api/auth/login` and `GET /api/auth/me` routes. Include a minimal `users` table (email, hashed_password, role enum).

**Acceptance criteria:**
- [ ] `POST /api/auth/login` with valid credentials returns `access_token` (JWT) and `token_type: bearer`
- [ ] `POST /api/auth/login` with invalid credentials returns 401
- [ ] `GET /api/auth/me` with valid Bearer token returns `{email, role}` — no password hash in response
- [ ] `require_viewer` dependency allows all three roles; `require_billing_admin` rejects viewer and finance_reviewer
- [ ] Roles: `viewer`, `finance_reviewer`, `billing_admin` (enum in JWT claim `role`)
- [ ] JWT secret loaded from `config.JWT_SECRET_KEY`; algorithm from `config.JWT_ALGORITHM`
- [ ] Alembic migration includes `users` table (or separate migration `002_users`)

**Verification:**
- [x] `curl -X POST /api/auth/login -d '{"email":"admin@geidi.com","password":"changeme"}'` returns 200 with token
- [x] `curl /api/auth/me -H "Authorization: Bearer <token>"` returns 200 with role
- [x] `curl /api/auth/me` without token returns 401
- [x] `python -m pytest tests/unit/test_auth.py` passes

**Dependencies:** Tasks 1, 2, 3

**Files likely touched:**
- `backend/app/auth/__init__.py`, `jwt.py`, `dependencies.py`
- `backend/app/models/user.py`
- `backend/app/routers/auth.py`
- `backend/alembic/versions/002_users.py`
- `backend/tests/unit/test_auth.py`

**Estimated scope:** Large (7 files)

---

### ✅ Checkpoint A — Backend Foundation
- [x] `alembic upgrade head` applies cleanly on fresh database
- [x] `GET /health` returns 200
- [x] `POST /api/auth/login` + `GET /api/auth/me` work end-to-end
- [x] Zero float/Float usage in models and schemas (grep check)
- [ ] **Human review before proceeding to Phase 2**

---

## Phase 2 — Backend Feature Slices

### ~~Task 5: Billing accounts CRUD router and service~~ ✅ DONE
**Description:** Implement `GET /api/ai-billing/accounts` (list) and `POST /api/ai-billing/accounts` (create). Requires `billing_admin` to create; `viewer` can list. `ownership_type` field validated against enum (`geidi|personal|other_venture`). `collection_method` validated against `api|invoice|csv`. AuditEvent written on every create/update. Credentials never stored in or returned from this table.

**Acceptance criteria:**
- [ ] `GET /api/ai-billing/accounts` returns list of accounts (no credential fields)
- [ ] `POST /api/ai-billing/accounts` creates account and writes AuditEvent in same transaction
- [ ] Viewer token cannot POST (403)
- [ ] `is_active` defaults to `true`; supports `PATCH /api/ai-billing/accounts/{id}` to deactivate
- [ ] Response schema never includes `api_key` or secret fields

**Verification:**
- [x] Create account via API, fetch list, verify account present
- [x] Attempt create with viewer token → 403
- [x] AuditEvent row exists in DB after create
- [x] `python -m pytest tests/unit/test_accounts.py` passes _(verified 2026-10-16: file added 2026-10-16)_

**Dependencies:** Tasks 1–4

**Files likely touched:**
- `backend/app/routers/accounts.py`
- `backend/app/services/accounts.py`
- `backend/tests/unit/test_accounts.py`

**Estimated scope:** Medium (3 files)

---

### ~~Task 6: File import pipeline — PDF/CSV ingestion router and processor~~ ✅ DONE
**Description:** Implement `POST /api/ai-billing/imports` (multipart upload), `GET /api/ai-billing/imports/{id}` (status + parsed preview). File processor: validate type/size, compute SHA-256 hash, detect duplicate upload (same hash → reject), extract fields (pdfplumber for PDF, csv.reader for CSV), flag uncertain monetary totals for review, store normalized `BillingSource` + `BillingRecord` rows with `validation_status=pending`. Write AuditEvent on upload.

**Acceptance criteria:**
- [ ] Supported file types: `pdf`, `csv` (from config `ALLOWED_UPLOAD_EXTENSIONS`)
- [ ] Max size enforced (`MAX_UPLOAD_SIZE_MB` from config)
- [ ] Duplicate file (same SHA-256) rejected with 409 and reference to existing source id
- [ ] Parsed records stored with `financial_basis` field populated (`invoiced|subscription|seat` etc.)
- [ ] Uncertain extraction (PDF totals unverifiable) → `validation_status=pending`; not posted as verified
- [ ] `GET /api/ai-billing/imports/{id}` returns parse result, confidence notes, and current status
- [ ] AuditEvent written on upload
- [ ] `invoice_storage_path` directory created if absent; files stored with UUID filename

**Verification:**
- [x] Upload a test CSV → 200 + source id returned _(verified 2026-10-16: returns 201 Created)_
- [x] Upload same CSV again → 409
- [x] Upload an oversized file → 413
- [x] `python -m pytest tests/unit/test_file_processor.py` passes (CSV parsing + dedup hash) _(verified 2026-10-16: file added 2026-10-16)_

**Dependencies:** Tasks 1–5

**Files likely touched:**
- `backend/app/routers/imports.py`
- `backend/app/services/ingestion/file_processor.py`
- `backend/tests/unit/test_file_processor.py`

**Estimated scope:** Large (5–6 files incl. fixtures)

---

### ~~Task 7: Provider sync connectors — OpenAI and Anthropic~~ ✅ DONE
**Description:** Implement `POST /api/ai-billing/sync/{provider}` (billing_admin only). Two connectors: `OpenAIConnector` calls `GET /v1/organization/costs`, `AnthropicConnector` calls `GET /v1/organizations/cost_report`. Both: read credential from env (not DB), handle pagination, rate-limit retry (exponential backoff), validate response schema, upsert records idempotently (ON CONFLICT DO UPDATE), write `SyncRun` row with status/coverage, write AuditEvent. If API is unreachable or credentials absent, write `SyncRun.status=blocked` and return 200 with `capability_status: blocked` — do not return 500.

**Acceptance criteria:**
- [ ] `OPENAI_BILLING_ENABLED=false` → sync returns `capability_status: disabled` without making API calls
- [ ] `ANTHROPIC_BILLING_ENABLED=false` → same
- [ ] Connector enabled but credentials empty → `capability_status: blocked` + `SyncRun.status=blocked`
- [ ] Re-running sync for same period does not create duplicate `BillingRecord` rows
- [ ] Pagination: all pages fetched before committing
- [ ] Rate-limit response (429) triggers retry with backoff (max 3 attempts)
- [ ] `SyncRun` row written on every call (success or failure)
- [ ] AuditEvent written per sync trigger
- [ ] No API key appears in any log line or response body

**Verification:**
- [x] With `OPENAI_BILLING_ENABLED=false`: sync returns 200 + `{capability_status: "disabled"}`
- [x] Re-trigger same sync twice → same number of BillingRecord rows (idempotent)
- [x] `python -m pytest tests/unit/test_connectors.py` passes (mocked HTTP responses) _(verified 2026-10-16: file added 2026-10-16; found + fixed 3 connector bugs)_

**Dependencies:** Tasks 1–5

**Files likely touched:**
- `backend/app/routers/sync.py`
- `backend/app/services/ingestion/openai_connector.py`
- `backend/app/services/ingestion/anthropic_connector.py`
- `backend/app/services/ingestion/base_connector.py`
- `backend/tests/unit/test_connectors.py`

**Estimated scope:** Large (6 files)

---

### ~~Task 8: Billing records router + normalization + deduplication service~~ ✅ DONE
**Description:** Implement `GET /api/ai-billing/records` with server-side pagination and filters (provider, account_id, period, category, financial_basis, ownership_type, validation_status). Implement `normalization.py` (standardise provider names, categories, financial basis) and `deduplication.py` (upsert logic, fallback dedup key for file imports). Category enum: `subscription|seat|api|credit|adjustment`. Financial basis enum: `invoiced|usage|payment|credit`.

**Acceptance criteria:**
- [ ] `GET /api/ai-billing/records?provider=openai&period=2026-10` returns paginated records
- [ ] `page` and `page_size` query params work; response includes `total`, `page`, `page_size`, `items`
- [ ] All monetary amounts in response are JSON strings, not numbers
- [ ] Filtering by `ownership_type=geidi` excludes personal accounts by default
- [ ] Normalization converts raw provider category strings to internal enum values
- [ ] Duplicate record (same dedup key) raises no DB error — upsert silently updates metadata

**Verification:**
- [x] Insert two records with same dedup key → DB has one row
- [x] `GET /api/ai-billing/records` with various filter combos returns correct subsets _(verified 2026-10-16: `reconciliation_status` filter was ignored — fixed)_
- [x] `python -m pytest tests/unit/test_normalization.py tests/unit/test_deduplication.py` pass

**Dependencies:** Tasks 1–5, 6, 7

**Files likely touched:**
- `backend/app/routers/records.py`
- `backend/app/services/normalization.py`
- `backend/app/services/deduplication.py`
- `backend/tests/unit/test_normalization.py`
- `backend/tests/unit/test_deduplication.py`

**Estimated scope:** Large (5 files)

---

### ~~Task 9: Reconciliation service and router~~ ✅ DONE
**Description:** Implement `GET /api/ai-billing/reconciliation` (finance_reviewer+). Service matches `BillingRecord` rows against `Reconciliation` rows by financial_reference. Returns matched/unmatched/partial items with variance. Implement `POST /api/ai-billing/reconciliation/{billing_record_id}/review` (finance_reviewer only) to approve or dispute a record. Write AuditEvent on every review action.

**Acceptance criteria:**
- [ ] Viewer token cannot access reconciliation endpoints (403)
- [ ] `GET /api/ai-billing/reconciliation` returns items grouped by `reconciliation_status` (matched/unmatched/partial)
- [ ] `variance` field = `expected_amount - observed_amount` as Decimal string
- [ ] `POST /api/ai-billing/reconciliation/{id}/review` with `action=approve` sets `validation_status=verified` on linked BillingRecord
- [ ] AuditEvent written on each review action with reviewer id and outcome
- [ ] `reconciliation_status=partial` when variance != 0 and within acceptable threshold

**Verification:**
- [x] Create a BillingRecord, create a Reconciliation with variance → GET shows `partial` status
- [x] Approve via POST → BillingRecord validation_status changes to `verified`
- [x] Viewer token → 403 on all reconciliation endpoints
- [x] `python -m pytest tests/unit/test_reconciliation.py` passes _(verified 2026-10-16: file added 2026-10-16)_

**Dependencies:** Tasks 1–5, 8

**Files likely touched:**
- `backend/app/routers/reconciliation.py`
- `backend/app/services/reconciliation.py`
- `backend/tests/unit/test_reconciliation.py`

**Estimated scope:** Medium (3 files)

---

### ~~Task 10: Reporting service — summary and 12-month trend~~ ✅ DONE
**Description:** Implement `GET /api/ai-billing/summary?period=2026-10` and `GET /api/ai-billing/trends?months=12`. Summary: total verified expense, per-provider breakdown, per-category breakdown, `data_status`, `unreconciled_records` count. Trends: one entry per month for last N months; each entry includes `period`, `actual_expense` (Decimal str), `coverage_status` (`complete|partial|unavailable`). Unavailable months are always included — never omitted. No cross-currency addition without approved FX (return per-currency subtotals if FX disabled).

**Acceptance criteria:**
- [ ] `GET /api/ai-billing/summary?period=2026-10` returns `SummaryResponse` with all required fields
- [ ] Missing provider data for a month → `data_status: partial`, not `complete`
- [ ] `GET /api/ai-billing/trends?months=12` returns exactly 12 entries (even for months with no data → `coverage_status: unavailable`)
- [ ] Monetary values in response are JSON strings
- [ ] `FX_CONVERSION_ENABLED=false` → provider totals returned per-currency, no single cross-currency sum
- [ ] Double-counting prevented: same charge cannot appear in both `api_consumption_cost` and `actual_expense` with different basis

**Verification:**
- [x] `GET /api/ai-billing/trends?months=12` returns array of length 12
- [x] Month with no records has `coverage_status: unavailable`, not `actual_expense: "0.000000"`
- [x] `python -m pytest tests/unit/test_reporting.py` passes (cost calc rules)

**Dependencies:** Tasks 1–5, 8, 9

**Files likely touched:**
- `backend/app/routers/reporting.py`
- `backend/app/services/reporting.py`
- `backend/tests/unit/test_reporting.py`

**Estimated scope:** Medium (3 files)

---

### ✅ Checkpoint B — Backend Feature Complete
- [x] All 8 API route groups respond correctly with auth enforcement _(verified 2026-10-16: covered by API tests incl. 403/401)_
- [x] `alembic upgrade head` still clean
- [x] Zero float/Float in entire backend codebase (grep check) _(verified 2026-10-16: only non-money: LLM `temperature`; `normalize_amount` accepts a float but converts via str→Decimal)_
- [x] No secret/key in any API response (manual spot check) _(verified 2026-10-16: all GET endpoints + log scanned for real key/secret values)_
- [x] Duplicate import → no inflated totals (manual test)
- [ ] **Human review before proceeding to Phase 3**

---

## Phase 3 — Backend Tests

### ~~Task 11: Complete unit test suite~~ ✅ DONE
**Description:** Fill out all unit tests covering: normalization edge cases (unknown category strings, missing currency), deduplication (API key, file fallback key, hash collision), cost calculation rules (credit+usage no double-count, partial month, mixed currency with FX disabled), auth role enforcement (all 3 role levels against all protected routes).

**Acceptance criteria:**
- [ ] `pytest tests/unit/` exits 0 with all tests passing
- [ ] Normalization: at least 6 cases (valid, unknown category, missing currency, credit adjustment, adjustment, subscription)
- [ ] Deduplication: at least 4 cases (new record, duplicate API key, duplicate file hash, different account same record_id)
- [ ] Reporting: at least 5 cases (full month, partial month, unavailable month, credit+usage separation, FX disabled multi-currency)
- [ ] Auth: viewer/finance_reviewer/billing_admin access checked against each protected route class
- [ ] Coverage ≥ 80% on `app/services/` (measured by `pytest --cov`)

**Verification:**
- [x] `pytest tests/unit/ --cov=app/services --cov-report=term-missing` exits 0 and shows ≥80% coverage _(verified 2026-10-16: 91%)_

**Dependencies:** Tasks 1–10

**Files likely touched:**
- `backend/tests/unit/test_normalization.py` (extend)
- `backend/tests/unit/test_deduplication.py` (extend)
- `backend/tests/unit/test_reporting.py` (extend)
- `backend/tests/unit/test_auth.py` (extend)
- `backend/tests/conftest.py`

**Estimated scope:** Medium (4–5 files)

---

### ✅ Checkpoint C — Backend Ready for Frontend Integration
- [x] `pytest tests/unit/ -v` exits 0, all green _(verified 2026-10-16: 139 passed)_
- [x] `uvicorn app.main:app --reload` starts without error
- [x] All 8 route groups accessible via curl/httpie with correct auth
- [ ] **Human review before proceeding to Phase 4**

---

## Phase 4 — Frontend Foundation

### ~~Task 12: Vite project scaffold, Tailwind, and axios API client~~ ✅ DONE
**Description:** Scaffold `frontend/` with Vite + Vue 3 (`npm create vite@latest frontend -- --template vue`). Install and configure: Tailwind CSS, PostCSS, autoprefixer, axios, pinia, vue-router, vue-chartjs, chart.js. Create `src/api/client.js` (axios instance with base URL from `VITE_API_BASE_URL`, Bearer token interceptor, 401 redirect). Create endpoint wrappers in `src/api/billing.js` (one function per backend route). Configure `vite.config.js` proxy `/api → http://localhost:8000`.

**Acceptance criteria:**
- [ ] `npm run dev` starts on port 5173 without error
- [ ] `npm run build` produces `dist/` without error
- [ ] Tailwind utility classes render correctly in a test component
- [ ] `src/api/client.js` automatically attaches `Authorization: Bearer <token>` from localStorage
- [ ] 401 response triggers `router.push('/login')` redirect
- [ ] `/api/health` proxied correctly to backend in dev

**Verification:**
- [x] `npm run build` exits 0
- [x] Browser: `http://localhost:5173` loads without console errors _(verified 2026-10-16: run on :5174 locally)_
- [x] Network tab: request to `/api/health` reaches backend _(verified 2026-10-16: health lives at `/health`, not `/api/health`)_

**Dependencies:** Tasks 1–4 (backend must be running for proxy test)

**Files likely touched:**
- `frontend/package.json`, `vite.config.js`, `index.html`
- `frontend/tailwind.config.js`, `postcss.config.js`
- `frontend/src/main.js`, `App.vue`
- `frontend/src/api/client.js`, `billing.js`

**Estimated scope:** Large (8 files, all new)

---

### ~~Task 13: Pinia stores — auth, accounts, records, reporting~~ ✅ DONE
**Description:** Implement four Pinia stores: `useAuthStore` (login action, JWT decode, role getter, logout), `useAccountsStore` (fetch/create accounts), `useRecordsStore` (fetch records with filter state, pagination), `useReportingStore` (fetch summary + trends, expose coverage status per month).

**Acceptance criteria:**
- [ ] `useAuthStore.login(email, password)` calls `POST /api/auth/login`, stores token, decodes role
- [ ] `useAuthStore.role` returns one of `viewer|finance_reviewer|billing_admin`
- [ ] `useReportingStore.trends` is always 12 entries; entries with `coverage_status: unavailable` preserved
- [ ] `useRecordsStore` exposes `filters` reactive object; `fetchRecords()` uses filters as query params
- [ ] Monetary values kept as strings in store state (no parseFloat)

**Verification:**
- [x] `useAuthStore.login` with mock API returns populated store _(verified 2026-10-16: Vitest added; `npm test`)_
- [x] `useReportingStore.trends.length === 12` after fetch with 12-month response

**Dependencies:** Task 12

**Files likely touched:**
- `frontend/src/stores/auth.js`
- `frontend/src/stores/accounts.js`
- `frontend/src/stores/records.js`
- `frontend/src/stores/reporting.js`

**Estimated scope:** Medium (4 files)

---

### ~~Task 14: Vue Router with auth guards and layout shell~~ ✅ DONE
**Description:** Configure `src/router/index.js` with routes for Login, Overview, BillingRecords, Imports, Integrations, Reconciliation. Navigation guard: redirect unauthenticated users to `/login`; redirect authenticated users away from `/login`. Role guard: Reconciliation and Integrations require `finance_reviewer` or `billing_admin`. Create `AppLayout.vue` (sidebar nav + slot) and `AppNav.vue` (links with active state, role-gated items).

**Acceptance criteria:**
- [ ] Navigating to `/` without token redirects to `/login`
- [ ] After login, `/login` redirects to `/`
- [ ] `/reconciliation` with viewer role shows 403 page or redirects
- [ ] Sidebar renders role-appropriate nav items only
- [ ] Browser back/forward works correctly after login redirect

**Verification:**
- [x] Manual: open `/` unauthenticated → redirected to `/login`
- [x] Login → redirected to `/`
- [x] Nav shows Reconciliation link only for finance_reviewer+

**Dependencies:** Tasks 12, 13

**Files likely touched:**
- `frontend/src/router/index.js`
- `frontend/src/layouts/AppLayout.vue`
- `frontend/src/components/AppNav.vue`
- `frontend/src/views/NotAuthorized.vue`

**Estimated scope:** Medium (4 files)

---

### ✅ Checkpoint D — Frontend Foundation
- [x] `npm run build` exits 0
- [x] Auth flow works end-to-end with running backend
- [x] Role-gated nav renders correctly for all three roles
- [ ] **Human review before proceeding to Phase 5**

---

## Phase 5 — Frontend Views

### ~~Task 15: Login view~~ ✅ DONE
**Description:** Implement `src/views/LoginView.vue`. Form: email + password fields, submit button, loading state, error display. On success: store token, redirect to `/`. On failure: show error message (never expose raw error details). No credentials in URL or logs.

**Acceptance criteria:**
- [ ] Form submits to `useAuthStore.login()`
- [ ] Loading spinner shown during request
- [ ] Invalid credentials show user-friendly error (not raw 401 body)
- [ ] Successful login redirects to `/`
- [ ] Form fields clear on failed attempt (no password persisted in state)

**Verification:**
- [x] Manual: login with wrong password → error shown, no redirect _(verified 2026-10-16: was broken (401 interceptor reloaded the page) — fixed)_
- [x] Login with correct credentials → redirect to Overview

**Dependencies:** Tasks 12–14

**Files likely touched:**
- `frontend/src/views/LoginView.vue`

**Estimated scope:** Small (1 file)

---

### ~~Task 16: Overview view — summary cards, trend chart, coverage banner~~ ✅ DONE
**Description:** Implement `src/views/OverviewView.vue` with: month selector (defaults to current month), `SummaryCards.vue` (total AI expense, OpenAI, Anthropic, subscription, API, unreconciled — all monetary values as strings with currency), `TrendChart.vue` (Chart.js bar chart, 12 months, unavailable months shown as distinct empty bars — not zero), `CoverageStatus.vue` (banner listing missing providers/months with action links). All amounts shown with ISO currency code. No cross-currency totals unless FX enabled.

**Acceptance criteria:**
- [ ] Month selector triggers re-fetch of summary and updates all cards
- [ ] `SummaryCards` shows 6 metric cards; amounts are formatted strings with currency (e.g. `$250.00 USD`)
- [ ] Trend chart shows 12 bars; months with `coverage_status: unavailable` rendered distinctly (e.g. striped/grey)
- [ ] Coverage banner visible when `data_status: partial`; hidden when `complete`
- [ ] No `NaN` or `[object Object]` renders for any monetary field
- [ ] Responsive: cards stack on mobile, chart scrolls horizontally if needed (FER-11)

**Verification:**
- [x] Manual with running backend: load Overview, confirm all 6 cards populate
- [x] Confirm 12-month chart renders with correct month labels
- [x] Confirm coverage banner appears when a provider is missing

**Dependencies:** Tasks 12–14

**Files likely touched:**
- `frontend/src/views/OverviewView.vue`
- `frontend/src/components/SummaryCards.vue`
- `frontend/src/components/TrendChart.vue`
- `frontend/src/components/CoverageStatus.vue`

**Estimated scope:** Large (4 files)

---

### ~~Task 17: Billing Records view — filterable table and source detail panel~~ ✅ DONE
**Description:** Implement `src/views/BillingRecordsView.vue`. Components: `FilterBar.vue` (dropdowns for provider, account, period, category, financial_basis, ownership, reconciliation_status — FER-05) and `BillingTable.vue` (paginated table with columns: provider, account, period, category, financial_basis, amount+currency, validation_status, reconciliation_status, source link). Clicking a row opens a side panel showing source reference details (FER-06, FER-09). Amounts rendered as strings. Ownership filter defaults to `geidi`.

**Acceptance criteria:**
- [ ] All 7 filter dropdowns present and functional; changing any filter re-fetches records
- [ ] Table shows correct columns with currency alongside amount
- [ ] Pagination controls (prev/next/page size) work and preserve active filters
- [ ] Row click opens source detail panel with account, document reference, and reconciliation evidence
- [ ] `ownership_type=geidi` applied by default (personal accounts not shown unless filter changed)
- [ ] Empty state: distinguishes "no charges found" from "no data available"

**Verification:**
- [x] Manual: apply provider filter → table updates
- [x] Apply period filter → correct month's records shown
- [x] Click row → source detail panel opens with correct data

**Dependencies:** Tasks 12–14, 16

**Files likely touched:**
- `frontend/src/views/BillingRecordsView.vue`
- `frontend/src/components/FilterBar.vue`
- `frontend/src/components/BillingTable.vue`

**Estimated scope:** Large (3 files)

---

### ~~Task 18: Imports view — upload panel, preview, validation, history~~ ✅ DONE
**Description:** Implement `src/views/ImportsView.vue`. Components: `UploadPanel.vue` (file picker limited to pdf/csv, max size from `VITE_ENABLE_BILLING_UPLOAD`, drag-drop, progress bar, provider/account selector before upload). After upload: show parsed preview table, validation errors/warnings, confirmation step before posting. Import history table (past imports with status, date, source id). Duplicate upload shows reference to original import, not a generic error.

**Acceptance criteria:**
- [ ] File picker restricted to pdf/csv; oversized files rejected client-side before upload
- [ ] Provider and account must be selected before upload allowed
- [ ] After upload: preview table shows extracted line items with amounts as strings
- [ ] Validation warnings highlighted; uncertain fields flagged as "requires review"
- [ ] Confirmation step required before records posted (`validation_status=pending` → `accepted`)
- [ ] Duplicate file (409 from server) shows "Already imported" with link to original import
- [ ] Import history table shows last N imports with status badge

**Verification:**
- [ ] Manual: upload a CSV → preview appears → confirm → record in history _(2026-10-16: preview + history work, but there is **no confirm step** — upload posts records immediately. Decide if a confirm step is required.)_
- [x] Re-upload same file → "Already imported" message shown
- [x] Upload wrong file type → rejected before network call

**Dependencies:** Tasks 12–14, 17

**Files likely touched:**
- `frontend/src/views/ImportsView.vue`
- `frontend/src/components/UploadPanel.vue`

**Estimated scope:** Large (2 files, but complex components)

---

### ~~Task 19: Integrations view and Reconciliation view~~ ✅ DONE
**Description:** Implement `src/views/IntegrationsView.vue` (account connection cards for OpenAI + Anthropic showing sync health, last run, capability_status; sync trigger button for billing_admin only; source coverage per account). Implement `src/views/ReconciliationView.vue` (finance_reviewer+ only; matched/unmatched/partial items table; variance column; approve/dispute actions; audit trail link; FER-08, FER-09, FER-10).

**Acceptance criteria:**
- [ ] Integrations view shows per-account cards with `capability_status` badge (enabled/disabled/blocked)
- [ ] Sync trigger button visible only for `billing_admin`; triggers `POST /api/ai-billing/sync/{provider}`
- [ ] Reconciliation view inaccessible to viewer (router guard already enforces; view shows 403 fallback if bypassed)
- [ ] Matched/unmatched/partial filter tabs work
- [ ] Approve action updates record status and refreshes table
- [ ] Variance column shows Decimal string with currency

**Verification:**
- [x] Manual (billing_admin): sync trigger button present and fires sync
- [ ] Manual (viewer): Integrations loads but sync button absent; Reconciliation shows 403 _(2026-10-16: viewer gets **403 on Integrations too** (route requires billing_admin) — stricter than this line. Decide which is intended.)_
- [x] Approve a record → status changes in table without full page reload _(verified 2026-10-16: table did not change — fixed: shows Verified/Disputed after review)_

**Dependencies:** Tasks 12–14, 16, 17

**Files likely touched:**
- `frontend/src/views/IntegrationsView.vue`
- `frontend/src/views/ReconciliationView.vue`

**Estimated scope:** Large (2 files)

---

### ✅ Checkpoint E — Project Complete
- [x] `npm run build` exits 0 (frontend)
- [x] `pytest tests/unit/ -v` exits 0 (backend)
- [x] Full user journey works: login → overview → filter records → upload invoice → reconcile
- [x] 12-month chart shows unavailable months distinctly (not as zero) _(verified 2026-10-16: shown as N/A)_
- [x] Duplicate import rejected with correct message
- [x] Zero floats in backend (grep), no secrets in any API response (spot check)
- [x] Viewer cannot access Reconciliation or trigger sync
- [ ] **Final human review and Nicko sign-off**

---

## Summary

| Phase | Tasks | Key Output |
|-------|-------|-----------|
| 1 — Backend Foundation | T1–T4 | Models, migration, schemas, JWT auth |
| 2 — Backend Features | T5–T10 | All 8 route groups + services |
| 3 — Backend Tests | T11 | Unit test suite ≥80% coverage |
| 4 — Frontend Foundation | T12–T14 | Scaffold, stores, router |
| 5 — Frontend Views | T15–T19 | All 6 views + components |
| **Total** | **19 tasks** | **Full-stack working application** |

---

## Verification log — 2026-10-16

Verification steps and checkpoint items above were re-run and ticked only where they were actually exercised.
Acceptance-criteria checklists were **not** re-audited line by line (117 still unticked); the tests below cover most of them.

**How to re-run**
- Backend: `cd backend && pytest tests/unit/ --cov=app/services` — API tests use a separate `<db>_test` database
  (or `TEST_DATABASE_URL`) and are skipped when it is unreachable. Result: 139 passed, 91% services coverage.
- Frontend: `cd frontend && npm test` (Vitest store tests + `node:test` report export tests), `npm run build`.

**Added:** `tests/conftest.py` (API test fixtures), `test_accounts.py`, `test_file_processor.py`, `test_connectors.py`,
`test_reconciliation.py`, `test_records_api.py`, `test_reporting_api.py`, `test_assistant_api.py`, `test_assistant_llm.py`,
`frontend/src/stores/__tests__/stores.test.js`; coverage now traces greenlets (`pyproject.toml`).

**Bugs found and fixed while verifying**
- OpenAI sync with a period always failed on Windows (`strftime("%s")`) — now a UTC timestamp.
- OpenAI paging never reached page 2 (httpx `params` replaces the URL query) — cursor sent as `page` param.
- Both connectors reported a run as *completed* after exhausting 429 retries — now fails; 5xx retried with backoff, 4xx not retried.
- `GET /records?reconciliation_status=` was silently ignored — now filters.
- Reconciliation: unknown record gave 500 (now 404); reviewing a record reconciled twice gave 500 (now uses the latest);
  table never showed the review outcome (API returns `record_validation_status`, UI shows Verified/Disputed).
- Login with a wrong password reloaded the page so the error was never shown (401 interceptor) — fixed.
- Deprecated `HTTP_413_REQUEST_ENTITY_TOO_LARGE` replaced.

**Open decisions (not ticked)**
- Task 18: Imports has no confirm step — records post immediately on upload when parsing is confident.
- Task 19: viewers get 403 on Integrations (route requires billing_admin); spec line says it should load without the sync button.
- Overview "Total AI Spend" card shows `0.00 USD` (labelled *unavailable*) for an empty month because `/summary` returns 0, not null.
- Connector response shapes are tested against mocks only; no real OpenAI/Anthropic admin keys have been used yet.
- All "Human review" gates and the final Nicko sign-off.

