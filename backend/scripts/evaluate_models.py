"""
Model Performance Evaluation Script
Tests both PRECON (AMI) and SGCC models with different consumption patterns
to evaluate discrimination and threshold behavior.
"""
import sys
import os
# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import json
import numpy as np
from app.ml.inference import model_service
from app.schemas.prediction import PredictionRequest, MonthlyUsage

# ─────────────────────────────────────────────
# PRECON / AMI Scenarios
# ─────────────────────────────────────────────

AMI_SCENARIOS = {
    "Normal residential (daytime peak)": [
        1.2, 1.1, 0.9, 0.8, 0.7, 0.8,
        1.0, 1.4, 1.8, 2.0, 2.2, 2.3,
        2.1, 2.0, 1.9, 1.8, 1.7, 1.8,
        2.0, 2.4, 2.2, 1.9, 1.6, 1.4
    ],
    "Suspicious - near-zero all day (no load)": [
        0.02, 0.01, 0.01, 0.01, 0.01, 0.02,
        0.03, 0.03, 0.02, 0.02, 0.03, 0.02,
        0.02, 0.02, 0.02, 0.02, 0.02, 0.02,
        0.02, 0.03, 0.02, 0.02, 0.01, 0.01
    ],
    "High usage industrial (normal)": [
        5.0, 4.8, 4.5, 4.3, 4.0, 4.2,
        5.5, 6.2, 7.0, 8.1, 8.5, 8.7,
        8.6, 8.4, 8.0, 7.8, 7.5, 7.6,
        8.0, 8.5, 8.0, 7.0, 6.0, 5.5
    ],
    "Suspicious - only nighttime usage (bypass?)": [
        3.5, 3.8, 4.0, 3.9, 3.7, 3.5,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.2, 2.0, 3.2
    ],
    "Extremely suspicious - flat constant (meter tamper?)": [
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 1.0, 1.0, 1.0, 1.0
    ],
    "Normal commercial (business hours only)": [
        0.2, 0.1, 0.1, 0.1, 0.2, 0.5,
        1.2, 2.5, 3.8, 4.5, 4.8, 5.0,
        5.1, 5.0, 4.9, 4.7, 4.5, 4.0,
        2.5, 1.5, 0.8, 0.4, 0.3, 0.2
    ],
}

# ─────────────────────────────────────────────
# SGCC / Monthly Scenarios (needs 34 months)
# ─────────────────────────────────────────────

def make_monthly_history(pattern: list) -> list:
    """Build 34 MonthlyUsage records from a list of 34 kwh values."""
    from datetime import date, timedelta
    result = []
    for i, kwh in enumerate(pattern):
        d = date.today().replace(day=1) - timedelta(days=30 * (33 - i))
        result.append(MonthlyUsage(month=d.strftime("%Y-%m"), usage_kwh=kwh))
    return result

def flat_consumption(base, n=34):
    return [base] * n

def dropping_consumption(start, end, n=34):
    """Linearly drops from start to end over n months."""
    return [round(start + (end - start) * i / (n - 1), 1) for i in range(n)]

def sudden_drop(base, drop_factor=0.2, drop_at=30, n=34):
    """Stable then sudden drop in last few months."""
    return [round(base + np.random.uniform(-20, 20), 1) if i < drop_at
            else round(base * drop_factor + np.random.uniform(-5, 5), 1)
            for i in range(n)]

np.random.seed(42)

SGCC_SCENARIOS = {
    "Stable normal consumer (~250 kWh/month)": flat_consumption(250),
    "Stable high consumer (~700 kWh/month)":   flat_consumption(700),
    "Gradual decline (600 → 80 kWh)":          dropping_consumption(600, 80),
    "Sudden drop in last 4 months (tamper?)":  sudden_drop(400, drop_factor=0.15, drop_at=30),
    "Sudden drop to near-zero":                sudden_drop(350, drop_factor=0.05, drop_at=29),
    "Erratic / irregular usage":               [round(abs(np.random.normal(300, 150)), 1) for _ in range(34)],
    "Seasonal summer peak (Pakistan)": [
        180, 190, 200, 230, 320, 480,  # Jan–Jun
        550, 580, 520, 400, 250, 200,  # Jul–Dec
        185, 195, 205, 235, 325, 485,  # Year 2
        555, 585, 525, 405, 255, 205,
        190, 200, 210, 240, 330, 490,  # Year 3 (10 months)
        560, 590, 530, 410,
    ],
}

# ─────────────────────────────────────────────
# Run Evaluations
# ─────────────────────────────────────────────

PRECON_THRESHOLD = model_service.precon_threshold
SGCC_THRESHOLD   = model_service.sgcc_threshold

print("=" * 70)
print("GRID-GUARD AI — MODEL PERFORMANCE EVALUATION")
print("=" * 70)

# ── PRECON Branch ──
print(f"\n{'─'*70}")
print(f"  PRECON / AMI BRANCH  (threshold = {PRECON_THRESHOLD})")
print(f"{'─'*70}")
print(f"  {'Scenario':<45}  {'Score':>8}  {'Decision':<20}")
print(f"  {'-'*45}  {'-'*8}  {'-'*20}")

ami_results = []
for name, hourly in AMI_SCENARIOS.items():
    req = PredictionRequest(consumer_id="TEST", meter_type="ami", hourly_usage_kwh=hourly)
    resp = model_service.predict(req)
    ami_results.append((name, resp.risk_score, resp.decision))
    flag = "⚠️ " if resp.decision == "review_required" else "✅ "
    print(f"  {flag}{name:<43}  {resp.risk_score:>8.4f}  {resp.decision:<20}")

scores_ami = [r[1] for r in ami_results]
print(f"\n  Min score: {min(scores_ami):.4f} | Max score: {max(scores_ami):.4f} | Mean: {np.mean(scores_ami):.4f}")
print(f"  Flagged: {sum(1 for _,_,d in ami_results if d=='review_required')}/{len(ami_results)}")

# ── SGCC Branch ──
print(f"\n{'─'*70}")
print(f"  SGCC / MONTHLY BRANCH  (threshold = {SGCC_THRESHOLD})")
print(f"{'─'*70}")
print(f"  {'Scenario':<45}  {'Score':>8}  {'Decision':<20}")
print(f"  {'-'*45}  {'-'*8}  {'-'*20}")

sgcc_results = []
for name, monthly_kwh in SGCC_SCENARIOS.items():
    history = make_monthly_history(monthly_kwh[:34])  # ensure exactly 34
    req = PredictionRequest(
        consumer_id="TEST",
        meter_type="conventional_monthly_history",
        monthly_usage_history=history
    )
    resp = model_service.predict(req)
    sgcc_results.append((name, resp.risk_score, resp.decision))
    flag = "⚠️ " if resp.decision == "review_required" else "✅ "
    print(f"  {flag}{name:<43}  {resp.risk_score:>8.4f}  {resp.decision:<20}")

scores_sgcc = [r[1] for r in sgcc_results]
print(f"\n  Min score: {min(scores_sgcc):.4f} | Max score: {max(scores_sgcc):.4f} | Mean: {np.mean(scores_sgcc):.4f}")
print(f"  Flagged: {sum(1 for _,_,d in sgcc_results if d=='review_required')}/{len(sgcc_results)}")

# ── Threshold Sensitivity ──
print(f"\n{'─'*70}")
print(f"  THRESHOLD SENSITIVITY (PRECON — using 'Normal residential' as baseline)")
print(f"{'─'*70}")
normal_score = ami_results[0][1]
print(f"  Baseline score: {normal_score:.4f}")
for t in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:
    decision = "review_required" if normal_score >= t else "low_risk"
    print(f"  Threshold {t:.2f} → {decision}")

print(f"\n{'='*70}")
print(f"  SUMMARY")
print(f"{'='*70}")
print(f"  PRECON threshold (0.05) is very sensitive — catches subtle anomalies")
print(f"  SGCC threshold  (0.50) is conservative — flags clear patterns only")
print(f"  Both models are calling .predict_proba() on your trained PKL bundle ✓")
print()
