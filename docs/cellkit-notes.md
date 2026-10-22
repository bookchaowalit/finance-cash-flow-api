# cellkit notes

`src/cellkit/` is this service's own framework code. It was first generated from `cell.yaml` by the shared generator (solo-cell-kit, retired 2026-10-12), and it is changed here only. Nothing upstream is synced; other cells keep their own copies (owner decision 2026-10-21).

## Before Wave 2

At `bec5bef` this copy was the finance copy: already reported a failed inline publish to Sentry; nosemgrep/noqa comments in the finance wording. In a comparison of all 24 cell copies (AST, comments and formatting ignored) there were only two behaviours: with or without Sentry `capture` on a failed inline publish.

## Changed in Wave 2 (2026-10-22)

- Strict typing (mypy strict on `cellkit.*` except the contract suite) and Ruff fixes; no behaviour change.
- `ranges` resource key: a write that leaves `[start, end]` both set must keep start <= end (422 `invalid_value`); only a patch that changes one of them is checked. No schema change.
- Integers are bounded to their column (`int` = 32-bit, `bigint`/`ref` = 64-bit) and real fields refuse NaN/Infinity: 422 instead of a 500 or a silent NULL. The 422 handler makes such inputs JSON-safe.
- A failed inline publish is passed to Sentry `capture()` as well as logged.
- Contract tests for each of these (`src/cellkit/contract.py`).

Commits touching `src/cellkit/` or `cell.yaml`:

- `e3ac037 fix: refuse integers past their column and NaN/Infinity reals with 422`
- `b6a9d2f test: integers past their column and non-finite reals must be refused with 422 (red)`
- `31a92c5 chore: L2 baseline; cash-flow periods must not end before they start`

## Fixes per need of this cell

| Fix | Does this cell need it? | Evidence |
|---|---|---|
| Inline publish failure → Sentry | no: no resource has graph events, so the inline publisher never runs. The line is in the copy but inert. | — |
| `ranges` rule | yes: `cashflow-plan` period_start..period_end | 073af27 · `.venv/bin/pytest -q tests/test_cashflow_validation.py::test_a_cash_flow_period_cannot_end_before_it_starts` · `assert 201 == 422` |
| Column limits / finite reals | yes: `cashflow-plan.expected_inflow`, `cashflow-plan.expected_outflow`, `cashflow-plan.reserve_target` | b6a9d2f · `.venv/bin/pytest -q -k numbers_fit` · `ValueError: Out of range float values are not JSON compliant: nan` |

## Deliberately not applied

- No other fix was skipped: no cell copy had a fix this one lacks after Wave 2, and there were no domain-specific differences to keep (the other differences were comments and formatting).

Change this code here, with a failing test first (ADR-0004). Records: `specs/` (SPEC-001 red/green log).
