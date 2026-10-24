# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | approved (2026-10-24, see Approval) |
| Repository / path | bookchaowalit/finance-cash-flow-api / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | AI approval 2026-10-24 under the owner's process (see Approval) |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / 2026-10-24 |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, there was no type check, the only tests were the generic contract suite, and the API stored a cash-flow plan whose `period_end` is before its `period_start`.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — A cash-flow period cannot end before it starts

- **Given** an owner with write permission
- **When** they create a plan with `period_start` 2026-12-01 and `period_end` 2026-11-30
- **Then** the API answers 422 `invalid_value` naming both fields; the same day for both dates is accepted
- **Test:** `tests/test_cashflow_validation.py::test_a_cash_flow_period_cannot_end_before_it_starts` · level: integration (API + throwaway PostgreSQL)

### AC-02 — Moving the end before the start is refused on update

- **Given** a plan for 2026-11-01 to 2026-11-30
- **When** a patch sets `period_end` to 2026-10-31
- **Then** the API answers 422 and the stored period and version stay unchanged; a patch that touches neither date still succeeds
- **Test:** `tests/test_cashflow_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-03 — Expected flows and reserve cannot be negative

- **Given** an owner with write permission
- **When** they create a plan with a negative `expected_inflow`, `expected_outflow` or `reserve_target`, then with 0
- **Then** the negative values are refused with 422 and 0 is created
- **Test:** `tests/test_cashflow_validation.py::test_expected_inflow_cannot_be_negative` · level: integration (API + throwaway PostgreSQL)

### AC-04 — Name and period are required

- **Given** a create request missing the name or a period date
- **When** it is sent
- **Then** the API answers 422; a name over 200 characters is refused too
- **Test:** `tests/test_cashflow_validation.py::test_period_start_is_required` · level: integration (API + throwaway PostgreSQL)

### AC-05 — New plans default to solo_empire, draft, THB, zero flows

- **Given** a create request with only a name and a period
- **When** the plan is created
- **Then** `owner_scope` is solo_empire, `status` is draft, `currency` is THB, `expected_inflow` and `expected_outflow` are 0, `reserve_target` is empty and `version` is 1
- **Test:** `tests/test_cashflow_defaults.py::test_expected_flows_default_to_zero_and_reserve_to_empty` · level: integration (API + throwaway PostgreSQL)

### AC-06 — Listing and stats follow the declared filters

- **Given** plans in several scopes and statuses
- **When** the owner lists by `owner_scope` or `status`, or asks for stats grouped by a filter or by a non-filter field
- **Then** only matching plans are listed, stats count per group, and grouping by `currency` is refused with 422
- **Test:** `tests/test_cashflow_queries.py::test_stats_refuse_a_field_that_is_not_a_filter` · level: integration (API + throwaway PostgreSQL)

### AC-07 — Changing a plan bumps its version once

- **Given** a draft plan at version 1
- **When** a patch activates it, then repeats unchanged values
- **Then** the version becomes 2 on the change and stays the same on a patch that changes nothing; a stale `expected_version` gets 409
- **Test:** `tests/test_cashflow_queries.py::test_activating_a_plan_bumps_its_version` · level: integration (API + throwaway PostgreSQL)

### AC-08 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `POST /v1/cashflow-plans`, `PATCH /v1/cashflow-plans/{id}` | changed | `period_end` before `period_start` → `422 {"error": "invalid_value", "fields": ["period_end", "period_start"]}` |
| `cell.yaml` | changed | new resource key `ranges: [[period_start, period_end]]` |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "56"` (measured 58.61% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_cashflow_validation.py::test_a_cash_flow_period_cannot_end_before_it_starts` | 073af27 · `.venv/bin/pytest -q tests/test_cashflow_validation.py::test_a_cash_flow_period_cannot_end_before_it_starts` · `assert 201 == 422` | CI run of the pushed tip | none |
| AC-02 | `tests/test_cashflow_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` | 073af27 · `.venv/bin/pytest -q tests/test_cashflow_validation.py::test_moving_the_end_before_the_start_is_refused_on_update` · `assert 200 == 422` | CI run of the pushed tip | none |
| AC-03 | `tests/test_cashflow_validation.py::test_expected_inflow_cannot_be_negative` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_cashflow_validation.py::test_period_start_is_required` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_cashflow_defaults.py::test_expected_flows_default_to_zero_and_reserve_to_empty` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_cashflow_queries.py::test_stats_refuse_a_field_that_is_not_a_filter` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_cashflow_queries.py::test_activating_a_plan_bumps_its_version` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_contract.py::test_numbers_fit_their_columns` | b6a9d2f · `.venv/bin/pytest -q -k numbers_fit` · `ValueError: Out of range float values are not JSON compliant: nan` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |

## Approval (2026-10-24)

| Field | Value |
|---|---|
| Checker | independent Claude reviewer subagent (`solo:solo-reviewer`, Sonnet, read-only, no maker context) |
| Approver | AI approval under the owner's process (approvals by the owner or AI with evidence; maker and checker are different agents). Recorded by Claude session oa-remainder on the owner's instruction "ทำที่เหลือให้หน่อย" (2026-10-24) |
| Verdict | **approved** |
| Tests run by the checker | .venv/bin/pytest -q --cov: 55 passed, 4 skipped |
| Evidence | test_cashflow_validation.py, test_cashflow_defaults.py, test_cashflow_queries.py; cell.yaml ranges; gate 56. |
