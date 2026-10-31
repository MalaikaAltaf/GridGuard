"""
Hybrid Scoring Overlay — deterministic rule-based signal applied on top of ML score.
Works for both PRECON (AMI) and SGCC (Monthly) branches.

Rules fire independently of the ML model and boost the combined score.
This compensates for the SGCC model's compressed score distribution.
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from scipy.stats import linregress


# ─── CALIBRATED THRESHOLDS ────────────────────────────────────────────────────
# Original bundle thresholds                    PRECON=0.05  SGCC=0.50
# SGCC scores cluster at 0.16–0.28 (too low) → calibrate down to 0.20
SGCC_CALIBRATED_THRESHOLD = 0.20   # was 0.50 in bundle
PRECON_CALIBRATED_THRESHOLD = None  # keep original from bundle (0.05)

# Maximum rule boost applied to ML score
RULE_BOOST_PER_FLAG = 0.12   # each triggered rule adds 0.12 to the score
MAX_RULE_BOOST = 0.40        # hard cap on total boost


# ─── HYBRID SCORING — SGCC MONTHLY ────────────────────────────────────────────

def apply_sgcc_hybrid_rules(
    ml_score: float,
    monthly_history: List[Dict[str, Any]],
    threshold: float,
) -> Tuple[float, float, str, List[str]]:
    """
    Apply deterministic rule-based overlay on top of the SGCC ML score.

    Args:
        ml_score:        Raw .predict_proba() score from sgcc_monthly_rf
        monthly_history: List of dicts with 'month' and 'usage_kwh'
        threshold:       Calibrated SGCC threshold

    Returns:
        (hybrid_score, raw_ml_score, decision, triggered_rules)
    """
    usages = [m["usage_kwh"] for m in monthly_history]
    n = len(usages)
    triggered_rules: List[str] = []

    if n < 3:
        return ml_score, ml_score, _decision(ml_score, threshold), triggered_rules

    usages_np = np.array(usages, dtype=float)

    # ── Rule 1: Consumption drop > 60% in last 3 months vs prior 6 ─────────
    if n >= 9:
        recent_avg = np.mean(usages_np[-3:])
        prior_avg  = np.mean(usages_np[-9:-3])
        if prior_avg > 0 and (prior_avg - recent_avg) / prior_avg > 0.60:
            triggered_rules.append(
                f"Consumption dropped {((prior_avg - recent_avg)/prior_avg*100):.0f}% "
                f"in last 3 months vs prior 6-month average"
            )

    # ── Rule 2: 2+ near-zero months (< 20 kWh) in last 6 ──────────────────
    if n >= 6:
        near_zero = sum(1 for u in usages_np[-6:] if u < 20)
        if near_zero >= 2:
            triggered_rules.append(
                f"{near_zero} near-zero billing months (< 20 kWh) in last 6 months"
            )

    # ── Rule 3: Strong negative trend slope ─────────────────────────────────
    x = np.arange(n)
    slope, _, _, _, _ = linregress(x, usages_np)
    if slope < -8:   # declining > 8 kWh per month
        triggered_rules.append(
            f"Strongly declining consumption trend (slope={slope:.1f} kWh/month)"
        )

    # ── Rule 4: Sudden single-month cliff ───────────────────────────────────
    if n >= 2:
        pct_changes = np.diff(usages_np) / np.clip(usages_np[:-1], 1, None) * 100
        worst_drop = pct_changes.min()
        if worst_drop < -70:
            triggered_rules.append(
                f"Single-month cliff drop of {abs(worst_drop):.0f}% detected"
            )

    # ── Rule 5: Flat constant reading (meter tamper signal) ──────────────────
    if n >= 4:
        recent_4 = usages_np[-4:]
        if recent_4.std() < 2.0 and recent_4.mean() < 30:
            triggered_rules.append(
                "Near-constant ultra-low reading in last 4 months (possible tamper)"
            )

    # ── Combine: boost ML score by RULE_BOOST_PER_FLAG per triggered rule ───
    total_boost = min(len(triggered_rules) * RULE_BOOST_PER_FLAG, MAX_RULE_BOOST)
    hybrid_score = min(1.0, ml_score + total_boost)
    decision = _decision(hybrid_score, threshold)

    return hybrid_score, ml_score, decision, triggered_rules


# ─── HYBRID SCORING — PRECON AMI ──────────────────────────────────────────────

def apply_precon_hybrid_rules(
    ml_score: float,
    hourly_usage: List[float],
    threshold: float,
) -> Tuple[float, float, str, List[str]]:
    """
    Apply deterministic rule-based overlay on top of the PRECON AMI score.

    Args:
        ml_score:      Raw .predict_proba() score from precon_fa_rf
        hourly_usage:  24 hourly kWh values
        threshold:     PRECON threshold (usually already 0.05)

    Returns:
        (hybrid_score, raw_ml_score, decision, triggered_rules)
    """
    triggered_rules: List[str] = []
    h = np.array(hourly_usage, dtype=float)

    # ── Rule 1: All-day near-zero (no load) ─────────────────────────────────
    if h.mean() < 0.15:
        triggered_rules.append(
            f"All-day near-zero consumption (avg={h.mean():.3f} kWh/hr)"
        )

    # ── Rule 2: Consumption only at night (bypass signal) ───────────────────
    daytime  = h[8:20]   # 08:00–20:00
    nighttime = np.concatenate([h[:8], h[20:]])
    if nighttime.mean() > 0 and daytime.mean() / (nighttime.mean() + 1e-6) < 0.25:
        triggered_rules.append(
            "Consumption heavily concentrated in off-peak nighttime hours (bypass signal)"
        )

    # ── Rule 3: Flat constant reading ───────────────────────────────────────
    if h.std() < 0.05:
        triggered_rules.append(
            f"Perfectly constant hourly readings (std={h.std():.4f}) — possible meter tamper"
        )

    # ── Rule 4: Peak-hour ratio anomaly ─────────────────────────────────────
    peak    = h[9:22].mean()     # 09:00–22:00 peak window
    offpeak = h[[*range(0,9), *range(22,24)]].mean()
    if peak > 0 and offpeak / (peak + 1e-6) > 3.0:
        triggered_rules.append(
            f"Off-peak usage is {offpeak/peak:.1f}x higher than peak hours (anomalous)"
        )

    total_boost = min(len(triggered_rules) * RULE_BOOST_PER_FLAG, MAX_RULE_BOOST)
    hybrid_score = min(1.0, ml_score + total_boost)
    decision = _decision(hybrid_score, threshold)

    return hybrid_score, ml_score, decision, triggered_rules


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _decision(score: float, threshold: float) -> str:
    return "review_required" if score >= threshold else "low_risk"
