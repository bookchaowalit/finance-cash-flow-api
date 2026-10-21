"""Listing, grouping and the lifecycle of a cash-flow plan."""

from cashflow_helpers import CASHFLOW_PLANS, create


def test_list_filters_by_owner_scope(client, owner):
    create(client, owner, name="Venture plan", owner_scope="venture")
    create(client, owner, name="Client plan", owner_scope="client")
    listed = client.get(CASHFLOW_PLANS, headers=owner, params={"owner_scope": "client"})
    assert listed.status_code == 200, listed.text
    scopes = {item["owner_scope"] for item in listed.json()["items"]}
    assert scopes == {"client"}


def test_list_filters_by_status(client, owner):
    create(client, owner, name="Closed plan", status="closed")
    create(client, owner, name="Cancelled plan", status="cancelled")
    listed = client.get(CASHFLOW_PLANS, headers=owner, params={"status": "cancelled"})
    assert listed.status_code == 200, listed.text
    assert {item["status"] for item in listed.json()["items"]} == {"cancelled"}


def test_list_filter_with_an_unknown_status_is_refused(client, owner):
    listed = client.get(CASHFLOW_PLANS, headers=owner, params={"status": "frozen"})
    assert listed.status_code == 422


def test_list_refuses_a_field_that_is_not_a_filter(client, owner):
    listed = client.get(CASHFLOW_PLANS, headers=owner, params={"name": "x"})
    assert listed.status_code == 422


def test_plans_are_listed_in_creation_order(client, owner):
    ids = [create(client, owner, name=f"Order {n}").json()["id"] for n in range(3)]
    listed = client.get(CASHFLOW_PLANS, headers=owner).json()["items"]
    assert [item["id"] for item in listed] == sorted(ids)


def test_stats_count_plans_per_status(client, owner):
    create(client, owner, name="Draft one")
    create(client, owner, name="Active one", status="active")
    stats = client.get(
        f"{CASHFLOW_PLANS}/stats", headers=owner, params={"group_by": "status"}
    )
    assert stats.status_code == 200, stats.text
    groups = stats.json()["groups"]
    assert groups["draft"] >= 1
    assert groups["active"] >= 1


def test_stats_count_plans_per_owner_scope(client, owner):
    create(client, owner, name="Shared plan", owner_scope="shared")
    stats = client.get(
        f"{CASHFLOW_PLANS}/stats", headers=owner, params={"group_by": "owner_scope"}
    )
    assert stats.status_code == 200, stats.text
    assert stats.json()["groups"]["shared"] == 1


def test_stats_refuse_a_field_that_is_not_a_filter(client, owner):
    stats = client.get(
        f"{CASHFLOW_PLANS}/stats", headers=owner, params={"group_by": "currency"}
    )
    assert stats.status_code == 422


def test_activating_a_plan_bumps_its_version(client, owner):
    plan = create(client, owner, name="Activate me").json()
    activated = client.patch(
        f"{CASHFLOW_PLANS}/{plan['id']}", headers=owner, json={"status": "active"}
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["status"] == "active"
    assert activated.json()["version"] == 2


def test_a_patch_that_changes_nothing_keeps_the_version(client, owner):
    plan = create(client, owner, name="Stable", expected_inflow=50).json()
    same = client.patch(
        f"{CASHFLOW_PLANS}/{plan['id']}",
        headers=owner,
        json={"name": "Stable", "expected_inflow": 50},
    )
    assert same.status_code == 200, same.text
    assert same.json()["version"] == 1


def test_a_stale_expected_version_is_refused(client, owner):
    plan = create(client, owner, name="Versioned").json()
    path = f"{CASHFLOW_PLANS}/{plan['id']}"
    assert client.patch(path, headers=owner, json={"notes": "a"}).status_code == 200
    stale = client.patch(
        path, headers=owner, json={"notes": "b", "expected_version": 1}
    )
    assert stale.status_code == 409


def test_a_negative_amount_is_refused_on_update(client, owner):
    plan = create(client, owner, name="Keep amount", expected_outflow=75).json()
    path = f"{CASHFLOW_PLANS}/{plan['id']}"
    refused = client.patch(path, headers=owner, json={"expected_outflow": -5})
    assert refused.status_code == 422
    assert client.get(path, headers=owner).json()["expected_outflow"] == 75


def test_a_required_field_cannot_be_cleared(client, owner):
    plan = create(client, owner, name="Needs dates").json()
    refused = client.patch(
        f"{CASHFLOW_PLANS}/{plan['id']}", headers=owner, json={"period_end": None}
    )
    assert refused.status_code == 422


def test_the_reserve_target_can_be_set_later(client, owner):
    plan = create(client, owner, name="Reserve later").json()
    updated = client.patch(
        f"{CASHFLOW_PLANS}/{plan['id']}", headers=owner, json={"reserve_target": 900}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["reserve_target"] == 900
    assert updated.json()["version"] == 2


def test_deleting_a_plan_removes_it(client, owner):
    plan = create(client, owner, name="Short lived").json()
    path = f"{CASHFLOW_PLANS}/{plan['id']}"
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404
    assert client.delete(path, headers=owner).status_code == 404
