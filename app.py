"""CNHI Incentive Intelligence Platform — Proof of Concept."""

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
    PROVIDER_COLORS,
    BASE_PMPM_RATE,
    PMPM_MIN,
    PMPM_MAX,
    DISEASE_WEIGHTS,
    AGE_SEX_ADJUSTMENTS,
    COMORBIDITY_TERMS,
    RANDOM_SEED,
    PERFORMANCE_BASELINES,
    WITHHOLD_PERCENTAGE,
    PERFORMANCE_TARGET,
    PERFORMANCE_FLOOR,
    QUALITY_GATE_DIABETES,
    QUALITY_GATE_READMISSION,
    QUALITY_GATE_SATISFACTION,
    SAVINGS_SPLIT_CNHI,
    SAVINGS_SPLIT_PROVIDER,
    TIER_THRESHOLDS,
)
from config.demographics import PROVIDER_PROFILES

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CNHI Incentive Intelligence Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
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
    .provider-tag {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }}
</style>
""", unsafe_allow_html=True)


# ─── Helper ────────────────────────────────────────────────────────────────────
def fmt_sar(value: float) -> str:
    """Format a number as SAR with commas."""
    if value < 0:
        return f"-{fmt_sar(-value)}"
    if value >= 1e6:
        return f"SAR {value:,.0f}"
    return f"SAR {value:,.2f}"


def provider_label(pid: str) -> str:
    return f"Provider {pid} — {PROVIDER_PROFILES[pid]['name']}"


# ─── Data generation (cached) ─────────────────────────────────────────────────
@st.cache_data(show_spinner="Generating synthetic patient population...")
def load_population(seed: int = RANDOM_SEED) -> pd.DataFrame:
    return generate_population(seed)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown(
    f'<div style="padding: 8px 0;">'
    f'<span style="font-size: 1.1rem; font-weight: 700; color: {COLORS["teal"]};">'
    f'Arthur D. Little</span><br/>'
    f'<span style="font-size: 0.75rem; color: {COLORS["mid_grey"]};">Incentive Intelligence Platform</span>'
    f'</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# ── Group 1: RAC Capitation ──────────────────────────────────────────────────
with st.sidebar.expander("1 — RAC Capitation", expanded=True):
    base_pmpm = st.slider(
        "Base PMPM Rate (SAR)",
        min_value=PMPM_MIN, max_value=PMPM_MAX,
        value=BASE_PMPM_RATE, step=50,
        help="Monthly per-member-per-month capitation base rate",
    )

# ── Group 2: Risk Model Weights ──────────────────────────────────────────────
with st.sidebar.expander("2 — Risk Model Weights", expanded=False):
    st.caption("Disease weights")
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

# ── Group 3: Provider Performance ────────────────────────────────────────────
with st.sidebar.expander("3 — Provider Performance", expanded=False):
    perf_tabs = st.tabs(["Prov A", "Prov B", "Prov C"])
    perf_data = {}
    for i, pid in enumerate(["A", "B", "C"]):
        defaults = PERFORMANCE_BASELINES[pid]
        with perf_tabs[i]:
            dc = st.slider(
                "Diabetes Control (%)", 0, 100,
                defaults["diabetes_control_rate"], 1, key=f"dc_{pid}",
            )
            rr = st.slider(
                "30-Day Readmission (%)", 0, 30,
                defaults["readmission_rate_30day"], 1, key=f"rr_{pid}",
            )
            ps = st.slider(
                "Patient Satisfaction", 0, 100,
                defaults["patient_satisfaction_score"], 1, key=f"ps_{pid}",
            )
            ce = st.slider(
                "Cost Efficiency Ratio", 0.60, 1.30,
                defaults["cost_efficiency_ratio"], 0.01, key=f"ce_{pid}",
            )
        perf_data[pid] = {
            "diabetes_control_rate": dc,
            "readmission_rate_30day": rr,
            "patient_satisfaction_score": ps,
            "cost_efficiency_ratio": ce,
        }

# ── Group 4: Incentive Mechanisms ────────────────────────────────────────────
with st.sidebar.expander("4 — Incentive Mechanisms", expanded=False):
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
    st.caption("Shared Savings")
    cnhi_share = st.slider(
        "CNHI Share (%)", 0, 100, SAVINGS_SPLIT_CNHI, 5, key="cnhi_share",
    )
    provider_share = 100 - cnhi_share
    st.caption(f"Provider Share: {provider_share}%")

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

# ── Group 5: Quality Gates ───────────────────────────────────────────────────
with st.sidebar.expander("5 — Quality Gates", expanded=False):
    qg_diabetes = st.slider(
        "Diabetes Control (min %)", 0, 100, QUALITY_GATE_DIABETES, 5, key="qg_diab",
    )
    qg_readmission = st.slider(
        "Readmission Rate (max %)", 0, 30, QUALITY_GATE_READMISSION, 1, key="qg_readm",
    )
    qg_satisfaction = st.slider(
        "Patient Satisfaction (min)", 0, 100, QUALITY_GATE_SATISFACTION, 5, key="qg_sat",
    )


# ─── Load data ─────────────────────────────────────────────────────────────────
population = load_population()

# Calculate risk scores with current slider values
risk_scores = calculate_risk_scores(
    population,
    disease_weights=dw,
    comorbidity_terms=comorbidity_overrides,
)
population["risk_score"] = risk_scores

rac_summary = calculate_rac_payments(population, risk_scores, base_pmpm)


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
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

    All patient data is **synthetic** and generated for demonstration purposes only.
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 1: SYNTHETIC PATIENT POPULATION
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("## 1. Synthetic Patient Population")
st.markdown(
    "A synthetic cohort of **50,000 patients** distributed across three provider panels "
    "with demographics reflecting Saudi Arabia's population structure."
)

# ─── Key metrics row (always visible) ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Patients", f"{len(population):,}")
with col2:
    st.metric("Provider Panels", "3")
with col3:
    avg_age = population["age"].mean()
    st.metric("Mean Age", f"{avg_age:.1f} years")
with col4:
    avg_comorb = population["comorbidity_count"].mean()
    st.metric("Avg Comorbidities", f"{avg_comorb:.2f}")

# ─── Provider summary cards (always visible) ─────────────────────────────────
pcols = st.columns(3)
for i, (pid, profile) in enumerate(PROVIDER_PROFILES.items()):
    prov_data = population[population["provider_id"] == pid]
    rac_row = rac_summary[rac_summary["provider_id"] == pid].iloc[0]
    color = PROVIDER_COLORS[pid]

    with pcols[i]:
        st.markdown(
            f'<div style="background: {color}; '
            f'padding: 12px 16px; border-radius: 8px; margin-bottom: 12px;">'
            f'<span style="font-weight: 700; color: white; font-size: 1.1rem;">'
            f'Provider {pid}</span><br/>'
            f'<span style="color: rgba(255,255,255,0.85); font-size: 0.9rem;">'
            f'{profile["name"]}</span></div>',
            unsafe_allow_html=True,
        )
        st.metric("Patients", f"{len(prov_data):,}")
        st.metric("Avg Risk Score", f"{rac_row['avg_risk_score']:.2f}")

# ─── Expandable detail section ───────────────────────────────────────────────
with st.expander("Population Detail — Age, Disease Prevalence & Risk Profiles", expanded=False):

    st.markdown("#### Age Distribution by Provider")
    fig_age = px.histogram(
        population,
        x="age",
        color="provider_id",
        barmode="overlay",
        nbins=40,
        color_discrete_map=PROVIDER_COLORS,
        labels={"age": "Patient Age", "provider_id": "Provider", "count": "Patients"},
        opacity=0.65,
    )
    fig_age.update_layout(
        template="plotly_white",
        height=380,
        legend_title_text="Provider",
        xaxis_title="Age",
        yaxis_title="Number of Patients",
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_age, use_container_width=True)

    st.markdown("#### Chronic Disease Prevalence by Provider")
    conditions = ["has_diabetes", "has_cvd", "has_respiratory", "has_mental_health", "has_obesity"]
    condition_labels = {
        "has_diabetes": "Diabetes",
        "has_cvd": "CVD",
        "has_respiratory": "Respiratory",
        "has_mental_health": "Mental Health",
        "has_obesity": "Obesity",
    }

    prev_rows = []
    for pid in ["A", "B", "C"]:
        prov_data = population[population["provider_id"] == pid]
        for cond in conditions:
            rate = prov_data[cond].mean() * 100
            prev_rows.append({
                "Provider": f"Provider {pid}",
                "Condition": condition_labels[cond],
                "Prevalence (%)": round(rate, 1),
            })

    prev_df = pd.DataFrame(prev_rows)
    fig_prev = px.bar(
        prev_df,
        x="Condition",
        y="Prevalence (%)",
        color="Provider",
        barmode="group",
        color_discrete_map={
            "Provider A": PROVIDER_COLORS["A"],
            "Provider B": PROVIDER_COLORS["B"],
            "Provider C": PROVIDER_COLORS["C"],
        },
        text="Prevalence (%)",
    )
    fig_prev.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_prev.update_layout(
        template="plotly_white",
        height=400,
        yaxis_title="Prevalence (%)",
        xaxis_title="",
        font=dict(family="Inter, sans-serif"),
        legend_title_text="Provider",
    )
    st.plotly_chart(fig_prev, use_container_width=True)

    st.markdown("#### Risk Profile Comparison")
    table_rows = []
    for pid in ["A", "B", "C"]:
        prov_data = population[population["provider_id"] == pid]
        rac_row = rac_summary[rac_summary["provider_id"] == pid].iloc[0]
        table_rows.append({
            "Provider": provider_label(pid),
            "Panel Size": f"{int(rac_row['panel_size']):,}",
            "Mean Age": f"{prov_data['age'].mean():.1f}",
            "% Female": f"{(prov_data['sex'] == 'F').mean() * 100:.1f}%",
            "Diabetes (%)": f"{prov_data['has_diabetes'].mean() * 100:.1f}%",
            "CVD (%)": f"{prov_data['has_cvd'].mean() * 100:.1f}%",
            "Avg Comorbidities": f"{prov_data['comorbidity_count'].mean():.2f}",
            "Avg Risk Score": f"{rac_row['avg_risk_score']:.2f}",
        })

    risk_table = pd.DataFrame(table_rows)
    st.dataframe(risk_table, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 2: RAC CALCULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 2. RAC Calculation Engine")
st.markdown(
    "Risk-adjusted capitation payments derived from patient-level risk scores. "
    "Adjust the **Base PMPM Rate** and **Disease Weights** in the sidebar to see how payments shift."
)

# ─── Key financial metrics (always visible) ──────────────────────────────────
total_rac = rac_summary["total_rac_payment"].sum()
flat_per_capita = base_pmpm * 12

m2c1, m2c2, m2c3 = st.columns(3)
with m2c1:
    st.metric("Base PMPM Rate", fmt_sar(base_pmpm))
with m2c2:
    st.metric("Annual Per-Capita (flat)", fmt_sar(flat_per_capita))
with m2c3:
    st.metric("Total RAC Budget", fmt_sar(total_rac))

# ─── RAC Payment Summary Table (always visible) ─────────────────────────────
payment_rows = []
for pid in ["A", "B", "C"]:
    rac_row = rac_summary[rac_summary["provider_id"] == pid].iloc[0]
    payment_rows.append({
        "Provider": provider_label(pid),
        "Panel Size": f"{int(rac_row['panel_size']):,}",
        "Avg Risk Score": f"{rac_row['avg_risk_score']:.2f}",
        "Total RAC Payment": fmt_sar(rac_row['total_rac_payment']),
        "Per-Capita Payment": fmt_sar(rac_row['per_capita_payment']),
    })
payment_rows.append({
    "Provider": "TOTAL",
    "Panel Size": f"{int(rac_summary['panel_size'].sum()):,}",
    "Avg Risk Score": f"{risk_scores.mean():.2f}",
    "Total RAC Payment": fmt_sar(rac_summary['total_rac_payment'].sum()),
    "Per-Capita Payment": fmt_sar(rac_summary['total_rac_payment'].sum() / rac_summary['panel_size'].sum()),
})
payment_df = pd.DataFrame(payment_rows)
st.dataframe(payment_df, use_container_width=True, hide_index=True)

# ─── Expandable detail section ───────────────────────────────────────────────
with st.expander("RAC Detail — Risk Distributions, Flat vs. RAC Comparison", expanded=False):

    st.markdown("#### Risk Score Distribution by Provider")
    fig_risk = px.histogram(
        population,
        x="risk_score",
        color="provider_id",
        barmode="overlay",
        nbins=50,
        color_discrete_map=PROVIDER_COLORS,
        labels={"risk_score": "Risk Score", "provider_id": "Provider"},
        opacity=0.6,
    )
    fig_risk.update_layout(
        template="plotly_white",
        height=380,
        legend_title_text="Provider",
        xaxis_title="Patient Risk Score",
        yaxis_title="Number of Patients",
        font=dict(family="Inter, sans-serif"),
    )
    st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("#### Risk Adjustment Impact: Flat Capitation vs. RAC")
    callout_rows = []
    for pid in ["A", "B", "C"]:
        rac_row = rac_summary[rac_summary["provider_id"] == pid].iloc[0]
        flat_total = flat_per_capita * rac_row["panel_size"]
        rac_total = rac_row["total_rac_payment"]
        diff = rac_total - flat_total
        callout_rows.append({
            "Provider": provider_label(pid),
            "Flat Capitation Total": fmt_sar(flat_total),
            "RAC Total": fmt_sar(rac_total),
            "Difference": fmt_sar(diff),
            "Impact": "Underpaid without RAC" if diff > 0 else "Overpaid without RAC",
        })
    callout_df = pd.DataFrame(callout_rows)

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.dataframe(callout_df, use_container_width=True, hide_index=True)
    with col_right:
        prov_a_diff = rac_summary[rac_summary["provider_id"] == "A"].iloc[0]["total_rac_payment"] - flat_per_capita * rac_summary[rac_summary["provider_id"] == "A"].iloc[0]["panel_size"]
        prov_c_diff = rac_summary[rac_summary["provider_id"] == "C"].iloc[0]["total_rac_payment"] - flat_per_capita * rac_summary[rac_summary["provider_id"] == "C"].iloc[0]["panel_size"]

        st.markdown(
            f'<div style="background: {COLORS["navy"]}; color: white; padding: 16px; '
            f'border-radius: 8px; font-size: 0.9rem;">'
            f'<strong style="color: {COLORS["teal"]};">Key Insight</strong><br/><br/>'
            f'Under flat capitation (no risk adjustment), '
            f'<strong>Provider A</strong> would be underpaid by '
            f'<strong style="color: {COLORS["teal"]};">{fmt_sar(abs(prov_a_diff))}</strong> '
            f'annually, while '
            f'<strong>Provider C</strong> would be overpaid by '
            f'<strong style="color: {COLORS["gold"]};">{fmt_sar(abs(prov_c_diff))}</strong>.'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("#### Payment Comparison: Flat vs. Risk-Adjusted")
    comp_data = []
    for pid in ["A", "B", "C"]:
        rac_row = rac_summary[rac_summary["provider_id"] == pid].iloc[0]
        flat_total = flat_per_capita * rac_row["panel_size"]
        comp_data.append({"Provider": f"Provider {pid}", "Method": "Flat Capitation", "Total Payment (SAR)": flat_total})
        comp_data.append({"Provider": f"Provider {pid}", "Method": "Risk-Adjusted (RAC)", "Total Payment (SAR)": rac_row["total_rac_payment"]})

    comp_df = pd.DataFrame(comp_data)
    fig_comp = px.bar(
        comp_df,
        x="Provider",
        y="Total Payment (SAR)",
        color="Method",
        barmode="group",
        color_discrete_map={
            "Flat Capitation": COLORS["mid_grey"],
            "Risk-Adjusted (RAC)": COLORS["teal"],
        },
        text_auto=".3s",
    )
    fig_comp.update_layout(
        template="plotly_white",
        height=400,
        yaxis_title="Total Annual Payment (SAR)",
        xaxis_title="",
        font=dict(family="Inter, sans-serif"),
        legend_title_text="",
    )
    fig_comp.update_traces(textposition="outside")
    st.plotly_chart(fig_comp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 3: PERFORMANCE INCENTIVE SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 3. Performance Incentive Simulation")
st.markdown(
    "Four incentive mechanisms layered on top of RAC payments. "
    "Adjust **performance baselines** and **mechanism parameters** in the sidebar."
)

# Run all four mechanisms
pool_df = performance_pool(rac_summary, perf_data, withhold_pct, perf_target, perf_floor)
expectations_df = rac_adjusted_expectations(rac_summary, perf_data)
savings_df = shared_savings(
    rac_summary, perf_data,
    qg_diabetes, qg_readmission, qg_satisfaction,
    cnhi_share, provider_share,
)
tier_df = tiered_tranches(rac_summary, perf_data, tier_config)
combined_df, cnhi_net_incentives, cnhi_savings_retained = combined_summary(
    rac_summary, pool_df, savings_df, tier_df,
)

# ─── Combined summary (always visible) ───────────────────────────────────────
st.markdown("### Combined Financial Summary")

summary_rows = []
for _, row in combined_df.iterrows():
    pid = row["provider_id"]
    summary_rows.append({
        "Provider": provider_label(pid),
        "RAC Base": fmt_sar(row["rac_base"]),
        "Pool Withheld": fmt_sar(-row["pool_withheld"]),
        "Pool Earned": fmt_sar(row["pool_earned"]),
        "Savings Share": fmt_sar(row["savings_share"]),
        "Tier Bonus": fmt_sar(row["tier_bonus"]),
        "Total Payment": fmt_sar(row["total_payment"]),
        "vs. RAC Base": fmt_sar(row["vs_rac_base"]),
    })

# CNHI row
total_paid = combined_df["total_payment"].sum()
total_rac_base = combined_df["rac_base"].sum()
summary_rows.append({
    "Provider": "CNHI Total Exposure",
    "RAC Base": fmt_sar(total_rac_base),
    "Pool Withheld": "",
    "Pool Earned": "",
    "Savings Share": fmt_sar(-cnhi_savings_retained),
    "Tier Bonus": "",
    "Total Payment": fmt_sar(total_paid),
    "vs. RAC Base": fmt_sar(total_paid - total_rac_base),
})

summary_display = pd.DataFrame(summary_rows)
st.dataframe(summary_display, use_container_width=True, hide_index=True)

# Key callout metrics
kc1, kc2, kc3 = st.columns(3)
with kc1:
    st.metric("Total RAC Base", fmt_sar(total_rac_base))
with kc2:
    st.metric("Total After Incentives", fmt_sar(total_paid))
with kc3:
    delta = total_paid - total_rac_base
    st.metric("CNHI Net Exposure", fmt_sar(delta))

# ─── Expandable mechanism details ─────────────────────────────────────────────
with st.expander("Incentive Detail — Performance Pool, Expectations, Savings & Tiers", expanded=False):

  tab_pool, tab_expect, tab_savings, tab_tiers = st.tabs([
      "Performance Pool", "RAC-Adjusted Expectations",
      "Shared Savings", "Tiered Tranches",
  ])

  # ─── Tab 1: Performance Pool ───────────────────────────────────────────────
  with tab_pool:
      st.markdown("#### Mechanism 1 — Performance Pool")
      st.markdown(
          f"A **{withhold_pct:.1f}%** withhold from each provider's RAC payment, "
          f"earned back based on composite performance score (target: {perf_target}, floor: {perf_floor})."
      )

      pool_display = []
      for _, row in pool_df.iterrows():
          pid = row["provider_id"]
          pool_display.append({
              "Provider": provider_label(pid),
              "Pool Size": fmt_sar(row["pool_size"]),
              "Composite Score": f"{row['composite_score']:.1f}",
              "Earned Back (%)": f"{row['earned_back_pct']:.1f}%",
              "Earned Back": fmt_sar(row["earned_back"]),
              "Net Impact": fmt_sar(row["net_impact"]),
          })
      st.dataframe(pd.DataFrame(pool_display), use_container_width=True, hide_index=True)

      pool_chart_data = []
      for _, row in pool_df.iterrows():
          pid = row["provider_id"]
          pool_chart_data.append({"Provider": f"Provider {pid}", "Component": "Withheld", "Amount (SAR)": -row["pool_size"]})
          pool_chart_data.append({"Provider": f"Provider {pid}", "Component": "Earned Back", "Amount (SAR)": row["earned_back"]})
      fig_pool = px.bar(
          pd.DataFrame(pool_chart_data),
          x="Provider", y="Amount (SAR)", color="Component",
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
          "Providers are evaluated relative to their risk profile. "
          "Those above the regression line outperform given their population risk."
      )

      a = expectations_df["regression_intercept"].iloc[0]
      b = expectations_df["regression_slope"].iloc[0]

      fig_expect = go.Figure()

      x_range = np.linspace(
          expectations_df["avg_risk_score"].min() - 0.1,
          expectations_df["avg_risk_score"].max() + 0.1,
          50,
      )
      fig_expect.add_trace(go.Scatter(
          x=x_range, y=a + b * x_range,
          mode="lines",
          name="Expected Performance",
          line=dict(color=COLORS["mid_grey"], dash="dash", width=2),
      ))

      for _, row in expectations_df.iterrows():
          pid = row["provider_id"]
          color = PROVIDER_COLORS[pid]
          fig_expect.add_trace(go.Scatter(
              x=[row["avg_risk_score"]],
              y=[row["composite_score"]],
              mode="markers+text",
              name=f"Provider {pid}",
              marker=dict(size=18, color=color),
              text=[f"Provider {pid}"],
              textposition="top center",
              textfont=dict(size=13, color=color),
          ))

      fig_expect.update_layout(
          template="plotly_white",
          height=420,
          xaxis_title="Average Risk Score",
          yaxis_title="Composite Performance Score",
          font=dict(family="Inter, sans-serif"),
          showlegend=True,
      )
      st.plotly_chart(fig_expect, use_container_width=True)

      for _, row in expectations_df.iterrows():
          pid = row["provider_id"]
          residual = row["residual"]
          color = COLORS["teal"] if residual > 0 else COLORS["red"]
          label = "outperforms" if residual > 0 else "underperforms"
          st.markdown(
              f'<span style="color: {color}; font-weight: 600;">Provider {pid}</span> '
              f'{label} expectations by **{abs(residual):.1f}** points '
              f'(actual: {row["composite_score"]:.1f}, expected: {row["expected_score"]:.1f})',
              unsafe_allow_html=True,
          )

  # ─── Tab 3: Shared Savings ─────────────────────────────────────────────────
  with tab_savings:
      st.markdown("#### Mechanism 3 — Shared Savings with Quality Gates")
      st.markdown(
          f"Providers must pass **all three quality gates** to be eligible for savings sharing "
          f"(CNHI {cnhi_share}% / Provider {provider_share}%)."
      )

      gate_display = []
      for _, row in savings_df.iterrows():
          pid = row["provider_id"]
          gate_display.append({
              "Provider": provider_label(pid),
              "Diabetes Gate": "PASS" if row["gate_diabetes"] else "FAIL",
              "Readmission Gate": "PASS" if row["gate_readmission"] else "FAIL",
              "Satisfaction Gate": "PASS" if row["gate_satisfaction"] else "FAIL",
              "Overall": "PASS" if row["gate_passed"] else "FAIL",
              "Gross Savings": fmt_sar(row["gross_savings"]),
              "Eligible Savings": fmt_sar(row["eligible_savings"]),
              "Provider Share": fmt_sar(row["provider_share"]),
              "CNHI Share": fmt_sar(row["cnhi_share"]),
          })
      st.dataframe(pd.DataFrame(gate_display), use_container_width=True, hide_index=True)

      for _, row in savings_df.iterrows():
          pid = row["provider_id"]

          fig_wf = go.Figure(go.Waterfall(
              x=["RAC Budget", "Actual Spend", "Gross Savings",
                 "Quality Gate" if not row["gate_passed"] else "Eligible Savings",
                 "Provider Share"],
              measure=["absolute", "absolute", "relative", "relative", "absolute"],
              y=[
                  row["rac_budget"],
                  row["actual_spend"],
                  row["gross_savings"],
                  0 if row["gate_passed"] else -row["gross_savings"],
                  row["provider_share"],
              ],
              connector=dict(line=dict(color="rgba(63, 63, 63, 0.3)")),
              increasing=dict(marker=dict(color=COLORS["teal"])),
              decreasing=dict(marker=dict(color=COLORS["red"])),
              totals=dict(marker=dict(color=COLORS["gold"])),
              text=[
                  fmt_sar(row["rac_budget"]),
                  fmt_sar(row["actual_spend"]),
                  fmt_sar(row["gross_savings"]),
                  "Blocked" if not row["gate_passed"] else fmt_sar(row["eligible_savings"]),
                  fmt_sar(row["provider_share"]),
              ],
              textposition="outside",
          ))
          gate_status = "PASSED" if row["gate_passed"] else "BLOCKED"
          fig_wf.update_layout(
              template="plotly_white",
              height=320,
              title=dict(text=f"Provider {pid} — Savings Waterfall (Quality Gate: {gate_status})", font=dict(size=14)),
              font=dict(family="Inter, sans-serif"),
              showlegend=False,
          )
          st.plotly_chart(fig_wf, use_container_width=True)

  # ─── Tab 4: Tiered Tranches ────────────────────────────────────────────────
  with tab_tiers:
      st.markdown("#### Mechanism 4 — Tiered Tranches")
      st.markdown(
          "Composite performance score mapped to bonus tiers. "
          "Higher performance unlocks larger percentage bonuses."
      )

      tier_display = []
      for _, row in tier_df.iterrows():
          pid = row["provider_id"]
          tier_display.append({
              "Provider": provider_label(pid),
              "Composite Score": f"{row['composite_score']:.1f}",
              "Tier": row["tier"],
              "Payout %": f"{row['payout_pct']:.1f}%",
              "Bonus": fmt_sar(row["bonus"]),
          })
      st.dataframe(pd.DataFrame(tier_display), use_container_width=True, hide_index=True)

      tier_colors = {"No Payout": COLORS["mid_grey"], "Tier 1": "#CD7F32", "Tier 2": "#C0C0C0", "Tier 3": COLORS["gold"]}
      fig_tier = px.bar(
          tier_df,
          x=tier_df["provider_id"].apply(lambda p: f"Provider {p}"),
          y="bonus",
          color="tier",
          color_discrete_map=tier_colors,
          text=tier_df["bonus"].apply(lambda v: fmt_sar(v)),
          labels={"x": "", "bonus": "Bonus (SAR)", "tier": "Tier"},
      )
      fig_tier.update_layout(
          template="plotly_white",
          height=380,
          yaxis_title="Bonus (SAR)",
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

# ═══════════════════════════════════════════════════════════════════════════════
# MODULE 4: SCENARIO COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 4. Scenario Comparison")
st.markdown(
    "Compare pre-built scenarios against the current baseline. "
    "Each scenario adjusts performance parameters and recalculates the full pipeline."
)

scenario_name = st.selectbox(
    "Select Scenario",
    list(SCENARIOS.keys()),
    index=0,
    key="scenario_selector",
)

st.markdown(f"**{scenario_name}:** {SCENARIOS[scenario_name]['description']}")

# ─── Run scenario ────────────────────────────────────────────────────────────
sc_perf, sc_risk_mult, sc_budget_cap = apply_scenario(scenario_name, perf_data)

# If risk multiplier != 1, adjust risk scores
if sc_risk_mult != 1.0:
    sc_risk_scores = risk_scores * sc_risk_mult
    sc_rac_summary = calculate_rac_payments(population, sc_risk_scores, base_pmpm)
else:
    sc_risk_scores = risk_scores
    sc_rac_summary = rac_summary

sc_pool = performance_pool(sc_rac_summary, sc_perf, withhold_pct, perf_target, perf_floor)
sc_savings = shared_savings(
    sc_rac_summary, sc_perf,
    qg_diabetes, qg_readmission, qg_satisfaction,
    cnhi_share, provider_share,
)
sc_tiers = tiered_tranches(sc_rac_summary, sc_perf, tier_config)
sc_combined, sc_cnhi_net, sc_cnhi_sav = combined_summary(
    sc_rac_summary, sc_pool, sc_savings, sc_tiers,
)

# Apply budget cap if set
sc_total_incentives = (
    sc_combined["pool_earned"].sum() - sc_combined["pool_withheld"].sum()
    + sc_combined["savings_share"].sum()
    + sc_combined["tier_bonus"].sum()
)
cap_applied = False
cap_reduction = 1.0
if sc_budget_cap is not None and sc_total_incentives > sc_budget_cap:
    cap_applied = True
    cap_reduction = sc_budget_cap / sc_total_incentives
    sc_combined["pool_earned"] *= cap_reduction
    sc_combined["savings_share"] *= cap_reduction
    sc_combined["tier_bonus"] *= cap_reduction
    sc_combined["total_payment"] = (
        sc_combined["rac_base"]
        - sc_combined["pool_withheld"]
        + sc_combined["pool_earned"]
        + sc_combined["savings_share"]
        + sc_combined["tier_bonus"]
    )
    sc_combined["vs_rac_base"] = sc_combined["total_payment"] - sc_combined["rac_base"]

sc_total_paid = sc_combined["total_payment"].sum()
sc_total_rac_base = sc_combined["rac_base"].sum()

if cap_applied:
    st.warning(
        f"Budget cap of {fmt_sar(sc_budget_cap)} applied — "
        f"all incentives reduced by {(1 - cap_reduction) * 100:.1f}%."
    )

# ─── Key comparison metrics (always visible) ─────────────────────────────────
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

# ─── Side-by-side comparison table ───────────────────────────────────────────
compare_rows = []
for pid in ["A", "B", "C"]:
    base_row = combined_df[combined_df["provider_id"] == pid].iloc[0]
    sc_row = sc_combined[sc_combined["provider_id"] == pid].iloc[0]

    base_gate = savings_df[savings_df["provider_id"] == pid].iloc[0]["gate_passed"]
    sc_gate = sc_savings[sc_savings["provider_id"] == pid].iloc[0]["gate_passed"]

    compare_rows.append({
        "Provider": provider_label(pid),
        "Baseline Total": fmt_sar(base_row["total_payment"]),
        "Scenario Total": fmt_sar(sc_row["total_payment"]),
        "Change": fmt_sar(sc_row["total_payment"] - base_row["total_payment"]),
        "Baseline Gate": "PASS" if base_gate else "FAIL",
        "Scenario Gate": "PASS" if sc_gate else "FAIL",
    })

# Totals
compare_rows.append({
    "Provider": "CNHI Total",
    "Baseline Total": fmt_sar(total_paid),
    "Scenario Total": fmt_sar(sc_total_paid),
    "Change": fmt_sar(sc_total_paid - total_paid),
    "Baseline Gate": "",
    "Scenario Gate": "",
})

st.dataframe(pd.DataFrame(compare_rows), use_container_width=True, hide_index=True)

# ─── Expandable detail ───────────────────────────────────────────────────────
with st.expander("Scenario Detail — Full Breakdown & Sensitivity Analysis", expanded=False):

    # Per-provider scenario breakdown
    st.markdown("#### Scenario Financial Breakdown")
    sc_detail_rows = []
    for _, row in sc_combined.iterrows():
        pid = row["provider_id"]
        sc_detail_rows.append({
            "Provider": provider_label(pid),
            "RAC Base": fmt_sar(row["rac_base"]),
            "Pool Withheld": fmt_sar(-row["pool_withheld"]),
            "Pool Earned": fmt_sar(row["pool_earned"]),
            "Savings Share": fmt_sar(row["savings_share"]),
            "Tier Bonus": fmt_sar(row["tier_bonus"]),
            "Total Payment": fmt_sar(row["total_payment"]),
            "vs. RAC Base": fmt_sar(row["vs_rac_base"]),
        })
    st.dataframe(pd.DataFrame(sc_detail_rows), use_container_width=True, hide_index=True)

    # ─── Sensitivity / Tornado chart ─────────────────────────────────────────
    st.markdown("#### Sensitivity Analysis — Tornado Diagram")
    st.markdown(
        "Shows which parameters have the largest impact on CNHI total financial exposure. "
        "Each bar shows the effect of a +/- swing from the current value."
    )

    # Define parameters to test and their swing ranges
    sensitivity_params = [
        ("Base PMPM Rate", "pmpm", base_pmpm, max(PMPM_MIN, base_pmpm - 200), min(PMPM_MAX, base_pmpm + 200)),
        ("Withhold %", "withhold", withhold_pct, max(0.5, withhold_pct - 1.5), min(5.0, withhold_pct + 1.5)),
        ("Quality Gate (Diabetes)", "qg_diab", qg_diabetes, max(0, qg_diabetes - 15), min(100, qg_diabetes + 15)),
        ("Quality Gate (Readmission)", "qg_readm", qg_readmission, max(0, qg_readmission - 5), min(30, qg_readmission + 5)),
        ("Quality Gate (Satisfaction)", "qg_sat", qg_satisfaction, max(0, qg_satisfaction - 15), min(100, qg_satisfaction + 15)),
        ("CNHI Savings Share %", "cnhi_sh", cnhi_share, max(0, cnhi_share - 20), min(100, cnhi_share + 20)),
        ("Tier 2 Payout %", "tier2", tier2_pct, max(0, tier2_pct - 1.0), min(5.0, tier2_pct + 1.0)),
        ("Tier 3 Payout %", "tier3", tier3_pct, max(0, tier3_pct - 1.5), min(10.0, tier3_pct + 1.5)),
    ]

    def _calc_cnhi_total(pmpm_o, wh_o, qgd_o, qgr_o, qgs_o, cs_o, t2_o, t3_o):
        """Recalculate CNHI total using the active scenario's risk scores and performance data."""
        r_summary = calculate_rac_payments(population, sc_risk_scores, pmpm_o)
        p = performance_pool(r_summary, sc_perf, wh_o, perf_target, perf_floor)
        s = shared_savings(r_summary, sc_perf, qgd_o, qgr_o, qgs_o, cs_o, 100 - cs_o)
        tc = [(0, 49, 0.0, "No Payout"), (50, 64, tier1_pct, "Tier 1"), (65, 79, t2_o, "Tier 2"), (80, 100, t3_o, "Tier 3")]
        t = tiered_tranches(r_summary, sc_perf, tc)
        c, _, _ = combined_summary(r_summary, p, s, t)
        return c["total_payment"].sum()

    baseline_total = sc_total_paid
    tornado_data = []

    for label, key, current, lo, hi in sensitivity_params:
        args_lo = [base_pmpm, withhold_pct, qg_diabetes, qg_readmission, qg_satisfaction, cnhi_share, tier2_pct, tier3_pct]
        args_hi = list(args_lo)

        idx_map = {"pmpm": 0, "withhold": 1, "qg_diab": 2, "qg_readm": 3, "qg_sat": 4, "cnhi_sh": 5, "tier2": 6, "tier3": 7}
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
        y=tornado_df["Parameter"],
        x=tornado_df["Low"],
        orientation="h",
        name="Low Swing",
        marker_color=COLORS["teal"],
        text=tornado_df["Low"].apply(lambda v: fmt_sar(v)),
        textposition="auto",
    ))
    fig_tornado.add_trace(go.Bar(
        y=tornado_df["Parameter"],
        x=tornado_df["High"],
        orientation="h",
        name="High Swing",
        marker_color=COLORS["red"],
        text=tornado_df["High"].apply(lambda v: fmt_sar(v)),
        textposition="auto",
    ))
    fig_tornado.update_layout(
        template="plotly_white",
        height=400,
        barmode="overlay",
        xaxis_title="Change in CNHI Total Exposure (SAR)",
        yaxis_title="",
        font=dict(family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_tornado, use_container_width=True)

st.markdown("---")
st.markdown(
    f'<p style="text-align: center; color: {COLORS["mid_grey"]}; font-size: 0.8rem;">'
    f'CNHI Incentive Intelligence Platform — Arthur D. Little POC</p>',
    unsafe_allow_html=True,
)
