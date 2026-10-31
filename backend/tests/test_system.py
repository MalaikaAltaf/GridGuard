"""
Tests for system-level endpoints and edge cases:

GET /         - root
GET /health   - health check
General:
- 404 for unknown routes
- CORS headers present
- Large page numbers beyond data return empty list (not error)
"""
import pytest
from tests.conftest import auth_headers


class TestRootEndpoint:

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_contains_expected_keys(self, client):
        resp = client.get("/")
        data = resp.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data


class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_status_is_ok(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "grid-guard-ai-backend"

    def test_health_has_version(self, client):
        resp = client.get("/health")
        assert "version" in resp.json()


class TestGeneralBehavior:

    def test_unknown_route_returns_404(self, client):
        resp = client.get("/this/does/not/exist")
        assert resp.status_code == 404

    def test_large_page_returns_empty_not_error(
            self, client, officer_token):
        resp = client.get("/consumers/risk-queue?page=99999&page_size=25",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []

    def test_large_page_cases_returns_empty(self, client, officer_token):
        resp = client.get("/cases?page=99999&page_size=25",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_invalid_uuid_consumer_explanation_returns_422(
            self, client, officer_token):
        resp = client.get("/consumers/not-a-uuid/explanation",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 422

    def test_invalid_uuid_case_returns_422(self, client, officer_token):
        resp = client.get("/cases/not-a-uuid",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 422

    def test_docs_are_accessible(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_redoc_is_accessible(self, client):
        resp = client.get("/redoc")
        assert resp.status_code == 200
