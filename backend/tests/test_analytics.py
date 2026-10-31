"""
Tests for GET /analytics/model-performance

Covers:
- Returns valid structure
- All numeric rate fields are 0–100
- Trend array has 12 weekly data points
- Works with no closed cases (empty state)
- Requires authentication
- Rates sum to ~100% when there are cases
"""
import pytest
from tests.conftest import auth_headers


class TestModelPerformance:

    def test_returns_valid_structure(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = [
            "total_cases", "confirmed_count", "false_positive_count",
            "inconclusive_count", "confirmed_rate", "false_positive_rate",
            "inconclusive_rate", "trend",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    def test_requires_auth(self, client):
        resp = client.get("/analytics/model-performance")
        assert resp.status_code == 401

    def test_inspector_can_access(self, client, inspector_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(inspector_token))
        assert resp.status_code == 200

    def test_trend_has_12_data_points(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        trend = resp.json()["trend"]
        assert len(trend) == 12, \
            f"Expected 12 weekly trend points, got {len(trend)}"

    def test_trend_points_have_required_fields(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        for point in resp.json()["trend"]:
            assert "date" in point
            assert "confirmed_rate" in point
            assert "false_positive_rate" in point
            assert "inconclusive_rate" in point
            assert "total_cases" in point

    def test_rates_are_percentages_0_to_100(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        data = resp.json()
        for rate_key in ["confirmed_rate", "false_positive_rate",
                         "inconclusive_rate"]:
            assert 0.0 <= data[rate_key] <= 100.0, \
                f"{rate_key}={data[rate_key]} is out of range"

    def test_counts_are_non_negative(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        data = resp.json()
        assert data["total_cases"] >= 0
        assert data["confirmed_count"] >= 0
        assert data["false_positive_count"] >= 0
        assert data["inconclusive_count"] >= 0

    def test_counts_sum_to_total(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        data = resp.json()
        if data["total_cases"] > 0:
            total = (data["confirmed_count"] +
                     data["false_positive_count"] +
                     data["inconclusive_count"])
            assert total == data["total_cases"], \
                "Counts do not sum to total_cases"

    def test_rates_sum_to_100_when_cases_exist(self, client, officer_token):
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        data = resp.json()
        if data["total_cases"] > 0:
            rate_sum = (data["confirmed_rate"] +
                        data["false_positive_rate"] +
                        data["inconclusive_rate"])
            assert abs(rate_sum - 100.0) < 0.1, \
                f"Rates sum to {rate_sum}, not 100"

    def test_empty_state_returns_zeros(self, client, officer_token):
        """Even with no data, endpoint should not error."""
        resp = client.get("/analytics/model-performance",
                          headers=auth_headers(officer_token))
        assert resp.status_code == 200
        # Either has data or returns all zeros – both valid
        data = resp.json()
        if data["total_cases"] == 0:
            assert data["confirmed_rate"] == 0.0
            assert data["false_positive_rate"] == 0.0
            assert data["inconclusive_rate"] == 0.0
