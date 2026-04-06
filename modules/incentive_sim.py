"""Performance-based incentive simulation — four mechanisms."""

from __future__ import annotations

import pandas as pd
import numpy as np


def compute_composite_score(
    cluster_kpis: dict,
    kpi_categories: dict,
    category_weights: dict,
    kpi_active: dict,
    kpi_weights: dict | None = None,
) -> tuple[float, dict]:
    """Calculate weighted composite score across KPI categories.

    Args:
        cluster_kpis: {kpi_id: value} for this cluster
        kpi_categories: the KPI_CATEGORIES structure
        category_weights: {category_id: weight_pct} (should sum to 100)
        kpi_active: {kpi_id: bool} — which KPIs are currently active
        kpi_weights: {kpi_id: weight} within-category weights (equal if None)

    Returns:
        (composite_score, {category_id: category_score})
    """
    category_scores = {}

    for cat_id, cat_def in kpi_categories.items():
        active_kpis = [
            kpi_id for kpi_id in cat_def["kpis"]
            if kpi_active.get(kpi_id, cat_def["kpis"][kpi_id]["wave_1_active"])
        ]

        if not active_kpis:
            category_scores[cat_id] = 0.0
            continue

        normalised = []
        for kpi_id in active_kpis:
            kpi_def = cat_def["kpis"][kpi_id]
            raw = cluster_kpis.get(kpi_id, 0)
            kpi_range = kpi_def["max"] - kpi_def["min"]

            if kpi_range == 0:
                score = 50.0
            elif kpi_def["direction"] == "higher_better":
                score = (raw - kpi_def["min"]) / kpi_range * 100
            else:  # lower_better
                score = (kpi_def["max"] - raw) / kpi_range * 100

            normalised.append(max(0, min(100, score)))

        category_scores[cat_id] = sum(normalised) / len(normalised)

    # Weighted composite across categories
    total_weight = sum(category_weights.get(c, 0) for c in category_scores)
    if total_weight == 0:
        return 0.0, category_scores

    composite = sum(
        category_scores[c] * category_weights.get(c, 0)
        for c in category_scores
    ) / total_weight

    return round(composite, 2), category_scores


def _get_score(cid: str, perf_data: dict, score_args: dict) -> float:
    """Helper to compute composite score for a cluster, returning just the float."""
    score, _ = compute_composite_score(
        perf_data[cid],
        score_args["kpi_categories"],
        score_args["category_weights"],
        score_args["kpi_active"],
    )
    return score


# ─── Mechanism 1: Performance Pool ───────────────────────────────────────────

def performance_pool(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    withhold_pct: float,
    target: float,
    floor: float,
    score_args: dict | None = None,
) -> pd.DataFrame:
    """Calculate performance pool withhold and earn-back per cluster."""
    rows = []
    for _, row in rac_payments.iterrows():
        cid = row["cluster_id"]
        pool = row["total_rac_payment"] * (withhold_pct / 100)
        score = _get_score(cid, perf_data, score_args)

        if score >= target:
            earned_pct = 100.0
        elif score >= floor:
            earned_pct = (score - floor) / (target - floor) * 100
        else:
            earned_pct = 0.0

        earned = pool * (earned_pct / 100)
        rows.append({
            "cluster_id": cid,
            "pool_size": pool,
            "composite_score": score,
            "earned_back_pct": round(earned_pct, 1),
            "earned_back": earned,
            "net_impact": earned - pool,
        })
    return pd.DataFrame(rows)


# ─── Mechanism 2: RAC-Adjusted Expectations ──────────────────────────────────

def rac_adjusted_expectations(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    score_args: dict | None = None,
) -> pd.DataFrame:
    """Compute risk-adjusted performance expectations."""
    rows = []
    for _, row in rac_payments.iterrows():
        cid = row["cluster_id"]
        score = _get_score(cid, perf_data, score_args)
        rows.append({
            "cluster_id": cid,
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


# ─── Mechanism 3: Shared Savings with Quality Gates ─────────────────────────

def shared_savings(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    quality_gate_diabetes: float,
    quality_gate_readmission: float,
    quality_gate_composite: float,
    cnhi_share_pct: float,
    cluster_share_pct: float,
    score_args: dict | None = None,
) -> pd.DataFrame:
    """Calculate shared savings with quality gate enforcement."""
    rows = []
    for _, row in rac_payments.iterrows():
        cid = row["cluster_id"]
        p = perf_data[cid]
        rac_total = row["total_rac_payment"]
        cer = p["cost_efficiency_ratio"]

        gross_savings = rac_total * (1 - cer)

        # Quality gate checks
        gate_diabetes = p.get("diabetes_hba1c_control", p.get("diabetes_control_rate", 0)) >= quality_gate_diabetes
        gate_readmission = p.get("readmission_30day", p.get("readmission_rate_30day", 30)) <= quality_gate_readmission

        # Gate 3: composite score threshold
        score = _get_score(cid, perf_data, score_args)
        gate_composite = score >= quality_gate_composite

        gate_passed = gate_diabetes and gate_readmission and gate_composite

        if gate_passed and gross_savings > 0:
            eligible_savings = gross_savings
            cnhi_share = eligible_savings * (cnhi_share_pct / 100)
            cluster_share = eligible_savings * (cluster_share_pct / 100)
        else:
            eligible_savings = 0.0
            cnhi_share = 0.0
            cluster_share = 0.0

        rows.append({
            "cluster_id": cid,
            "rac_budget": rac_total,
            "actual_spend": rac_total * cer,
            "gross_savings": gross_savings,
            "gate_diabetes": gate_diabetes,
            "gate_readmission": gate_readmission,
            "gate_composite": gate_composite,
            "gate_passed": gate_passed,
            "eligible_savings": eligible_savings,
            "cnhi_share": cnhi_share,
            "cluster_share": cluster_share,
        })
    return pd.DataFrame(rows)


# ─── Mechanism 4: Tiered Tranches ────────────────────────────────────────────

def tiered_tranches(
    rac_payments: pd.DataFrame,
    perf_data: dict[str, dict],
    tiers: list[tuple[int, int, float, str]],
    score_args: dict | None = None,
) -> pd.DataFrame:
    """Assign tier and calculate bonus per cluster."""
    rows = []
    for _, row in rac_payments.iterrows():
        cid = row["cluster_id"]
        score = _get_score(cid, perf_data, score_args)

        tier_name = "No Payout"
        payout_pct = 0.0
        for lo, hi, pct, name in tiers:
            if lo <= score <= hi:
                tier_name = name
                payout_pct = pct
                break

        bonus = row["total_rac_payment"] * (payout_pct / 100)
        rows.append({
            "cluster_id": cid,
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
    """Merge all mechanisms into a single per-cluster summary."""
    rows = []
    for _, row in rac_payments.iterrows():
        cid = row["cluster_id"]
        rac_base = row["total_rac_payment"]

        pool_row = pool_df[pool_df["cluster_id"] == cid].iloc[0]
        sav_row = savings_df[savings_df["cluster_id"] == cid].iloc[0]
        tier_row = tier_df[tier_df["cluster_id"] == cid].iloc[0]

        pool_earned = pool_row["earned_back"]
        pool_withheld = pool_row["pool_size"]
        savings_share = sav_row["cluster_share"]
        tier_bonus = tier_row["bonus"]

        total = rac_base - pool_withheld + pool_earned + savings_share + tier_bonus
        vs_base = total - rac_base

        rows.append({
            "cluster_id": cid,
            "rac_base": rac_base,
            "pool_withheld": pool_withheld,
            "pool_earned": pool_earned,
            "savings_share": savings_share,
            "tier_bonus": tier_bonus,
            "total_payment": total,
            "vs_rac_base": vs_base,
        })

    df = pd.DataFrame(rows)

    cnhi_total_incentives = (
        df["pool_earned"].sum()
        - df["pool_withheld"].sum()
        + df["savings_share"].sum()
        + df["tier_bonus"].sum()
    )
    cnhi_savings_retained = savings_df["cnhi_share"].sum()

    return df, cnhi_total_incentives, cnhi_savings_retained
