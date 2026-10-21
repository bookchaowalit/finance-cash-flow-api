"""What cash flow refuses: missing fields, unknown kinds, negative amounts, backwards periods."""

from cashflow_helpers import CASHFLOW_PLANS, create


def test_name_is_required(client, owner):
    response = client.post(
        CASHFLOW_PLANS,
        headers=owner,
        json={"period_start": "2026-11-01", "period_end": "2026-11-30"},
    )
    assert response.status_code == 422


def test_name_is_limited_to_200_characters(client, owner):
    assert create(client, owner, name="x" * 201).status_code == 422
    assert create(client, owner, name="y" * 200).status_code == 201


def test_period_start_is_required(client, owner):
    response = client.post(
        CASHFLOW_PLANS,
        headers=owner,
        json={"name": "No start", "period_end": "2026-11-30"},
    )
    assert response.status_code == 422


def test_period_end_is_required(client, owner):
    response = client.post(
        CASHFLOW_PLANS,
        headers=owner,
        json={"name": "No end", "period_start": "2026-11-01"},
    )
    assert response.status_code == 422


def test_a_date_must_be_a_real_calendar_date(client, owner):
    response = create(client, owner, name="Bad date", period_end="2026-13-01")
    assert response.status_code == 422


def test_expected_inflow_cannot_be_negative(client, owner):
    assert create(client, owner, name="Neg in", expected_inflow=-1).status_code == 422
    assert create(client, owner, name="Zero in", expected_inflow=0).status_code == 201


def test_expected_outflow_cannot_be_negative(client, owner):
    assert (
        create(client, owner, name="Neg out", expected_outflow=-0.5).status_code == 422
    )
    assert create(client, owner, name="Zero out", expected_outflow=0).status_code == 201


def test_reserve_target_cannot_be_negative(client, owner):
    assert (
        create(client, owner, name="Neg reserve", reserve_target=-10).status_code == 422
    )
    assert (
        create(client, owner, name="Zero reserve", reserve_target=0).status_code == 201
    )


def test_owner_scope_must_be_a_known_scope(client, owner):
    response = create(client, owner, name="Odd scope", owner_scope="family")
    assert response.status_code == 422


def test_status_must_be_a_known_status(client, owner):
    response = create(client, owner, name="Odd status", status="frozen")
    assert response.status_code == 422


def test_currency_code_is_at_most_12_characters(client, owner):
    assert create(client, owner, name="Long ccy", currency="C" * 13).status_code == 422
    assert create(client, owner, name="USD plan", currency="USD").status_code == 201


def test_unknown_fields_are_refused(client, owner):
    response = create(client, owner, name="Extra", colour="red")
    assert response.status_code == 422


def test_a_cash_flow_period_cannot_end_before_it_starts(client, owner):
    backwards = create(
        client,
        owner,
        name="Backwards",
        period_start="2026-12-01",
        period_end="2026-11-30",
    )
    assert backwards.status_code == 422, backwards.text
    assert backwards.json()["detail"] == {
        "error": "invalid_value",
        "fields": ["period_end", "period_start"],
    }
    one_day = create(
        client,
        owner,
        name="One day",
        period_start="2026-12-01",
        period_end="2026-12-01",
    )
    assert one_day.status_code == 201, one_day.text


def test_moving_the_end_before_the_start_is_refused_on_update(client, owner):
    plan = create(client, owner, name="November", period_start="2026-11-01").json()
    path = f"{CASHFLOW_PLANS}/{plan['id']}"
    refused = client.patch(path, headers=owner, json={"period_end": "2026-10-31"})
    assert refused.status_code == 422, refused.text
    unchanged = client.get(path, headers=owner).json()
    assert unchanged["period_end"] == "2026-11-30"
    assert unchanged["version"] == 1
    # A patch that touches neither date still works.
    renamed = client.patch(path, headers=owner, json={"name": "Renamed"})
    assert renamed.status_code == 200, renamed.text
