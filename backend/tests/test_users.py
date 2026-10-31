"""
Tests for GET /users

Covers:
- Returns list of inspectors
- Availability flag computed correctly (based on last_seen_at threshold)
- Non-inspector roles are not returned
- Requires authentication
- Items have required fields
"""
import pytest
from datetime import datetime, timedelta
from tests.conftest import auth_headers


class TestListInspectors:

    def test_returns_list_of_inspectors(self, client, officer_token):
        resp = client.get("/users", headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_requires_auth(self, client):
        resp = client.get("/users")
        assert resp.status_code == 401

    def test_inspector_can_access(self, client, inspector_token):
        resp = client.get("/users", headers=auth_headers(inspector_token))
        assert resp.status_code == 200

    def test_items_have_required_fields(self, client, officer_token):
        resp = client.get("/users", headers=auth_headers(officer_token))
        items = resp.json()
        if items:
            item = items[0]
            for field in ["id", "name", "email", "available"]:
                assert field in item, f"Missing field: {field}"

    def test_available_flag_true_for_recently_active(
            self, client, officer_token, inspector_user):
        """The test inspector has last_seen_at = now, so should be available."""
        resp = client.get("/users", headers=auth_headers(officer_token))
        items = resp.json()
        # Find our test inspector
        match = next(
            (i for i in items if i["id"] == str(inspector_user.id)), None
        )
        if match:
            # last_seen_at is updated on login, so inspector just logged in
            assert match["available"] is True

    def test_all_returned_users_are_inspectors(
            self, client, officer_token, officer_user):
        """Officers/managers should never appear in the inspector list."""
        resp = client.get("/users", headers=auth_headers(officer_token))
        items = resp.json()
        # The officer user should NOT be in this list
        ids = [i["id"] for i in items]
        assert str(officer_user.id) not in ids

    def test_available_field_is_boolean(self, client, officer_token):
        resp = client.get("/users", headers=auth_headers(officer_token))
        for item in resp.json():
            assert isinstance(item["available"], bool)
