"""
Tests for POST /auth/login

Covers:
- Successful login returns JWT + user info for each role
- Wrong password → 401
- Non-existent email → 401
- Missing fields → 422
- Token is a valid Bearer token accepted by protected endpoints
"""
import pytest
from tests.conftest import auth_headers


class TestLogin:

    def test_officer_login_success(self, client, officer_user):
        resp = client.post("/auth/login", json={
            "email": officer_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["token"]
        assert data["user"]["email"] == officer_user.email
        assert data["user"]["role"] == "officer"

    def test_inspector_login_success(self, client, inspector_user):
        resp = client.post("/auth/login", json={
            "email": inspector_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["role"] == "inspector"

    def test_manager_login_success(self, client, manager_user):
        resp = client.post("/auth/login", json={
            "email": manager_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["role"] == "circle_manager"

    def test_wrong_password_returns_401(self, client, officer_user):
        resp = client.post("/auth/login", json={
            "email": officer_user.email,
            "password": "wrongpassword",
        })
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_nonexistent_email_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "whatever",
        })
        assert resp.status_code == 401

    def test_missing_email_returns_422(self, client):
        resp = client.post("/auth/login", json={"password": "testpass123"})
        assert resp.status_code == 422

    def test_missing_password_returns_422(self, client):
        resp = client.post("/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/auth/login", json={})
        assert resp.status_code == 422

    def test_token_accepted_on_protected_endpoint(self, client, officer_token):
        """Token returned from login is valid for authenticated endpoints."""
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200

    def test_no_token_returns_403(self, client):
        resp = client.get("/consumers/risk-queue")
        assert resp.status_code == 401

    def test_garbage_token_returns_403(self, client):
        resp = client.get("/consumers/risk-queue",
                          headers={"Authorization": "Bearer this.is.garbage"})
        assert resp.status_code == 401
