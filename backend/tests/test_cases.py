"""
Tests for /cases endpoints:

POST   /cases                  - create case (officer only)
GET    /cases                  - list cases (role-filtered)
GET    /cases/mine             - inspector-only shortcut
GET    /cases/{id}             - case detail
GET    /cases/{id}/audit-log   - audit trail
"""
import pytest
from uuid import uuid4
from tests.conftest import auth_headers


class TestCreateCase:

    def test_officer_can_create_case(
            self, client, officer_token,
            test_consumer, test_risk_score, inspector_user):
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(inspector_user.id),
            "assignment_note": "Auto-test case creation",
        }, headers=auth_headers(officer_token))
        assert resp.status_code == 201
        data = resp.json()
        assert "case_id" in data
        assert data["status"] == "assigned"

    def test_create_case_requires_auth(
            self, client, test_consumer, test_risk_score, inspector_user):
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(inspector_user.id),
            "assignment_note": "No auth",
        })
        assert resp.status_code == 401

    def test_inspector_cannot_create_case(
            self, client, inspector_token,
            test_consumer, test_risk_score, inspector_user):
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(inspector_user.id),
            "assignment_note": "Inspector trying to create",
        }, headers=auth_headers(inspector_token))
        assert resp.status_code == 403

    def test_invalid_consumer_id_returns_404(
            self, client, officer_token, test_risk_score, inspector_user):
        resp = client.post("/cases", json={
            "consumer_id": str(uuid4()),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(inspector_user.id),
            "assignment_note": "Bad consumer",
        }, headers=auth_headers(officer_token))
        assert resp.status_code == 404

    def test_invalid_risk_score_id_returns_404(
            self, client, officer_token, test_consumer, inspector_user):
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(uuid4()),
            "assigned_to": str(inspector_user.id),
            "assignment_note": "Bad risk score",
        }, headers=auth_headers(officer_token))
        assert resp.status_code == 404

    def test_invalid_inspector_id_returns_404(
            self, client, officer_token, test_consumer, test_risk_score):
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(uuid4()),
            "assignment_note": "Bad inspector",
        }, headers=auth_headers(officer_token))
        assert resp.status_code == 404

    def test_cannot_assign_to_officer_as_inspector(
            self, client, officer_token,
            test_consumer, test_risk_score, officer_user):
        """Officers cannot be assigned as field inspectors."""
        resp = client.post("/cases", json={
            "consumer_id": str(test_consumer.id),
            "risk_score_id": str(test_risk_score.id),
            "assigned_to": str(officer_user.id),  # officer, not inspector
            "assignment_note": "Invalid assignment",
        }, headers=auth_headers(officer_token))
        assert resp.status_code == 404  # Inspector not found with that role

    def test_missing_required_fields_returns_422(
            self, client, officer_token):
        resp = client.post("/cases", json={},
                           headers=auth_headers(officer_token))
        assert resp.status_code == 422


class TestListCases:

    def test_officer_sees_all_cases(self, client, officer_token, test_case):
        resp = client.get("/cases", headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        # The test_case should be present
        ids = [item["id"] for item in data["items"]]
        assert str(test_case.id) in ids

    def test_inspector_sees_only_own_cases(
            self, client, inspector_token, inspector_user, test_case):
        resp = client.get("/cases", headers=auth_headers(inspector_token))
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["inspector_name"] is not None

    def test_list_requires_auth(self, client):
        resp = client.get("/cases")
        assert resp.status_code == 401

    def test_filter_by_status_assigned(self, client, officer_token, test_case):
        resp = client.get("/cases?status_filter=assigned",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["status"] == "assigned"

    def test_filter_by_invalid_status_returns_400(self, client, officer_token):
        resp = client.get("/cases?status_filter=INVALID",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 400

    def test_pagination_works(self, client, officer_token):
        resp = client.get("/cases?page=1&page_size=5",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5

    def test_items_have_required_fields(self, client, officer_token, test_case):
        resp = client.get("/cases", headers=auth_headers(officer_token))
        items = resp.json()["items"]
        if items:
            item = items[0]
            for field in ["id", "status", "created_at",
                          "consumer_external_ref", "feeder", "risk_band"]:
                assert field in item, f"Missing field: {field}"


class TestGetMyCases:

    def test_inspector_can_access_mine(self, client, inspector_token):
        resp = client.get("/cases/mine", headers=auth_headers(inspector_token))
        assert resp.status_code == 200

    def test_officer_cannot_access_mine(self, client, officer_token):
        resp = client.get("/cases/mine", headers=auth_headers(officer_token))
        assert resp.status_code == 403

    def test_mine_requires_auth(self, client):
        resp = client.get("/cases/mine")
        assert resp.status_code == 401


class TestCaseDetail:

    def test_officer_can_get_case_detail(
            self, client, officer_token, test_case):
        resp = client.get(f"/cases/{test_case.id}",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(test_case.id)

    def test_detail_has_all_fields(self, client, officer_token, test_case):
        resp = client.get(f"/cases/{test_case.id}",
                          headers=auth_headers(officer_token))
        data = resp.json()
        expected_fields = [
            "id", "status", "assignment_note", "created_at",
            "consumer_id", "consumer_external_ref", "consumer_address",
            "feeder", "meter_type", "risk_score", "risk_band",
            "explanation_text_en", "explanation_text_ur",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_inspector_can_access_own_case(
            self, client, inspector_token, test_case):
        resp = client.get(f"/cases/{test_case.id}",
                          headers=auth_headers(inspector_token))
        assert resp.status_code == 200

    def test_unknown_case_returns_404(self, client, officer_token):
        resp = client.get(f"/cases/{uuid4()}",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 404

    def test_detail_requires_auth(self, client, test_case):
        resp = client.get(f"/cases/{test_case.id}")
        assert resp.status_code == 401


class TestCaseAuditLog:

    def test_officer_can_get_audit_log(
            self, client, officer_token, test_case):
        resp = client.get(f"/cases/{test_case.id}/audit-log",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert isinstance(data["entries"], list)

    def test_audit_entries_have_required_fields(
            self, client, officer_token, test_case):
        resp = client.get(f"/cases/{test_case.id}/audit-log",
                          headers=auth_headers(officer_token))
        for entry in resp.json()["entries"]:
            assert "action" in entry
            assert "actor_name" in entry
            assert "created_at" in entry
            assert "entity_type" in entry

    def test_unknown_case_audit_log_returns_404(
            self, client, officer_token):
        resp = client.get(f"/cases/{uuid4()}/audit-log",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 404

    def test_audit_log_requires_auth(self, client, test_case):
        resp = client.get(f"/cases/{test_case.id}/audit-log")
        assert resp.status_code == 401
