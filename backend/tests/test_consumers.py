"""
Tests for /consumers endpoints:

GET /consumers/risk-queue
GET /consumers/{id}/explanation
GET /consumers/{id}/consumption-history
"""
import pytest
from uuid import uuid4
from tests.conftest import auth_headers


class TestRiskQueue:

    def test_returns_paginated_list(self, client, officer_token):
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert isinstance(data["items"], list)

    def test_requires_auth(self, client):
        resp = client.get("/consumers/risk-queue")
        assert resp.status_code == 401

    def test_inspector_can_access(self, client, inspector_token):
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(inspector_token))
        assert resp.status_code == 200

    def test_items_have_required_fields(self, client, officer_token):
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(officer_token))
        items = resp.json()["items"]
        if items:
            item = items[0]
            assert "id" in item
            assert "external_ref" in item
            assert "score" in item
            assert "risk_band" in item
            assert "feeder" in item

    def test_items_sorted_by_score_descending(self, client, officer_token):
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(officer_token))
        items = resp.json()["items"]
        scores = [i["score"] for i in items]
        assert scores == sorted(scores, reverse=True), \
            "Risk queue must be sorted by score DESC"

    def test_filter_by_risk_band_high(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?risk_band=high",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["risk_band"] == "high"

    def test_filter_by_risk_band_medium(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?risk_band=medium",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert item["risk_band"] == "medium"

    def test_invalid_risk_band_returns_400(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?risk_band=banana",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 400

    def test_filter_by_meter_type(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?meter_type=Single Phase",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200

    def test_invalid_meter_type_returns_400(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?meter_type=INVALID",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 400

    def test_filter_by_feeder(self, client, officer_token):
        # First get all items and pick a feeder that exists
        resp = client.get("/consumers/risk-queue",
                          headers=auth_headers(officer_token))
        items = resp.json()["items"]
        if not items:
            pytest.skip("No consumers in DB")
        feeder = items[0]["feeder"]
        resp2 = client.get(f"/consumers/risk-queue?feeder={feeder}",
                           headers=auth_headers(officer_token))
        assert resp2.status_code == 200
        for item in resp2.json()["items"]:
            assert item["feeder"] == feeder

    def test_pagination_page2(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?page=2&page_size=5",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 5

    def test_page_size_clamp_at_100(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?page_size=200",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 422  # Exceeds max

    def test_page_must_be_positive(self, client, officer_token):
        resp = client.get("/consumers/risk-queue?page=0",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 422


class TestExplanation:

    def test_returns_explanation_for_known_consumer(
            self, client, officer_token, test_consumer, test_risk_score):
        resp = client.get(
            f"/consumers/{test_consumer.id}/explanation",
            headers=auth_headers(officer_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["consumer_id"] == str(test_consumer.id)
        assert "score" in data
        assert "risk_band" in data
        assert "explanation_text_en" in data
        assert "explanation_text_ur" in data
        assert "explanation_raw" in data

    def test_explanation_requires_auth(self, client, test_consumer):
        resp = client.get(f"/consumers/{test_consumer.id}/explanation")
        assert resp.status_code == 401

    def test_unknown_consumer_returns_404(self, client, officer_token):
        resp = client.get(
            f"/consumers/{uuid4()}/explanation",
            headers=auth_headers(officer_token),
        )
        assert resp.status_code == 404

    def test_score_is_between_0_and_1(
            self, client, officer_token, test_consumer, test_risk_score):
        resp = client.get(
            f"/consumers/{test_consumer.id}/explanation",
            headers=auth_headers(officer_token),
        )
        score = resp.json()["score"]
        assert 0.0 <= score <= 1.0

    def test_risk_band_is_valid_value(
            self, client, officer_token, test_consumer, test_risk_score):
        resp = client.get(
            f"/consumers/{test_consumer.id}/explanation",
            headers=auth_headers(officer_token),
        )
        assert resp.json()["risk_band"] in ("high", "medium", "low")


class TestConsumptionHistory:

    def test_returns_trend_series(
            self, client, officer_token, test_consumer, test_consumption_history):
        resp = client.get(
            f"/consumers/{test_consumer.id}/consumption-history",
            headers=auth_headers(officer_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "consumer_id" in data
        assert "trend_series" in data
        assert isinstance(data["trend_series"], list)
        assert len(data["trend_series"]) == 12

    def test_history_requires_auth(self, client, test_consumer):
        resp = client.get(
            f"/consumers/{test_consumer.id}/consumption-history")
        assert resp.status_code == 401

    def test_unknown_consumer_returns_404(self, client, officer_token):
        resp = client.get(
            f"/consumers/{uuid4()}/consumption-history",
            headers=auth_headers(officer_token),
        )
        assert resp.status_code == 404

    def test_trend_series_data_points_have_period_and_kwh(
            self, client, officer_token, test_consumer, test_consumption_history):
        resp = client.get(
            f"/consumers/{test_consumer.id}/consumption-history",
            headers=auth_headers(officer_token),
        )
        for point in resp.json()["trend_series"]:
            assert "period_start" in point
            assert "kwh" in point
            assert point["kwh"] >= 0
