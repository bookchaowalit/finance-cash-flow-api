"""Shared helpers for the cash-flow domain tests."""

from typing import Any

CASHFLOW_PLANS = "/v1/cashflow-plans"


def create(client: Any, owner: dict[str, str], **fields: Any) -> Any:
    body = {
        "name": "Plan",
        "period_start": "2026-11-01",
        "period_end": "2026-11-30",
        **fields,
    }
    return client.post(CASHFLOW_PLANS, headers=owner, json=body)
