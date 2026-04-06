"""CNHI Incentive Intelligence Platform — Proof of Concept v2."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from modules.synthetic_data import generate_population
from modules.rac_engine import calculate_risk_scores, calculate_rac_payments
from modules.scenarios import SCENARIOS, apply_scenario
from modules.incentive_sim import (
    performance_pool,
    rac_adjusted_expectations,
    shared_savings,
    tiered_tranches,
    combined_summary,
    compute_composite_score,
)
from config.defaults import (
    COLORS,
    CLUSTER_COLORS,
    BASE_PMPM_RATE,
    PMPM_MIN,
    PMPM_MAX,
    DISEASE_WEIGHTS,
    COMORBIDITY_TERMS,
    RANDOM_SEED,
    CLUSTER_KPI_BASELINES,
    KPI_CATEGORIES,
    WITHHOLD_PERCENTAGE,
    PERFORMANCE_TARGET,
    PERFORMANCE_FLOOR,
    QUALITY_GATE_DIABETES,
    QUALITY_GATE_READMISSION,
    QUALITY_GATE_COMPOSITE,
    SAVINGS_SPLIT_CNHI,
    SAVINGS_SPLIT_PROVIDER,
    TIER_THRESHOLDS,
    CAPABILITY_THRESHOLD,
    CAPABILITY_INVESTMENT_PER_GAP,
    ELASTICITY_FACTOR_DEFAULT,
)
from config.demographics import CLUSTER_PROFILES
from docs_page import render_docs

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CNHI Incentive Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 1.5rem;
        max-width: 1200px;
    }}
    [data-testid="stMetric"] {{
        background-color: rgba(46, 196, 182, 0.08);
        padding: 12px 16px;
        border-radius: 8px;
        border-left: 4px solid {COLORS['teal']};
    }}
    h2, h3 {{
        border-bottom: 2px solid {COLORS['teal']};
        padding-bottom: 4px;
    }}
    .cluster-tag {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }}
    /* Prominent top-level tabs */
    div[data-testid="stTabs"] > div[role="tablist"] {{
        background: linear-gradient(135deg, {COLORS['navy']} 0%, #1a2d4a 100%);
        border-radius: 10px;
        padding: 6px 8px;
        gap: 4px;
        margin-bottom: 16px;
    }}
    div[data-testid="stTabs"] > div[role="tablist"] > button {{
        font-size: 1.1rem;
        font-weight: 700;
        padding: 10px 28px;
        border-radius: 8px;
        color: {COLORS['mid_grey']};
        border: none;
    }}
    div[data-testid="stTabs"] > div[role="tablist"] > button[aria-selected="true"] {{
        background-color: {COLORS['teal']};
        color: white;
    }}
    div[data-testid="stTabs"] > div[role="tablist"] > button:hover {{
        color: white;
    }}
    /* Hide the default tab underline */
    div[data-testid="stTabs"] > div[role="tablist"] > button[aria-selected="true"]::after {{
        display: none;
    }}
</style>
""", unsafe_allow_html=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────
def fmt_sar(value: float) -> str:
    if value < 0:
        return f"-{fmt_sar(-value)}"
    if value >= 1e6:
        return f"SAR {value:,.0f}"
    return f"SAR {value:,.2f}"


CLUSTER_SHORT_NAMES = {"A": "Riyadh 1st", "B": "Eastern", "C": "Madinah"}


def cluster_label(cid: str) -> str:
    return f"Cluster {cid} — {CLUSTER_PROFILES[cid]['name']}"


@st.cache_data(show_spinner="Generating synthetic patient population...")
def load_population(seed: int = RANDOM_SEED) -> pd.DataFrame:
    return generate_population(seed)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f'<div style="padding: 8px 0;">'
    f'<span style="font-size: 1.1rem; font-weight: 700; color: {COLORS["teal"]};">'
    f'Arthur D. Little</span><br/>'
    f'<span style="font-size: 0.75rem; color: {COLORS["mid_grey"]};">Incentive Intelligence Platform</span>'
    f'</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# ── Module 2: RAC Calculation Engine ────────────────────────────────────────
st.sidebar.markdown(
    f'<p style="color: {COLORS["teal"]}; font-weight: 700; font-size: 0.85rem; '
    f'margin: 4px 0 2px 0; padding: 0;">Module 2 — RAC Engine</p>',
    unsafe_allow_html=True,
)

with st.sidebar.expander("Base Capitation Rate", expanded=True):
    base_pmpm = st.slider(
        "Base PMPM Rate (SAR)",
        min_value=PMPM_MIN, max_value=PMPM_MAX,
        value=BASE_PMPM_RATE, step=50,
        help="Monthly per-member-per-month capitation base rate",
    )

with st.sidebar.expander("Risk Model Weights", expanded=False):
    st.caption("Disease weights for RAC payment calculation")
    dw = {}
    for condition, default in DISEASE_WEIGHTS.items():
        label = condition.replace("_", " ").title()
        dw[condition] = st.slider(
            label, 0.0, 1.0, default, 0.05, key=f"dw_{condition}",
        )
    st.caption("Comorbidity interaction")
    comorb_2 = st.slider("2 Conditions", 0.0, 0.5, float(COMORBIDITY_TERMS[2]), 0.05, key="comorb2")
    comorb_3 = st.slider("3+ Conditions", 0.0, 0.5, float(COMORBIDITY_TERMS[3]), 0.05, key="comorb3")

comorbidity_overrides = {2: comorb_2, 3: comorb_3}

# ── Module 3: Performance Incentive Simulation ──────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<p style="color: {COLORS["teal"]}; font-weight: 700; font-size: 0.85rem; '
    f'margin: 4px 0 2px 0; padding: 0;">Module 3 — Incentives</p>',
    unsafe_allow_html=True,
)

with st.sidebar.expander("Category Weights", expanded=False):
    st.caption("KPI category weights for composite scoring (must sum to 100%)")
    cat_weights = {}
    for cat_id, cat_def in KPI_CATEGORIES.items():
        cat_weights[cat_id] = st.slider(
            cat_def["label"],
            0, 100, cat_def["default_weight"], 5,
            key=f"cw_{cat_id}",
        )
    weight_sum = sum(cat_weights.values())
    if weight_sum != 100:
        st.warning(f"Weights sum to {weight_sum}% — should be 100%")
    else:
        st.success("Weights sum to 100%")

kpi_active = {}
total_kpis = 0
active_count = 0

with st.sidebar.expander("KPI Configuration", expanded=False):
    for cat_id, cat_def in KPI_CATEGORIES.items():
        st.markdown(f"**{cat_def['label']}**")
        for kpi_id, kpi_def in cat_def["kpis"].items():
            total_kpis += 1
            is_active = st.checkbox(
                kpi_def["label"],
                value=kpi_def["wave_1_active"],
                key=f"kpi_toggle_{kpi_id}",
            )
            kpi_active[kpi_id] = is_active
            if is_active:
                active_count += 1
        st.markdown("---")
    st.caption(f"{active_count} of {total_kpis} KPIs active")

with st.sidebar.expander("Cluster Performance", expanded=False):
    perf_tabs = st.tabs([CLUSTER_SHORT_NAMES[c] for c in ["A", "B", "C"]])
    perf_data = {}
    for i, cid in enumerate(["A", "B", "C"]):
        defaults = CLUSTER_KPI_BASELINES[cid]
        with perf_tabs[i]:
            cluster_kpis = {}
            for cat_id, cat_def in KPI_CATEGORIES.items():
                active_in_cat = [k for k in cat_def["kpis"] if kpi_active.get(k, False)]
                if not active_in_cat:
                    continue
                st.markdown(f"**{cat_def['label']}**")
                for kpi_id in active_in_cat:
                    kpi_def = cat_def["kpis"][kpi_id]
                    default_val = defaults.get(kpi_id, kpi_def["min"])
                    # Handle float vs int slider
                    if isinstance(default_val, float) and kpi_def["max"] <= 5:
                        val = st.slider(
                            kpi_def["label"], float(kpi_def["min"]), float(kpi_def["max"]),
                            float(default_val), 0.01, key=f"kpi_{cid}_{kpi_id}",
                        )
                    else:
                        val = st.slider(
                            kpi_def["label"], int(kpi_def["min"]), int(kpi_def["max"]),
                            int(default_val), 1, key=f"kpi_{cid}_{kpi_id}",
                        )
                    cluster_kpis[kpi_id] = val
            # Also carry forward inactive KPI defaults (needed for scenarios/exports)
            for cat_def in KPI_CATEGORIES.values():
                for kpi_id in cat_def["kpis"]:
                    if kpi_id not in cluster_kpis:
                        cluster_kpis[kpi_id] = defaults.get(kpi_id, 0)
            perf_data[cid] = cluster_kpis

# Build score_args dict used by all incentive mechanisms
score_args = {
    "kpi_categories": KPI_CATEGORIES,
    "category_weights": cat_weights,
    "kpi_active": kpi_active,
}

with st.sidebar.expander("Incentive Mechanisms", expanded=False):
    st.caption("Performance Pool")
    withhold_pct = st.slider(
        "Withhold %", 0.5, 5.0, WITHHOLD_PERCENTAGE, 0.5, key="withhold_pct",
    )
    perf_target = st.slider(
        "Performance Target", 0, 100, PERFORMANCE_TARGET, 5, key="perf_target",
    )
    perf_floor = st.slider(
        "Performance Floor", 0, 100, PERFORMANCE_FLOOR, 5, key="perf_floor",
    )

    st.markdown("---")
    st.caption("Capability Investment")
    capability_threshold = st.slider(
        "Capability Threshold", 0, 100, CAPABILITY_THRESHOLD, 5, key="cap_threshold",
        help="Clusters scoring below this enter the Capability Investment track",
    )
    investment_per_gap = st.slider(
        "Investment per Gap Point (SAR)", 10_000, 100_000, CAPABILITY_INVESTMENT_PER_GAP, 10_000,
        key="inv_per_gap",
    )

    st.markdown("---")
    st.caption("Shared Savings")
    cnhi_share = st.slider(
        "CNHI Share (%)", 0, 100, SAVINGS_SPLIT_CNHI, 5, key="cnhi_share",
    )
    cluster_share = 100 - cnhi_share
    st.caption(f"Cluster Share: {cluster_share}%")

    st.markdown("---")
    st.caption("Tier Payouts")
    tier1_pct = st.slider("Tier 1 Payout %", 0.0, 5.0, 0.5, 0.25, key="t1")
    tier2_pct = st.slider("Tier 2 Payout %", 0.0, 5.0, 1.5, 0.25, key="t2")
    tier3_pct = st.slider("Tier 3 Payout %", 0.0, 10.0, 3.0, 0.5, key="t3")

tier_config = [
    (0, 49, 0.0, "No Payout"),
    (50, 64, tier1_pct, "Tier 1"),
    (65, 79, tier2_pct, "Tier 2"),
    (80, 100, tier3_pct, "Tier 3"),
]

with st.sidebar.expander("Quality Gates", expanded=False):
    qg_diabetes = st.slider(
        "Diabetes HbA1c Control (min %)", 0, 100, QUALITY_GATE_DIABETES, 5, key="qg_diab",
    )
    qg_readmission = st.slider(
        "Readmission Rate (max %)", 0, 30, QUALITY_GATE_READMISSION, 1, key="qg_readm",
    )
    qg_composite = st.slider(
        "Composite Score (min)", 0, 100, QUALITY_GATE_COMPOSITE, 5, key="qg_comp",
        help="Minimum composite performance score to qualify for shared savings",
    )

# ── Module 5: Year 2 Projection ────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown(
    f'<p style="color: {COLORS["teal"]}; font-weight: 700; font-size: 0.85rem; '
    f'margin: 4px 0 2px 0; padding: 0;">Module 5 — Year 2 Projection</p>',
    unsafe_allow_html=True,
)

with st.sidebar.expander("Elasticity Assumptions", expanded=False):
    elasticity_factor = st.slider(
        "Efficiency Elasticity Factor", 0.0, 1.0, ELASTICITY_FACTOR_DEFAULT, 0.05,
        key="elasticity",
        help="Proportion of Year 1 efficiency improvement that carries through to Year 2 RAC budget reduction. "
             "0.5 = a 10% efficiency gain reduces next year's RAC by 5%.",
    )


# ─── Load data ───────────────────────────────────────────────────────────────
population = load_population()
risk_scores = calculate_risk_scores(
    population, disease_weights=dw, comorbidity_terms=comorbidity_overrides,
)
population["risk_score"] = risk_scores
rac_summary = calculate_rac_payments(population, risk_scores, base_pmpm)


# ─── Tabs ───────────────────────────────────────────────────────────────────
tab_docs, tab_platform = st.tabs(["📖 Documentation", "🏥 Platform"])

with tab_docs:
    render_docs()

with tab_platform:

    # ═════════════════════════════════════════════════════════════════════════
    # HEADER
    # ═════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['navy']} 0%, #1a2d4a 100%);
                padding: 24px 32px; border-radius: 12px; margin-bottom: 24px;">
        <h1 style="color: white; margin: 0; border: none; font-size: 1.8rem;">
            CNHI Incentive Intelligence Platform
        </h1>
        <p style="color: {COLORS['teal']}; margin: 4px 0 0 0; font-size: 1.05rem;">
            Risk-Adjusted Capitation & Performance-Based Incentive Simulation
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("About this Platform", expanded=False):
        st.markdown("""
        This is a proof-of-concept demonstration of the **Incentive Intelligence Platform**
        being developed by **Arthur D. Little** for CNHI. It uses synthetic data to simulate
        how a performance-based financial incentive model operates on top of Risk-Adjusted
        Capitation payments.

        **Health clusters** are ACO-style networks of hospitals, primary care centres, and
        community health facilities serving geographically defined populations across Saudi Arabia.
        Each cluster is incentivised as a single entity, aligning financial accountability with
        population health outcomes.

        The model uses a **dual-track incentive system**: clusters scoring above the capability
        threshold receive performance-based financial rewards, while underperforming clusters
        receive capability investment packages to build their capacity.

        All patient data is **synthetic** and generated for demonstration purposes only.

        *This POC demonstrates the public sector cluster incentive model. A private sector
        accreditation-based module is planned for a future version.*
        """)


    # ═════════════════════════════════════════════════════════════════════════════
    # MODULE 1: SYNTHETIC PATIENT POPULATION
    # ═════════════════════════════════════════════════════════════════════════════
    st.markdown("## 1. Synthetic Patient Population")
    st.markdown(
        "A synthetic cohort of **50,000 patients** distributed across three health cluster panels "
        "with demographics reflecting Saudi Arabia's population structure."
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Patients", f"{len(population):,}")
    with col2:
        st.metric("Health Clusters", "3")
    with col3:
        st.metric("Mean Age", f"{population['age'].mean():.1f} years")
    with col4:
        st.metric("Avg Comorbidities", f"{population['comorbidity_count'].mean():.2f}")

    pcols = st.columns(3)
    for i, (cid, profile) in enumerate(CLUSTER_PROFILES.items()):
        clust_data = population[population["cluster_id"] == cid]
        rac_row = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]
        color = CLUSTER_COLORS[cid]

        with pcols[i]:
            st.markdown(
                f'<div style="background: {color}; '
                f'padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">'
                f'<span style="font-weight: 700; color: white; font-size: 1.1rem;">'
                f'Cluster {cid}</span><br/>'
                f'<span style="color: rgba(255,255,255,0.85); font-size: 0.9rem;">'
                f'{profile["name"]}</span></div>',
                unsafe_allow_html=True,
            )
            st.metric("Patients", f"{len(clust_data):,}")
            st.metric("Avg Risk Score", f"{rac_row['avg_risk_score']:.2f}")

    with st.expander("Population Detail — Age, Disease Prevalence & Risk Profiles", expanded=False):

        st.markdown("#### Age Distribution by Cluster")
        fig_age = px.histogram(
            population, x="age", color="cluster_id", barmode="overlay", nbins=40,
            color_discrete_map=CLUSTER_COLORS,
            labels={"age": "Patient Age", "cluster_id": "Cluster", "count": "Patients"},
            opacity=0.65,
        )
        fig_age.update_layout(
            template="plotly_white", height=380, legend_title_text="Cluster",
            xaxis_title="Age", yaxis_title="Number of Patients",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig_age, use_container_width=True)

        st.markdown("#### Chronic Disease Prevalence by Cluster")
        conditions = ["has_diabetes", "has_cvd", "has_respiratory", "has_mental_health", "has_obesity"]
        condition_labels = {
            "has_diabetes": "Diabetes", "has_cvd": "CVD", "has_respiratory": "Respiratory",
            "has_mental_health": "Mental Health", "has_obesity": "Obesity",
        }
        prev_rows = []
        for cid in ["A", "B", "C"]:
            clust_data = population[population["cluster_id"] == cid]
            for cond in conditions:
                prev_rows.append({
                    "Cluster": f"Cluster {cid}", "Condition": condition_labels[cond],
                    "Prevalence (%)": round(clust_data[cond].mean() * 100, 1),
                })
        prev_df = pd.DataFrame(prev_rows)
        fig_prev = px.bar(
            prev_df, x="Condition", y="Prevalence (%)", color="Cluster", barmode="group",
            color_discrete_map={f"Cluster {c}": CLUSTER_COLORS[c] for c in ["A", "B", "C"]},
            text="Prevalence (%)",
        )
        fig_prev.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_prev.update_layout(
            template="plotly_white", height=400, yaxis_title="Prevalence (%)", xaxis_title="",
            font=dict(family="Inter, sans-serif"), legend_title_text="Cluster",
        )
        st.plotly_chart(fig_prev, use_container_width=True)

        st.markdown("#### Risk Profile Comparison")
        table_rows = []
        for cid in ["A", "B", "C"]:
            clust_data = population[population["cluster_id"] == cid]
            rac_row = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]
            table_rows.append({
                "Cluster": cluster_label(cid),
                "Panel Size": f"{int(rac_row['panel_size']):,}",
                "Mean Age": f"{clust_data['age'].mean():.1f}",
                "% Female": f"{(clust_data['sex'] == 'F').mean() * 100:.1f}%",
                "Diabetes (%)": f"{clust_data['has_diabetes'].mean() * 100:.1f}%",
                "CVD (%)": f"{clust_data['has_cvd'].mean() * 100:.1f}%",
                "Avg Comorbidities": f"{clust_data['comorbidity_count'].mean():.2f}",
                "Avg Risk Score": f"{rac_row['avg_risk_score']:.2f}",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)


    # ═════════════════════════════════════════════════════════════════════════════
    # MODULE 2: RAC CALCULATION ENGINE
    # ═════════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 2. RAC Calculation Engine")
    st.markdown(
        "Risk-adjusted capitation payments derived from patient-level risk scores. "
        "Adjust the **Base PMPM Rate** and **Disease Weights** in the sidebar to see how payments shift."
    )

    total_rac = rac_summary["total_rac_payment"].sum()
    flat_per_capita = base_pmpm * 12

    m2c1, m2c2, m2c3 = st.columns(3)
    with m2c1:
        st.metric("Base PMPM Rate", fmt_sar(base_pmpm))
    with m2c2:
        st.metric("Annual Per-Capita (flat)", fmt_sar(flat_per_capita))
    with m2c3:
        st.metric("Total RAC Budget", fmt_sar(total_rac))

    payment_rows = []
    for cid in ["A", "B", "C"]:
        rac_row = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]
        payment_rows.append({
            "Cluster": cluster_label(cid),
            "Panel Size": f"{int(rac_row['panel_size']):,}",
            "Avg Risk Score": f"{rac_row['avg_risk_score']:.2f}",
            "Total RAC Payment": fmt_sar(rac_row['total_rac_payment']),
            "Per-Capita Payment": fmt_sar(rac_row['per_capita_payment']),
        })
    payment_rows.append({
        "Cluster": "TOTAL",
        "Panel Size": f"{int(rac_summary['panel_size'].sum()):,}",
        "Avg Risk Score": f"{risk_scores.mean():.2f}",
        "Total RAC Payment": fmt_sar(rac_summary['total_rac_payment'].sum()),
        "Per-Capita Payment": fmt_sar(rac_summary['total_rac_payment'].sum() / rac_summary['panel_size'].sum()),
    })
    st.dataframe(pd.DataFrame(payment_rows), use_container_width=True, hide_index=True)

    with st.expander("RAC Detail — Risk Distributions, Flat vs. RAC Comparison", expanded=False):

        st.markdown("#### Risk Score Distribution by Cluster")
        fig_risk = px.histogram(
            population, x="risk_score", color="cluster_id", barmode="overlay", nbins=50,
            color_discrete_map=CLUSTER_COLORS,
            labels={"risk_score": "Risk Score", "cluster_id": "Cluster"}, opacity=0.6,
        )
        fig_risk.update_layout(
            template="plotly_white", height=380, legend_title_text="Cluster",
            xaxis_title="Patient Risk Score", yaxis_title="Number of Patients",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig_risk, use_container_width=True)

        st.markdown("#### Risk Adjustment Impact: Flat Capitation vs. RAC")
        callout_rows = []
        for cid in ["A", "B", "C"]:
            rac_row = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]
            flat_total = flat_per_capita * rac_row["panel_size"]
            rac_total = rac_row["total_rac_payment"]
            diff = rac_total - flat_total
            callout_rows.append({
                "Cluster": cluster_label(cid),
                "Flat Capitation Total": fmt_sar(flat_total),
                "RAC Total": fmt_sar(rac_total),
                "Difference": fmt_sar(diff),
                "Impact": "Underpaid without RAC" if diff > 0 else "Overpaid without RAC",
            })

        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.dataframe(pd.DataFrame(callout_rows), use_container_width=True, hide_index=True)
        with col_right:
            clust_a_diff = rac_summary[rac_summary["cluster_id"] == "A"].iloc[0]["total_rac_payment"] - flat_per_capita * rac_summary[rac_summary["cluster_id"] == "A"].iloc[0]["panel_size"]
            clust_c_diff = rac_summary[rac_summary["cluster_id"] == "C"].iloc[0]["total_rac_payment"] - flat_per_capita * rac_summary[rac_summary["cluster_id"] == "C"].iloc[0]["panel_size"]
            st.markdown(
                f'<div style="background: {COLORS["navy"]}; color: white; padding: 16px; '
                f'border-radius: 8px; font-size: 0.9rem;">'
                f'<strong style="color: {COLORS["teal"]};">Key Insight</strong><br/><br/>'
                f'Under flat capitation, <strong>Cluster A (Riyadh 1st)</strong> would be underpaid by '
                f'<strong style="color: {COLORS["teal"]};">{fmt_sar(abs(clust_a_diff))}</strong> '
                f'annually, while <strong>Cluster C (Madinah)</strong> would be overpaid by '
                f'<strong style="color: {COLORS["gold"]};">{fmt_sar(abs(clust_c_diff))}</strong>.'
                f'</div>', unsafe_allow_html=True,
            )

        st.markdown("#### Payment Comparison: Flat vs. Risk-Adjusted")
        comp_data = []
        for cid in ["A", "B", "C"]:
            rac_row = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]
            flat_total = flat_per_capita * rac_row["panel_size"]
            comp_data.append({"Cluster": f"Cluster {cid}", "Method": "Flat Capitation", "Total Payment (SAR)": flat_total})
            comp_data.append({"Cluster": f"Cluster {cid}", "Method": "Risk-Adjusted (RAC)", "Total Payment (SAR)": rac_row["total_rac_payment"]})
        fig_comp = px.bar(
            pd.DataFrame(comp_data), x="Cluster", y="Total Payment (SAR)", color="Method", barmode="group",
            color_discrete_map={"Flat Capitation": COLORS["mid_grey"], "Risk-Adjusted (RAC)": COLORS["teal"]},
            text_auto=".3s",
        )
        fig_comp.update_layout(
            template="plotly_white", height=400, yaxis_title="Total Annual Payment (SAR)", xaxis_title="",
            font=dict(family="Inter, sans-serif"), legend_title_text="",
        )
        fig_comp.update_traces(textposition="outside")
        st.plotly_chart(fig_comp, use_container_width=True)


    # ═════════════════════════════════════════════════════════════════════════════
    # MODULE 3: PERFORMANCE INCENTIVE SIMULATION
    # ═════════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 3. Performance Incentive Simulation")
    st.markdown(
        "Four incentive mechanisms layered on top of RAC payments, with a dual-track system: "
        "**Performance Rewards** for clusters above the capability threshold, "
        "**Capability Investment** for those below."
    )

    # Compute composite scores for display and track assignment
    cluster_scores = {}
    cluster_cat_scores = {}
    for cid in ["A", "B", "C"]:
        score, cats = compute_composite_score(perf_data[cid], KPI_CATEGORIES, cat_weights, kpi_active)
        cluster_scores[cid] = score
        cluster_cat_scores[cid] = cats

    # Assign tracks
    cluster_tracks = {}
    cluster_investments = {}
    for cid in ["A", "B", "C"]:
        if cluster_scores[cid] >= capability_threshold:
            cluster_tracks[cid] = "Performance Rewards"
            cluster_investments[cid] = 0.0
        else:
            cluster_tracks[cid] = "Capability Investment"
            gap = capability_threshold - cluster_scores[cid]
            cluster_investments[cid] = gap * investment_per_gap

    # Run mechanisms for Performance Rewards track only
    pool_df = performance_pool(rac_summary, perf_data, withhold_pct, perf_target, perf_floor, score_args)
    expectations_df = rac_adjusted_expectations(rac_summary, perf_data, score_args)
    savings_df = shared_savings(
        rac_summary, perf_data, qg_diabetes, qg_readmission, qg_composite,
        cnhi_share, cluster_share, score_args,
    )
    tier_df = tiered_tranches(rac_summary, perf_data, tier_config, score_args)
    combined_df, cnhi_net_incentives, cnhi_savings_retained = combined_summary(
        rac_summary, pool_df, savings_df, tier_df,
    )

    # Override Track 2 clusters: zero out incentive mechanisms, keep RAC base
    for cid in ["A", "B", "C"]:
        if cluster_tracks[cid] == "Capability Investment":
            mask = combined_df["cluster_id"] == cid
            combined_df.loc[mask, "pool_withheld"] = 0.0
            combined_df.loc[mask, "pool_earned"] = 0.0
            combined_df.loc[mask, "savings_share"] = 0.0
            combined_df.loc[mask, "tier_bonus"] = 0.0
            rac_base = combined_df.loc[mask, "rac_base"].values[0]
            combined_df.loc[mask, "total_payment"] = rac_base
            combined_df.loc[mask, "vs_rac_base"] = 0.0

    # ─── Combined summary (always visible) ──────────────────────────────────────
    st.markdown("### Combined Financial Summary")

    summary_rows = []
    for _, row in combined_df.iterrows():
        cid = row["cluster_id"]
        track = cluster_tracks[cid]
        summary_rows.append({
            "Cluster": cluster_label(cid),
            "Track": track,
            "RAC Base": fmt_sar(row["rac_base"]),
            "Pool Withheld": fmt_sar(-row["pool_withheld"]) if track == "Performance Rewards" else "—",
            "Pool Earned": fmt_sar(row["pool_earned"]) if track == "Performance Rewards" else "—",
            "Savings Share": fmt_sar(row["savings_share"]) if track == "Performance Rewards" else "—",
            "Tier Bonus": fmt_sar(row["tier_bonus"]) if track == "Performance Rewards" else "—",
            "Capability Investment": fmt_sar(cluster_investments[cid]) if track == "Capability Investment" else "—",
            "Total Payment": fmt_sar(row["total_payment"]),
            "vs. RAC Base": fmt_sar(row["vs_rac_base"]),
        })

    # CNHI totals
    total_paid = combined_df["total_payment"].sum()
    total_rac_base = combined_df["rac_base"].sum()
    total_track1_incentives = sum(
        combined_df[combined_df["cluster_id"] == cid]["vs_rac_base"].values[0]
        for cid in ["A", "B", "C"] if cluster_tracks[cid] == "Performance Rewards"
    )
    total_capability_investment = sum(cluster_investments.values())
    total_programme_cost = total_track1_incentives + total_capability_investment

    summary_rows.append({
        "Cluster": "CNHI Total Exposure",
        "Track": "",
        "RAC Base": fmt_sar(total_rac_base),
        "Pool Withheld": "",
        "Pool Earned": "",
        "Savings Share": fmt_sar(-cnhi_savings_retained),
        "Tier Bonus": "",
        "Capability Investment": fmt_sar(total_capability_investment),
        "Total Payment": fmt_sar(total_paid),
        "vs. RAC Base": fmt_sar(total_paid - total_rac_base),
    })

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    # Key callout metrics
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        st.metric("Total RAC Base", fmt_sar(total_rac_base))
    with kc2:
        st.metric("Incentive Payouts (Track 1)", fmt_sar(total_track1_incentives))
    with kc3:
        st.metric("Capability Investment (Track 2)", fmt_sar(total_capability_investment))
    with kc4:
        st.metric("Total Programme Cost", fmt_sar(total_programme_cost))

    # ─── Expandable mechanism details ────────────────────────────────────────────
    with st.expander("Incentive Detail — Mechanisms, League Table & Analysis", expanded=False):

      tab_pool, tab_expect, tab_savings, tab_tiers, tab_league = st.tabs([
          "Performance Pool", "RAC-Adjusted Expectations",
          "Shared Savings", "Tiered Tranches", "League Table",
      ])

      # ─── Tab 1: Performance Pool ───────────────────────────────────────────────
      with tab_pool:
          st.markdown("#### Mechanism 1 — Performance Pool")
          st.markdown(
              f"A **{withhold_pct:.1f}%** withhold from each cluster's RAC payment, "
              f"earned back based on composite performance score (target: {perf_target}, floor: {perf_floor}). "
              f"*Only applies to Performance Rewards track clusters.*"
          )
          pool_display = []
          for _, row in pool_df.iterrows():
              cid = row["cluster_id"]
              track = cluster_tracks[cid]
              pool_display.append({
                  "Cluster": cluster_label(cid),
                  "Track": track,
                  "Pool Size": fmt_sar(row["pool_size"]) if track == "Performance Rewards" else "N/A",
                  "Composite Score": f"{row['composite_score']:.1f}",
                  "Earned Back (%)": f"{row['earned_back_pct']:.1f}%" if track == "Performance Rewards" else "N/A",
                  "Earned Back": fmt_sar(row["earned_back"]) if track == "Performance Rewards" else "N/A",
                  "Net Impact": fmt_sar(row["net_impact"]) if track == "Performance Rewards" else "N/A",
              })
          st.dataframe(pd.DataFrame(pool_display), use_container_width=True, hide_index=True)

          pool_chart_data = []
          for _, row in pool_df.iterrows():
              cid = row["cluster_id"]
              if cluster_tracks[cid] == "Performance Rewards":
                  pool_chart_data.append({"Cluster": f"Cluster {cid}", "Component": "Withheld", "Amount (SAR)": -row["pool_size"]})
                  pool_chart_data.append({"Cluster": f"Cluster {cid}", "Component": "Earned Back", "Amount (SAR)": row["earned_back"]})
          if pool_chart_data:
              fig_pool = px.bar(
                  pd.DataFrame(pool_chart_data), x="Cluster", y="Amount (SAR)", color="Component",
                  barmode="group",
                  color_discrete_map={"Withheld": COLORS["red"], "Earned Back": COLORS["teal"]},
                  text_auto=".3s",
              )
              fig_pool.update_layout(template="plotly_white", height=350, font=dict(family="Inter, sans-serif"))
              fig_pool.update_traces(textposition="outside")
              st.plotly_chart(fig_pool, use_container_width=True)

      # ─── Tab 2: RAC-Adjusted Expectations ──────────────────────────────────────
      with tab_expect:
          st.markdown("#### Mechanism 2 — RAC-Adjusted Expectations")
          st.markdown(
              "Clusters are evaluated relative to their risk profile. "
              "Those above the regression line outperform given their population risk."
          )

          a_coeff = expectations_df["regression_intercept"].iloc[0]
          b_coeff = expectations_df["regression_slope"].iloc[0]

          fig_expect = go.Figure()
          x_range = np.linspace(
              expectations_df["avg_risk_score"].min() - 0.1,
              expectations_df["avg_risk_score"].max() + 0.1, 50,
          )
          fig_expect.add_trace(go.Scatter(
              x=x_range, y=a_coeff + b_coeff * x_range,
              mode="lines", name="Expected Performance",
              line=dict(color=COLORS["mid_grey"], dash="dash", width=2),
          ))
          for _, row in expectations_df.iterrows():
              cid = row["cluster_id"]
              color = CLUSTER_COLORS[cid]
              fig_expect.add_trace(go.Scatter(
                  x=[row["avg_risk_score"]], y=[row["composite_score"]],
                  mode="markers+text", name=f"Cluster {cid}",
                  marker=dict(size=18, color=color),
                  text=[f"Cluster {cid}"], textposition="top center",
                  textfont=dict(size=13, color=color),
              ))
          fig_expect.update_layout(
              template="plotly_white", height=420,
              xaxis_title="Average Risk Score", yaxis_title="Composite Performance Score",
              font=dict(family="Inter, sans-serif"), showlegend=True,
          )
          st.plotly_chart(fig_expect, use_container_width=True)

          for _, row in expectations_df.iterrows():
              cid = row["cluster_id"]
              residual = row["residual"]
              color = COLORS["teal"] if residual > 0 else COLORS["red"]
              lbl = "outperforms" if residual > 0 else "underperforms"
              st.markdown(
                  f'<span style="color: {color}; font-weight: 600;">Cluster {cid}</span> '
                  f'{lbl} expectations by **{abs(residual):.1f}** points '
                  f'(actual: {row["composite_score"]:.1f}, expected: {row["expected_score"]:.1f})',
                  unsafe_allow_html=True,
              )

      # ─── Tab 3: Shared Savings ─────────────────────────────────────────────────
      with tab_savings:
          st.markdown("#### Mechanism 3 — Shared Savings with Quality Gates")
          st.markdown(
              f"Clusters must pass **all three quality gates** to be eligible for savings sharing "
              f"(CNHI {cnhi_share}% / Cluster {cluster_share}%). "
              f"*Only applies to Performance Rewards track clusters.*"
          )

          gate_display = []
          for _, row in savings_df.iterrows():
              cid = row["cluster_id"]
              track = cluster_tracks[cid]
              gate_display.append({
                  "Cluster": cluster_label(cid),
                  "Track": track,
                  "Diabetes Gate": "PASS" if row["gate_diabetes"] else "FAIL",
                  "Readmission Gate": "PASS" if row["gate_readmission"] else "FAIL",
                  "Composite Gate": "PASS" if row["gate_composite"] else "FAIL",
                  "Overall": "PASS" if row["gate_passed"] else "FAIL",
                  "Gross Savings": fmt_sar(row["gross_savings"]),
                  "Eligible Savings": fmt_sar(row["eligible_savings"]) if track == "Performance Rewards" else "N/A",
                  "Cluster Share": fmt_sar(row["cluster_share"]) if track == "Performance Rewards" else "N/A",
              })
          st.dataframe(pd.DataFrame(gate_display), use_container_width=True, hide_index=True)

          for _, row in savings_df.iterrows():
              cid = row["cluster_id"]
              if cluster_tracks[cid] != "Performance Rewards":
                  continue

              fig_wf = go.Figure(go.Waterfall(
                  x=["RAC Budget", "Actual Spend", "Gross Savings",
                     "Quality Gate" if not row["gate_passed"] else "Eligible Savings",
                     "Cluster Share"],
                  measure=["absolute", "absolute", "relative", "relative", "absolute"],
                  y=[
                      row["rac_budget"], row["actual_spend"], row["gross_savings"],
                      0 if row["gate_passed"] else -row["gross_savings"],
                      row["cluster_share"],
                  ],
                  connector=dict(line=dict(color="rgba(63, 63, 63, 0.3)")),
                  increasing=dict(marker=dict(color=COLORS["teal"])),
                  decreasing=dict(marker=dict(color=COLORS["red"])),
                  totals=dict(marker=dict(color=COLORS["gold"])),
                  text=[
                      fmt_sar(row["rac_budget"]), fmt_sar(row["actual_spend"]),
                      fmt_sar(row["gross_savings"]),
                      "Blocked" if not row["gate_passed"] else fmt_sar(row["eligible_savings"]),
                      fmt_sar(row["cluster_share"]),
                  ],
                  textposition="outside",
              ))
              gate_status = "PASSED" if row["gate_passed"] else "BLOCKED"
              fig_wf.update_layout(
                  template="plotly_white", height=320,
                  title=dict(text=f"Cluster {cid} — Savings Waterfall (Quality Gate: {gate_status})", font=dict(size=14)),
                  font=dict(family="Inter, sans-serif"), showlegend=False,
              )
              st.plotly_chart(fig_wf, use_container_width=True)

      # ─── Tab 4: Tiered Tranches ────────────────────────────────────────────────
      with tab_tiers:
          st.markdown("#### Mechanism 4 — Tiered Tranches")
          st.markdown(
              "Composite performance score mapped to bonus tiers. "
              "*Only applies to Performance Rewards track clusters.*"
          )

          tier_display = []
          for _, row in tier_df.iterrows():
              cid = row["cluster_id"]
              track = cluster_tracks[cid]
              tier_display.append({
                  "Cluster": cluster_label(cid),
                  "Track": track,
                  "Composite Score": f"{row['composite_score']:.1f}",
                  "Tier": row["tier"] if track == "Performance Rewards" else "N/A",
                  "Payout %": f"{row['payout_pct']:.1f}%" if track == "Performance Rewards" else "N/A",
                  "Bonus": fmt_sar(row["bonus"]) if track == "Performance Rewards" else "N/A",
              })
          st.dataframe(pd.DataFrame(tier_display), use_container_width=True, hide_index=True)

          tier_colors = {"No Payout": COLORS["mid_grey"], "Tier 1": "#CD7F32", "Tier 2": "#C0C0C0", "Tier 3": COLORS["gold"]}
          # Only chart Track 1 clusters
          track1_tier = tier_df[tier_df["cluster_id"].isin([c for c in ["A", "B", "C"] if cluster_tracks[c] == "Performance Rewards"])]
          if not track1_tier.empty:
              fig_tier = px.bar(
                  track1_tier,
                  x=track1_tier["cluster_id"].apply(lambda c: f"Cluster {c}"),
                  y="bonus", color="tier", color_discrete_map=tier_colors,
                  text=track1_tier["bonus"].apply(lambda v: fmt_sar(v)),
                  labels={"x": "", "bonus": "Bonus (SAR)", "tier": "Tier"},
              )
              fig_tier.update_layout(
                  template="plotly_white", height=380, yaxis_title="Bonus (SAR)",
                  font=dict(family="Inter, sans-serif"),
              )
              fig_tier.update_traces(textposition="outside")
              st.plotly_chart(fig_tier, use_container_width=True)

          st.markdown("**Tier Thresholds:**")
          tier_ref = pd.DataFrame([
              {"Tier": name, "Score Range": f"{lo}-{hi}", "Payout": f"{pct:.1f}%"}
              for lo, hi, pct, name in tier_config
          ])
          st.dataframe(tier_ref, use_container_width=True, hide_index=True)

      # ─── Tab 5: League Table ───────────────────────────────────────────────────
      with tab_league:
          st.markdown("#### Cluster League Table")
          st.info(
              "This league table ranks clusters by composite performance score for "
              "transparency and benchmarking. Rankings do not determine incentive "
              "payouts — each cluster's incentives are calculated independently "
              "based on its own performance against RAC-adjusted expectations."
          )

          # Build league data
          league_rows = []
          for cid in ["A", "B", "C"]:
              row_data = combined_df[combined_df["cluster_id"] == cid].iloc[0]
              track = cluster_tracks[cid]
              incentive_or_investment = (
                  row_data["vs_rac_base"] if track == "Performance Rewards"
                  else cluster_investments[cid]
              )
              league_rows.append({
                  "cluster_id": cid,
                  "Cluster": CLUSTER_PROFILES[cid]["name"],
                  "Composite Score": cluster_scores[cid],
                  "Clinical": round(cluster_cat_scores[cid].get("clinical_outcomes", 0), 1),
                  "Efficiency": round(cluster_cat_scores[cid].get("efficiency_improvement", 0), 1),
                  "Data Quality": round(cluster_cat_scores[cid].get("data_quality", 0), 1),
                  "Data Reporting": round(cluster_cat_scores[cid].get("data_reporting", 0), 1),
                  "Track": track,
                  "Incentive / Investment": incentive_or_investment,
              })
          league_df = pd.DataFrame(league_rows).sort_values("Composite Score", ascending=False)
          league_df.insert(0, "Rank", range(1, len(league_df) + 1))

          # Display table
          league_display = league_df.copy()
          league_display["Incentive / Investment"] = league_display["Incentive / Investment"].apply(fmt_sar)
          league_display["Composite Score"] = league_display["Composite Score"].apply(lambda x: f"{x:.1f}")
          st.dataframe(
              league_display.drop(columns=["cluster_id"]),
              use_container_width=True, hide_index=True,
          )

          # Horizontal bar chart
          fig_league = go.Figure()
          for _, lrow in league_df.iterrows():
              cid = lrow["cluster_id"]
              bar_color = COLORS["teal"] if lrow["Track"] == "Performance Rewards" else COLORS["amber"]
              fig_league.add_trace(go.Bar(
                  y=[CLUSTER_PROFILES[cid]["name"]],
                  x=[lrow["Composite Score"]],
                  orientation="h",
                  marker_color=bar_color,
                  text=[f"{lrow['Composite Score']:.1f}"],
                  textposition="outside",
                  showlegend=False,
              ))

          # Capability threshold line
          fig_league.add_vline(
              x=capability_threshold, line_dash="dash", line_color=COLORS["red"], line_width=2,
              annotation_text=f"Threshold: {capability_threshold}",
              annotation_position="top right",
          )
          fig_league.update_layout(
              template="plotly_white", height=250,
              xaxis_title="Composite Performance Score", yaxis_title="",
              xaxis=dict(range=[0, 100]),
              font=dict(family="Inter, sans-serif"),
          )
          st.plotly_chart(fig_league, use_container_width=True)


    # ═════════════════════════════════════════════════════════════════════════════
    # MODULE 4: SCENARIO COMPARISON
    # ═════════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## 4. Scenario Comparison")
    st.markdown(
        "Compare pre-built scenarios against the current baseline. "
        "Each scenario adjusts performance parameters and recalculates the full pipeline."
    )

    scenario_name = st.selectbox(
        "Select Scenario", list(SCENARIOS.keys()), index=0, key="scenario_selector",
    )
    st.markdown(f"**{scenario_name}:** {SCENARIOS[scenario_name]['description']}")

    sc_perf, sc_risk_mult, sc_budget_cap = apply_scenario(scenario_name, perf_data)

    if sc_risk_mult != 1.0:
        sc_risk_scores = risk_scores * sc_risk_mult
        sc_rac_summary = calculate_rac_payments(population, sc_risk_scores, base_pmpm)
    else:
        sc_risk_scores = risk_scores
        sc_rac_summary = rac_summary

    sc_pool = performance_pool(sc_rac_summary, sc_perf, withhold_pct, perf_target, perf_floor, score_args)
    sc_savings = shared_savings(
        sc_rac_summary, sc_perf, qg_diabetes, qg_readmission, qg_composite,
        cnhi_share, cluster_share, score_args,
    )
    sc_tiers = tiered_tranches(sc_rac_summary, sc_perf, tier_config, score_args)
    sc_combined, sc_cnhi_net, sc_cnhi_sav = combined_summary(
        sc_rac_summary, sc_pool, sc_savings, sc_tiers,
    )

    # Compute scenario scores & tracks
    sc_cluster_scores = {}
    sc_cluster_tracks = {}
    sc_cluster_investments = {}
    for cid in ["A", "B", "C"]:
        sc_score, _ = compute_composite_score(sc_perf[cid], KPI_CATEGORIES, cat_weights, kpi_active)
        sc_cluster_scores[cid] = sc_score
        if sc_score >= capability_threshold:
            sc_cluster_tracks[cid] = "Performance Rewards"
            sc_cluster_investments[cid] = 0.0
        else:
            sc_cluster_tracks[cid] = "Capability Investment"
            sc_cluster_investments[cid] = (capability_threshold - sc_score) * investment_per_gap

    # Override Track 2 clusters in scenario
    for cid in ["A", "B", "C"]:
        if sc_cluster_tracks[cid] == "Capability Investment":
            mask = sc_combined["cluster_id"] == cid
            sc_combined.loc[mask, "pool_withheld"] = 0.0
            sc_combined.loc[mask, "pool_earned"] = 0.0
            sc_combined.loc[mask, "savings_share"] = 0.0
            sc_combined.loc[mask, "tier_bonus"] = 0.0
            rac_base = sc_combined.loc[mask, "rac_base"].values[0]
            sc_combined.loc[mask, "total_payment"] = rac_base
            sc_combined.loc[mask, "vs_rac_base"] = 0.0

    # Budget cap on total programme cost
    sc_total_track1 = sum(
        sc_combined[sc_combined["cluster_id"] == c]["vs_rac_base"].values[0]
        for c in ["A", "B", "C"] if sc_cluster_tracks[c] == "Performance Rewards"
    )
    sc_total_cap_invest = sum(sc_cluster_investments.values())
    sc_programme_cost = sc_total_track1 + sc_total_cap_invest

    cap_applied = False
    cap_reduction = 1.0
    if sc_budget_cap is not None and sc_programme_cost > sc_budget_cap:
        cap_applied = True
        cap_reduction = sc_budget_cap / sc_programme_cost
        # Reduce Track 1 incentives
        for cid in ["A", "B", "C"]:
            if sc_cluster_tracks[cid] == "Performance Rewards":
                mask = sc_combined["cluster_id"] == cid
                sc_combined.loc[mask, "pool_earned"] *= cap_reduction
                sc_combined.loc[mask, "savings_share"] *= cap_reduction
                sc_combined.loc[mask, "tier_bonus"] *= cap_reduction
                rac_b = sc_combined.loc[mask, "rac_base"].values[0]
                pw = sc_combined.loc[mask, "pool_withheld"].values[0]
                pe = sc_combined.loc[mask, "pool_earned"].values[0]
                ss = sc_combined.loc[mask, "savings_share"].values[0]
                tb = sc_combined.loc[mask, "tier_bonus"].values[0]
                sc_combined.loc[mask, "total_payment"] = rac_b - pw + pe + ss + tb
                sc_combined.loc[mask, "vs_rac_base"] = sc_combined.loc[mask, "total_payment"].values[0] - rac_b
        # Reduce Track 2 investments
        for cid in ["A", "B", "C"]:
            if sc_cluster_tracks[cid] == "Capability Investment":
                sc_cluster_investments[cid] *= cap_reduction

    sc_total_paid = sc_combined["total_payment"].sum()
    sc_total_rac_base = sc_combined["rac_base"].sum()

    if cap_applied:
        st.warning(
            f"Budget cap of {fmt_sar(sc_budget_cap)} applied — "
            f"all incentives and investments reduced by {(1 - cap_reduction) * 100:.1f}%."
        )

    st.markdown("### Baseline vs. Scenario")
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("Baseline Total", fmt_sar(total_paid))
    with sc2:
        st.metric("Scenario Total", fmt_sar(sc_total_paid))
    with sc3:
        change = sc_total_paid - total_paid
        st.metric("Change", fmt_sar(change))
    with sc4:
        pct_change = (change / total_paid * 100) if total_paid != 0 else 0
        st.metric("Change (%)", f"{pct_change:+.2f}%")

    compare_rows = []
    for cid in ["A", "B", "C"]:
        base_row = combined_df[combined_df["cluster_id"] == cid].iloc[0]
        sc_row = sc_combined[sc_combined["cluster_id"] == cid].iloc[0]
        compare_rows.append({
            "Cluster": cluster_label(cid),
            "Baseline Track": cluster_tracks[cid],
            "Scenario Track": sc_cluster_tracks[cid],
            "Baseline Total": fmt_sar(base_row["total_payment"]),
            "Scenario Total": fmt_sar(sc_row["total_payment"]),
            "Change": fmt_sar(sc_row["total_payment"] - base_row["total_payment"]),
        })
    compare_rows.append({
        "Cluster": "CNHI Total",
        "Baseline Track": "",
        "Scenario Track": "",
        "Baseline Total": fmt_sar(total_paid),
        "Scenario Total": fmt_sar(sc_total_paid),
        "Change": fmt_sar(sc_total_paid - total_paid),
    })
    st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)

    with st.expander("Scenario Detail — Full Breakdown & Sensitivity Analysis", expanded=False):

        st.markdown("#### Scenario Financial Breakdown")
        sc_detail_rows = []
        for _, row in sc_combined.iterrows():
            cid = row["cluster_id"]
            sc_detail_rows.append({
                "Cluster": cluster_label(cid),
                "Track": sc_cluster_tracks[cid],
                "RAC Base": fmt_sar(row["rac_base"]),
                "Pool Withheld": fmt_sar(-row["pool_withheld"]),
                "Pool Earned": fmt_sar(row["pool_earned"]),
                "Savings Share": fmt_sar(row["savings_share"]),
                "Tier Bonus": fmt_sar(row["tier_bonus"]),
                "Total Payment": fmt_sar(row["total_payment"]),
                "vs. RAC Base": fmt_sar(row["vs_rac_base"]),
            })
        st.dataframe(pd.DataFrame(sc_detail_rows), use_container_width=True, hide_index=True)

        st.markdown("#### Sensitivity Analysis — Tornado Diagram")
        st.markdown(
            "Shows which parameters have the largest impact on CNHI total financial exposure."
        )

        sensitivity_params = [
            ("Base PMPM Rate", "pmpm", base_pmpm, max(PMPM_MIN, base_pmpm - 200), min(PMPM_MAX, base_pmpm + 200)),
            ("Withhold %", "withhold", withhold_pct, max(0.5, withhold_pct - 1.5), min(5.0, withhold_pct + 1.5)),
            ("Quality Gate (Diabetes)", "qg_diab", qg_diabetes, max(0, qg_diabetes - 15), min(100, qg_diabetes + 15)),
            ("Quality Gate (Readmission)", "qg_readm", qg_readmission, max(0, qg_readmission - 5), min(30, qg_readmission + 5)),
            ("Quality Gate (Composite)", "qg_comp", qg_composite, max(0, qg_composite - 15), min(100, qg_composite + 15)),
            ("CNHI Savings Share %", "cnhi_sh", cnhi_share, max(0, cnhi_share - 20), min(100, cnhi_share + 20)),
            ("Tier 2 Payout %", "tier2", tier2_pct, max(0, tier2_pct - 1.0), min(5.0, tier2_pct + 1.0)),
            ("Tier 3 Payout %", "tier3", tier3_pct, max(0, tier3_pct - 1.5), min(10.0, tier3_pct + 1.5)),
        ]

        def _calc_cnhi_total(pmpm_o, wh_o, qgd_o, qgr_o, qgc_o, cs_o, t2_o, t3_o):
            r_summary = calculate_rac_payments(population, sc_risk_scores, pmpm_o)
            p = performance_pool(r_summary, sc_perf, wh_o, perf_target, perf_floor, score_args)
            s = shared_savings(r_summary, sc_perf, qgd_o, qgr_o, qgc_o, cs_o, 100 - cs_o, score_args)
            tc = [(0, 49, 0.0, "No Payout"), (50, 64, tier1_pct, "Tier 1"), (65, 79, t2_o, "Tier 2"), (80, 100, t3_o, "Tier 3")]
            t = tiered_tranches(r_summary, sc_perf, tc, score_args)
            c, _, _ = combined_summary(r_summary, p, s, t)
            # Apply track logic
            for cid_inner in ["A", "B", "C"]:
                if sc_cluster_tracks[cid_inner] == "Capability Investment":
                    m = c["cluster_id"] == cid_inner
                    c.loc[m, "total_payment"] = c.loc[m, "rac_base"]
            return c["total_payment"].sum()

        baseline_total = sc_total_paid
        tornado_data = []

        for label, key, current, lo, hi in sensitivity_params:
            args_base = [base_pmpm, withhold_pct, qg_diabetes, qg_readmission, qg_composite, cnhi_share, tier2_pct, tier3_pct]
            args_lo = list(args_base)
            args_hi = list(args_base)

            idx_map = {"pmpm": 0, "withhold": 1, "qg_diab": 2, "qg_readm": 3, "qg_comp": 4, "cnhi_sh": 5, "tier2": 6, "tier3": 7}
            idx = idx_map[key]
            args_lo[idx] = lo
            args_hi[idx] = hi

            total_lo = _calc_cnhi_total(*args_lo)
            total_hi = _calc_cnhi_total(*args_hi)

            tornado_data.append({
                "Parameter": label,
                "Low": total_lo - baseline_total,
                "High": total_hi - baseline_total,
                "Span": abs(total_hi - total_lo),
            })

        tornado_df = pd.DataFrame(tornado_data).sort_values("Span", ascending=True)

        fig_tornado = go.Figure()
        fig_tornado.add_trace(go.Bar(
            y=tornado_df["Parameter"], x=tornado_df["Low"], orientation="h",
            name="Low Swing", marker_color=COLORS["teal"],
            text=tornado_df["Low"].apply(lambda v: fmt_sar(v)), textposition="auto",
        ))
        fig_tornado.add_trace(go.Bar(
            y=tornado_df["Parameter"], x=tornado_df["High"], orientation="h",
            name="High Swing", marker_color=COLORS["red"],
            text=tornado_df["High"].apply(lambda v: fmt_sar(v)), textposition="auto",
        ))
        fig_tornado.update_layout(
            template="plotly_white", height=400, barmode="overlay",
            xaxis_title="Change in CNHI Total Exposure (SAR)", yaxis_title="",
            font=dict(family="Inter, sans-serif"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_tornado, use_container_width=True)


    # ═════════════════════════════════════════════════════════════════════════════
    # MODULE 5: YEAR 2 PROJECTION
    # ═════════════════════════════════════════════════════════════════════════════
    st.markdown("---")

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['navy']} 0%, #0d1b2a 100%);
                padding: 20px 28px; border-radius: 10px; margin-bottom: 16px;">
        <h2 style="color: white; margin: 0; border: none; font-size: 1.5rem;">
            5. Year 2 Projection — Long-Term Value Case
        </h2>
        <p style="color: {COLORS['teal']}; margin: 4px 0 0 0; font-size: 0.95rem;">
            Projecting how Year 1 efficiency gains translate into Year 2 RAC budget reductions
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Year 1 results
    year1_total_rac = rac_summary["total_rac_payment"].sum()
    year1_programme_cost = total_programme_cost

    # Calculate weighted average efficiency improvement
    weighted_eff_gain = 0.0
    total_pop = 0
    for cid in ["A", "B", "C"]:
        cer = perf_data[cid].get("cost_efficiency_ratio", 1.0)
        panel = rac_summary[rac_summary["cluster_id"] == cid].iloc[0]["panel_size"]
        gain = max(0, 1 - cer)
        weighted_eff_gain += gain * panel
        total_pop += panel
    avg_efficiency_gain = weighted_eff_gain / total_pop if total_pop > 0 else 0

    # Year 2 projection
    rac_reduction_pct = avg_efficiency_gain * elasticity_factor
    year2_total_rac = year1_total_rac * (1 - rac_reduction_pct)
    year2_rac_savings = year1_total_rac - year2_total_rac

    # Net position
    cumulative_net = year2_rac_savings - abs(year1_programme_cost)
    roi = year2_rac_savings / abs(year1_programme_cost) if year1_programme_cost != 0 else 0

    # Key metrics
    y1, y2, y3, y4 = st.columns(4)
    with y1:
        st.metric("Year 1 Programme Cost", fmt_sar(abs(year1_programme_cost)))
    with y2:
        st.metric("Year 2 RAC Reduction", fmt_sar(year2_rac_savings))
    with y3:
        net_color = "normal" if cumulative_net >= 0 else "inverse"
        st.metric("Cumulative Net", fmt_sar(cumulative_net))
    with y4:
        st.metric("ROI", f"{roi:.1f}x")

    with st.expander("Year 2 Detail — Budget Comparison, ROI & Sensitivity Analysis", expanded=False):

        # Side-by-side bar chart
        bar_data = pd.DataFrame([
            {"Year": "Year 1", "Component": "RAC Budget", "Amount": year1_total_rac},
            {"Year": "Year 1", "Component": "Programme Cost", "Amount": abs(year1_programme_cost)},
            {"Year": "Year 2", "Component": "RAC Budget", "Amount": year2_total_rac},
            {"Year": "Year 2", "Component": "Programme Cost", "Amount": abs(year1_programme_cost)},
        ])

        fig_y2 = px.bar(
            bar_data, x="Year", y="Amount", color="Component", barmode="group",
            color_discrete_map={"RAC Budget": COLORS["teal"], "Programme Cost": COLORS["red"]},
            text_auto=".3s",
        )
        fig_y2.update_layout(
            template="plotly_white", height=400,
            yaxis_title="Amount (SAR)", xaxis_title="",
            font=dict(family="Inter, sans-serif"), legend_title_text="",
        )
        fig_y2.update_traces(textposition="outside")

        # Add delta annotation
        fig_y2.add_annotation(
            x=1, y=max(year1_total_rac, year2_total_rac) * 1.05,
            text=f"RAC Reduction: {fmt_sar(year2_rac_savings)}", showarrow=False,
            font=dict(size=12, color=COLORS["teal"]),
        )
        st.plotly_chart(fig_y2, use_container_width=True)

        # ROI callout box
        if cumulative_net >= 0:
            roi_message = (
                f"Even at a conservative {elasticity_factor:.2f} elasticity, the incentive "
                f"programme generates a net positive return for CNHI by Year 2."
            )
        else:
            # Calculate break-even elasticity
            if avg_efficiency_gain > 0 and year1_total_rac > 0:
                breakeven_elasticity = abs(year1_programme_cost) / (avg_efficiency_gain * year1_total_rac)
                roi_message = (
                    f"At the current elasticity assumption, the programme reaches "
                    f"break-even at elasticity factor {breakeven_elasticity:.2f}."
                )
            else:
                roi_message = "Insufficient efficiency gain data to calculate break-even point."

        st.markdown(
            f'<div style="background: {COLORS["navy"]}; color: white; padding: 20px; '
            f'border-radius: 10px; border-left: 4px solid {COLORS["teal"]};">'
            f'<strong style="color: {COLORS["teal"]};">Return on Investment</strong><br/><br/>'
            f'At an elasticity factor of <strong>{elasticity_factor:.2f}</strong>:<br/>'
            f'&bull; Year 1 programme investment: <strong>{fmt_sar(abs(year1_programme_cost))}</strong><br/>'
            f'&bull; Year 2 projected RAC reduction: <strong>{fmt_sar(year2_rac_savings)}</strong><br/>'
            f'&bull; Return on investment: <strong>{roi:.1f}x</strong><br/><br/>'
            f'<em>{roi_message}</em>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Sensitivity line chart
        st.markdown("#### Break-Even Sensitivity")
        elasticity_range = np.arange(0.1, 1.05, 0.1)
        sensitivity_data = []
        for ef in elasticity_range:
            y2_savings = year1_total_rac * avg_efficiency_gain * ef
            net = y2_savings - abs(year1_programme_cost)
            sensitivity_data.append({"Elasticity Factor": round(ef, 1), "Cumulative Net (SAR)": net})

        sens_df = pd.DataFrame(sensitivity_data)
        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(
            x=sens_df["Elasticity Factor"], y=sens_df["Cumulative Net (SAR)"],
            mode="lines+markers", line=dict(color=COLORS["teal"], width=3),
            marker=dict(size=8),
        ))
        fig_sens.add_hline(y=0, line_dash="dash", line_color=COLORS["mid_grey"], line_width=1)
        fig_sens.add_vline(
            x=elasticity_factor, line_dash="dash", line_color=COLORS["gold"], line_width=2,
            annotation_text=f"Current: {elasticity_factor}", annotation_position="top right",
        )

        # Find and mark break-even point
        if avg_efficiency_gain > 0 and year1_total_rac > 0:
            be = abs(year1_programme_cost) / (avg_efficiency_gain * year1_total_rac)
            if 0 <= be <= 1.0:
                fig_sens.add_annotation(
                    x=be, y=0, text=f"Break-even: {be:.2f}",
                    showarrow=True, arrowhead=2, arrowcolor=COLORS["red"],
                    font=dict(size=11, color=COLORS["red"]),
                )

        fig_sens.update_layout(
            template="plotly_white", height=350,
            xaxis_title="Elasticity Factor", yaxis_title="Cumulative Net CNHI Position (SAR)",
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig_sens, use_container_width=True)


    # ─── Footer ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p style="text-align: center; color: {COLORS["mid_grey"]}; font-size: 0.8rem;">'
        f'CNHI Incentive Intelligence Platform — Arthur D. Little POC v2</p>',
        unsafe_allow_html=True,
    )
