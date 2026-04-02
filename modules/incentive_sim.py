"""Performance-based incentive simulation — four mechanisms."""

import pandas as pd
import numpy as np


def compute_composite_score(perf: dict, weights: dict | None = None) -> float:
    """Weighted composite performance score (0-100 scale).

    perf keys: diabetes_control_rate, readmission_rate_30day,
               patient_satisfaction_score, cost_efficiency_ratio
    """
    if weights is None:
        weights = {
            "diabetes_control_rate": 0.25,
            "readmission_rate_30day": 0.25,
            "patient_satisfaction_score": 0.25,
            "cost_efficiency_ratio": 0.25,
        }

    # Normalise each metric to 0-100 where higher = better
    scores = {
        "diabetes_control_rate": perf["diabetes_control_rate"],           # already 0-100
        "readmission_rate_30day": max(0, 100 - perf["readmission_rate_30day"] * 4),  # lower is better: 0% -> 100, 25% -> 0
        "patient_satisfaction_score": perf["patient_satisfaction_score"],  # already 0-100
        "cost_efficiency_ratio": max(0, min(100, (1.2 - perf["cost_efficiency_ratio"]) / 0.5 * 100)),  # <0.7 -> 100, >1.2 -> 0
    }

    composite = sum(scores[k] * weights[k] for k in weights)
    return round(composite, 2)


# ─── Mechanism 1: Performance Pool ────────────────────────────────────────────

def performance_pool(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    withhold_pct: float,
    target: float,
    floor: float,
    metric_weights: dict | None = None,
) -> pd.DataFrame:
    """Calculate performance pool withhold and earn-back per provider.

    Returns DataFrame with columns:
      provider_id, pool_size, composite_score, earned_back_pct, earned_back, net_impact
    """
    rows = []
    for _, row in rac_payments.iterrows():
        pid = row["provider_id"]
        pool = row["total_rac_payment"] * (withhold_pct / 100)
        score = compute_composite_score(perf_data[pid], metric_weights)

        if score >= target:
            earned_pct = 100.0
        elif score >= floor:
            earned_pct = (score - floor) / (target - floor) * 100
        else:
            earned_pct = 0.0

        earned = pool * (earned_pct / 100)
        rows.append({
            "provider_id": pid,
            "pool_size": pool,
            "composite_score": score,
            "earned_back_pct": round(earned_pct, 1),
            "earned_back": earned,
            "net_impact": earned - pool,
        })
    return pd.DataFrame(rows)


# ─── Mechanism 2: RAC-Adjusted Expectations ───────────────────────────────────

def rac_adjusted_expectations(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    metric_weights: dict | None = None,
) -> pd.DataFrame:
    """Compute risk-adjusted performance expectations.

    Returns DataFrame with provider_id, avg_risk_score, composite_score,
    expected_score (from regression), residual.
    """
    rows = []
    for _, row in rac_payments.iterrows():
        pid = row["provider_id"]
        score = compute_composite_score(perf_data[pid], metric_weights)
        rows.append({
            "provider_id": pid,
            "avg_risk_score": row["avg_risk_score"],
            "composite_score": score,
        })
    df = pd.DataFrame(rows)

    # Simple linear regression: expected_score = a + b * risk_score
    x = df["avg_risk_score"].values
    y = df["composite_score"].values
    if len(x) >= 2 and np.std(x) > 0:
        b = np.cov(x, y)[0, 1] / np.var(x)
        a = np.mean(y) - b * np.mean(x)
    else:
        a, b = np.mean(y), 0.0

    df["expected_score"] = a + b * df["avg_risk_score"]
    df["residual"] = df["composite_score"] - df["expected_score"]
    df["regression_intercept"] = a
    df["regression_slope"] = b

    return df


# ─── Mechanism 3: Shared Savings with Quality Gates ──────────────────────────

def shared_savings(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    quality_gate_diabetes: float,
    quality_gate_readmission: float,
    quality_gate_satisfaction: float,
    cnhi_share_pct: float,
    provider_share_pct: float,
) -> pd.DataFrame:
    """Calculate shared savings with quality gate enforcement.

    Returns DataFrame per provider with savings breakdown.
    """
    rows = []
    for _, row in rac_payments.iterrows():
        pid = row["provider_id"]
        p = perf_data[pid]
        rac_total = row["total_rac_payment"]
        cer = p["cost_efficiency_ratio"]

        gross_savings = rac_total * (1 - cer)

        # Quality gate checks
        gate_diabetes = p["diabetes_control_rate"] >= quality_gate_diabetes
        gate_readmission = p["readmission_rate_30day"] <= quality_gate_readmission
        gate_satisfaction = p["patient_satisfaction_score"] >= quality_gate_satisfaction
        gate_passed = gate_diabetes and gate_readmission and gate_satisfaction

        if gate_passed and gross_savings > 0:
            eligible_savings = gross_savings
            cnhi_share = eligible_savings * (cnhi_share_pct / 100)
            provider_share = eligible_savings * (provider_share_pct / 100)
        else:
            eligible_savings = 0.0
            cnhi_share = 0.0
            provider_share = 0.0

        rows.append({
            "provider_id": pid,
            "rac_budget": rac_total,
            "actual_spend": rac_total * cer,
            "gross_savings": gross_savings,
            "gate_diabetes": gate_diabetes,
            "gate_readmission": gate_readmission,
            "gate_satisfaction": gate_satisfaction,
            "gate_passed": gate_passed,
            "eligible_savings": eligible_savings,
            "cnhi_share": cnhi_share,
            "provider_share": provider_share,
        })
    return pd.DataFrame(rows)


# ─── Mechanism 4: Tiered Tranches ────────────────────────────────────────────

def tiered_tranches(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    tiers: list[tuple[int, int, float, str]],
    metric_weights: dict | None = None,
) -> pd.DataFrame:
    """Assign tier and calculate bonus per provider.

    tiers: list of (min_score, max_score, payout_pct, tier_name)
    """
    rows = []
    for _, row in rac_payments.iterrows():
        pid = row["provider_id"]
        score = compute_composite_score(perf_data[pid], metric_weights)

        tier_name = "No Payout"
        payout_pct = 0.0
        for lo, hi, pct, name in tiers:
            if lo <= score <= hi:
                tier_name = name
                payout_pct = pct
                break

        bonus = row["total_rac_payment"] * (payout_pct / 100)
        rows.append({
            "provider_id": pid,
            "composite_score": score,
            "tier": tier_name,
            "payout_pct": payout_pct,
            "bonus": bonus,
        })
    return pd.DataFrame(rows)


# ─── Combined Summary ────────────────────────────────────────────────────────

def combined_summary(
    rac_payments: pd.DataFrame,
    pool_df: pd.DataFrame,
    savings_df: pd.DataFrame,
    tier_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merge all mechanisms into a single per-provider summary."""
    rows = []
    for _, row in rac_payments.iterrows():
        pid = row["provider_id"]
        rac_base = row["total_rac_payment"]

        pool_row = pool_df[pool_df["provider_id"] == pid].iloc[0]
        sav_row = savings_df[savings_df["provider_id"] == pid].iloc[0]
        tier_row = tier_df[tier_df["provider_id"] == pid].iloc[0]

        pool_earned = pool_row["earned_back"]
        pool_withheld = pool_row["pool_size"]
        savings_share = sav_row["provider_share"]
        tier_bonus = tier_row["bonus"]

        # Net payment = RAC base - pool withheld + pool earned back + savings share + tier bonus
        total = rac_base - pool_withheld + pool_earned + savings_share + tier_bonus
        vs_base = total - rac_base

        rows.append({
            "provider_id": pid,
            "rac_base": rac_base,
            "pool_withheld": pool_withheld,
            "pool_earned": pool_earned,
            "savings_share": savings_share,
            "tier_bonus": tier_bonus,
            "total_payment": total,
            "vs_rac_base": vs_base,
        })

    df = pd.DataFrame(rows)

    # Add CNHI row
    cnhi_total_incentives = (
        df["pool_earned"].sum()
        - df["pool_withheld"].sum()
        + df["savings_share"].sum()
        + df["tier_bonus"].sum()
    )
    # Note: CNHI also keeps its share of savings
    cnhi_savings_retained = savings_df["cnhi_share"].sum()

    return df, cnhi_total_incentives, cnhi_savings_retained
