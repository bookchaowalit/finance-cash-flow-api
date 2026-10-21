# Product

<!-- impeccable:product-schema 1 -->

## Platform

api

## Users

- The Solo Empire owner, through `life-dashboard-web` (finance page: active cash-flow plans that
  cover today), the cell's own MCP server (`cash-flow-mcp`) and the hosted tool hub
  (`platform-mcp-remote-worker`).
- Automations with an `empire-platform` token (for example `owner-mcp`), within the permissions
  `cash-flow.cashflow-plan:read|write|delete`.

## Product Purpose

The list of expected cash movement per period: for each period, the money expected to come in, the
money expected to go out and the reserve to keep, per owner scope, with the plan's status (draft,
active, closed, cancelled). It holds the plan only; real movements live in
`finance-transactions-api`.

Success: the period the owner is in has one active plan with its expected inflow, outflow and
reserve target, and a valid start and end date.

## Positioning

One capability, one service: its own API (Railway), its own database (Neon) with row-level
security per workspace, and authorization, executions and audit through `empire-platform`. It is
workspace-scoped, so the same service can serve other tenants without code changes.

## Operating Context

- Production: `https://cash-flow-api-production.up.railway.app` (`/health`), deployed by merging
  to `main` after CI.
- Data starts empty (created 2026-10-12 from the retired `finance_*` tables' fields); imports keep
  old ids in `legacy_id`.
- Monitored by `platform-uptime-worker` (probed hourly, because the service sleeps when idle);
  errors go to Sentry without personal data.

## Capabilities and Constraints

- `/v1/cashflow-plans`: list (filters `owner_scope`, `status`; ordered by id), stats (grouped by
  one of those filters), get, get-by-legacy-id, create (with `Idempotency-Key`), patch (with
  `expected_version`), delete.
- Rules: `name` (at most 200 characters), `period_start` and `period_end` are required;
  `expected_inflow` and `expected_outflow` default to 0 and `reserve_target` is empty by default;
  none of the three can be negative (zero is allowed); `owner_scope` (default `solo_empire`) and
  `status` (default `draft`) are fixed enums; `currency` defaults to THB and has at most 12
  characters; `period_end` cannot be before `period_start`, on create or on update (422
  `invalid_value` naming both fields; the same day for both is allowed).
- Plan names are not unique: two plans may share a name and period.
- Out of scope: actual inflow and outflow (computed from `finance-transactions-api`), forecasting,
  and overlap checks between plans.

## Measures

Proposed (nothing collects them yet):

- Whether the current month has an active plan, per owner scope.
- Gap between expected and actual net flow for closed plans (needs `finance-transactions-api`).
- 5xx rate and p95 latency on `/v1/cashflow-plans` (Sentry and uptime worker).
