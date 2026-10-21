"""Defaults and uniqueness of a cash-flow plan."""

from cashflow_helpers import CASHFLOW_PLANS, create


def test_new_plan_defaults_to_solo_empire_draft_thb(client, owner):
    response = create(client, owner, name="Defaults")
    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan["owner_scope"] == "solo_empire"
    assert plan["status"] == "draft"
    assert plan["currency"] == "THB"
    assert plan["version"] == 1


def test_expected_flows_default_to_zero_and_reserve_to_empty(client, owner):
    plan = create(client, owner, name="Zeros").json()
    assert plan["expected_inflow"] == 0
    assert plan["expected_outflow"] == 0
    assert plan["reserve_target"] is None


def test_amounts_keep_their_decimal_value(client, owner):
    plan = create(
        client,
        owner,
        name="Decimals",
        expected_inflow=1234.56,
        expected_outflow=789.01,
        reserve_target=250.5,
    ).json()
    assert plan["expected_inflow"] == 1234.56
    assert plan["expected_outflow"] == 789.01
    assert plan["reserve_target"] == 250.5


def test_two_plans_may_share_a_name_and_period(client, owner):
    first = create(client, owner, name="Same")
    second = create(client, owner, name="Same")
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["id"] != second.json()["id"]


def test_an_import_keeps_the_old_id(client, owner):
    imported = create(client, owner, name="Imported", legacy_id=5151)
    assert imported.status_code == 201, imported.text
    assert imported.json()["id"] == 5151
    assert imported.json()["legacy_id"] == 5151
    found = client.get(f"{CASHFLOW_PLANS}/legacy/5151", headers=owner)
    assert found.status_code == 200, found.text
    assert found.json()["name"] == "Imported"
    assert create(client, owner, name="Again", legacy_id=5151).status_code == 409
