"""
CNHI Incentive Intelligence Platform — Documentation Page
Drop this file into your Streamlit app as a page or import into app.py.

Usage Option 1 — Multi-page app:
  Place as pages/1_Documentation.py (rename app.py to pages/2_Platform.py)

Usage Option 2 — Tab within app.py:
  In app.py, add:
    tab_docs, tab_platform = st.tabs(["📖 Documentation", "🏥 Platform"])
    with tab_docs:
        from docs_page import render_docs
        render_docs()
    with tab_platform:
        # ... existing app code ...
"""

import streamlit as st


def render_docs():
    """Render the full documentation page with collapsible sections."""

    # ─── Colour constants (match main app) ─────────────────────────────────
    NAVY = "#0A1628"
    TEAL = "#2EC4B6"
    GOLD = "#C9A84C"
    RED = "#E63946"
    AMBER = "#F4A261"
    MID_GREY = "#6C757D"
    LIGHT_BG = "#F8F9FA"

    # ─── Custom CSS ────────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
        /* Documentation page styles */
        .doc-header {{
            background: linear-gradient(135deg, {NAVY} 0%, #1a2d4a 100%);
            padding: 28px 36px;
            border-radius: 12px;
            margin-bottom: 28px;
        }}
        .doc-header h1 {{
            color: white !important;
            margin: 0 !important;
            border: none !important;
            font-size: 1.7rem !important;
        }}
        .doc-header p {{
            color: {TEAL};
            margin: 6px 0 0 0;
            font-size: 1rem;
        }}
        .doc-callout {{
            padding: 16px 20px;
            border-radius: 8px;
            margin: 12px 0 16px 0;
            font-size: 0.92rem;
            line-height: 1.5;
        }}
        .doc-callout-gold {{
            background: #FFF8E7;
            border-left: 4px solid {GOLD};
            color: #5D4E37;
        }}
        .doc-callout-teal {{
            background: #F0FDFA;
            border-left: 4px solid {TEAL};
            color: #1A4A44;
        }}
        .doc-callout-red {{
            background: #FDF0F0;
            border-left: 4px solid {RED};
            color: #8B1A1A;
        }}
        .doc-callout-amber {{
            background: #FFF5EB;
            border-left: 4px solid {AMBER};
            color: #6B4226;
        }}
        .part-label {{
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 4px;
            margin-bottom: 4px;
        }}
        .track-box {{
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 8px;
        }}
        .track-teal {{
            background: #F0FDFA;
            border: 2px solid {TEAL};
        }}
        .track-amber {{
            background: #FFF5EB;
            border: 2px solid {AMBER};
        }}
        .feature-tag {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 6px;
        }}
        .tag-new {{
            background: {TEAL};
            color: white;
        }}
        .tag-updated {{
            background: {GOLD};
            color: white;
        }}
        .version-badge {{
            background: {NAVY};
            color: {TEAL};
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        /* Make expander headers more prominent */
        .streamlit-expanderHeader {{
            font-size: 1.05rem !important;
            font-weight: 600 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div class="doc-header">
        <h1>📖 User Guide & Technical Reference</h1>
        <p>CNHI Incentive Intelligence Platform — POC v3.0</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "A comprehensive guide in three parts: **feature summary** with rules and assumptions, "
        "**step-by-step usage instructions**, and **what's new** in the latest version."
    )

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # PART A: FEATURE SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f'<p class="part-label" style="color: {TEAL};">PART A</p>', unsafe_allow_html=True)
    st.markdown("## Feature Summary — Rules, Assumptions & Logic")

    # ─── A1 ────────────────────────────────────────────────────────────────
    with st.expander("A1. What This Application Is", expanded=True):
        st.markdown("""
        A **proof-of-concept demonstration tool** that simulates how a national performance-based
        financial incentive model operates on top of Risk-Adjusted Capitation (RAC) payments for
        Saudi Arabia's public health clusters. It uses synthetic data, runs actual calculations,
        and produces interactive scenario-based financial outputs.
        """)
        st.markdown("""
        <div class="doc-callout doc-callout-gold">
            <strong>Think of it as a financial flight simulator for health insurance policy.</strong>
            You can test different incentive configurations without any real-world consequences.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        **Two things make it more than a slideshow:**
        - **It calculates, not just displays.** Every number on screen comes from actual calculations
          running on 50,000 synthetic patient records. Change a parameter and every number updates instantly.
        - **It simulates "what if" scenarios.** You can test questions like "What if we set the performance
          bonus at 3%?" or "What if a cluster cuts costs by reducing quality?" and see the financial
          consequences immediately.
        """)

    # ─── A2 ────────────────────────────────────────────────────────────────
    with st.expander("A2. The Five Modules"):
        st.markdown("""
        | Module | What It Does | What It Proves |
        |--------|-------------|----------------|
        | **1. Population** | Generates 50,000 synthetic patients across three named health clusters with Saudi demographics, ICD-10 codes, and comorbidity cascades. | We can create realistic test data without confidential CNHI records. |
        | **2. RAC Engine** | Calculates risk scores per patient (HCC-style) and risk-adjusted capitation payments per cluster. Normalised to population mean = 1.0. | Higher-risk populations receive proportionally higher payment. Risk adjustment makes funding fair. |
        | **3. Incentives** | Runs four incentive mechanisms simultaneously. Assigns clusters to Performance Rewards or Capability Investment track. League table ranking. | Incentives drive quality improvement, not just cost control. Gaming detected. Underperformers invested in, not penalised. |
        | **4. Scenarios** | Five pre-built scenarios with side-by-side comparison and tornado sensitivity analysis (8+ parameters). | CNHI can stress-test before implementation. Budget exposure is quantifiable. |
        | **5. Year 2** | Projects how Year 1 efficiency improvements reduce Year 2 RAC budgets. ROI and break-even analysis. | The programme is an investment with measurable return, not just a cost. |
        """)

    # ─── A3 ────────────────────────────────────────────────────────────────
    with st.expander("A3. The Three Health Clusters"):
        st.markdown("""
        The POC simulates three public health clusters with deliberately different profiles:

        | | **Cluster A** | **Cluster B** | **Cluster C** |
        |---|---|---|---|
        | **Name** | Riyadh First Health Cluster | Eastern Health Cluster | Madinah Health Cluster |
        | **Type** | Public | Public | Public |
        | **Population** | ~20,000 patients | ~18,000 patients | ~12,000 patients |
        | **Profile** | Older, higher acuity, more chronic disease | Balanced, representative mix | Younger, healthier, lower NCD burden |
        | **Disease Multiplier** | 1.55× (elevated rates) | 0.95× (near average) | 0.50× (reduced rates) |
        | **Target Risk Score** | ~1.35 | ~1.00 | ~0.72 |
        | **Data Strength** | Strong (government systems) | Moderate | Weaker (smaller, private-origin) |
        """)

    # ─── A4 ────────────────────────────────────────────────────────────────
    with st.expander("A4. KPI Framework — Four Categories, 20 KPIs"):
        st.markdown("""
        Performance is measured across four incentive categories. Category weights are adjustable
        and must sum to 100%. Individual KPIs can be toggled on/off to simulate wave configurations.

        | Category | Default Weight | Wave 1 Active KPIs | Dormant (Future Waves) |
        |----------|:---:|---|---|
        | **Clinical Outcomes** | 35% | Diabetes HbA1c control, Hypertension control, 30-day readmission, Preventable hospitalisations | Cancer screening, Maternal mortality, Childhood immunisation |
        | **Efficiency Improvement** | 30% | Avg LOS vs expected, Cost efficiency ratio, Hospital-to-primary-care shift, Generic prescribing | Theatre utilisation, Outpatient follow-up ratio |
        | **Data Quality** | 20% | ICD-10 coding accuracy, Claims completeness, Timely data submission | Duplicate record rate |
        | **Data Reporting** | 15% | Mandatory report compliance, Dashboard adoption | Population health register completeness |
        """)
        st.markdown("""
        <div class="doc-callout doc-callout-teal">
            <strong>Wave simulation:</strong> Toggle any dormant KPI to active and adjust its weight
            to see how it would affect cluster scores and incentive payouts if included in a future wave.
        </div>
        """, unsafe_allow_html=True)

    # ─── A5 ────────────────────────────────────────────────────────────────
    with st.expander("A5. Risk Adjustment Model — Rules & Logic"):
        st.markdown("""
        Each patient receives a risk score reflecting expected healthcare cost. The model follows a
        simplified HCC (Hierarchical Condition Category) approach:

        1. **Step 1 — Base score of 1.0.** Every patient starts at the population average.
        2. **Step 2 — Age-sex adjustment.** Older patients score higher (+0.55 for males 60-74,
           +1.00 for females 75+). Younger patients score lower (-0.30 for males 0-14). All configurable.
        3. **Step 3 — Chronic disease weights.** Diabetes +0.35, CVD +0.45, Respiratory +0.20,
           Mental Health +0.15, Obesity +0.10. All configurable.
        4. **Step 4 — Comorbidity interaction.** 2 conditions: +0.10 extra. 3+ conditions: +0.25 extra.
        5. **Step 5 — Normalisation.** All scores normalised so population mean = 1.0.
           A score of 1.35 means 35% more expensive than average. Standard CMS practice.

        **RAC Payment Formula:**
        `Annual Payment = Base PMPM × Patient Risk Score × 12 months`
        summed across all patients in each cluster.
        """)
        st.markdown("""
        <div class="doc-callout doc-callout-red">
            <strong>Important:</strong> These weights are simplified for demonstration. In the full
            engagement, a qualified health economist would calibrate against actual CNHI claims data.
        </div>
        """, unsafe_allow_html=True)

    # ─── A6 ────────────────────────────────────────────────────────────────
    with st.expander("A6. Four Incentive Mechanisms"):
        st.markdown("#### Mechanism 1: Performance Pool")
        st.markdown("""
        A percentage (default 2%) of each cluster's RAC payment is withheld. The cluster's KPIs
        are combined into a composite score. Score ≥ target (70): earn back 100%. Between floor (50)
        and target: proportional return. Below floor: earn back 0%. Only applies to Performance
        Rewards track clusters.
        """)

        st.markdown("#### Mechanism 2: RAC-Adjusted Expectations")
        st.markdown("""
        Each cluster is judged against what would be *expected given its population risk*. A regression
        line is calculated from all clusters' risk scores and performance scores. Clusters above the
        line outperform; below underperform — regardless of absolute numbers. Prevents penalising
        clusters serving sicker populations.
        """)

        st.markdown("#### Mechanism 3: Shared Savings with Quality Gates")
        st.markdown("""
        If a cluster spends less than its RAC budget (cost efficiency ratio < 1.0), the difference
        is "gross savings." But the cluster must pass **ALL THREE quality gates**: minimum diabetes
        control (≥65%), maximum readmission (≤15%), and minimum composite score (≥55). Only then
        are savings split between CNHI and the cluster. Savings from service cuts without quality
        are **blocked**.
        """)

        st.markdown("#### Mechanism 4: Tiered Performance Tranches")
        st.markdown("""
        | Score Range | Tier | Payout |
        |:---:|---|:---:|
        | Below 50 | No Payout | 0% of RAC |
        | 50–64 | Tier 1 | 0.5% of RAC |
        | 65–79 | Tier 2 | 1.5% of RAC |
        | 80+ | Tier 3 | 3.0% of RAC |

        Creates a continuous improvement gradient — no cliff edges. All thresholds and payouts adjustable.
        """)

    # ─── A7 ────────────────────────────────────────────────────────────────
    with st.expander("A7. Dual-Track System — Rewards vs. Capability Investment"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="track-box track-teal">
                <strong style="color: {TEAL};">PERFORMANCE REWARDS TRACK</strong><br/>
                <span style="font-size: 0.9rem;">Composite score ≥ capability threshold</span>
                <hr style="margin: 8px 0; border-color: {TEAL}40;"/>
                <ul style="font-size: 0.88rem; margin: 0; padding-left: 18px;">
                    <li>All four incentive mechanisms apply</li>
                    <li>Earn: pool return + savings share + tier bonus</li>
                    <li><em>Financial rewards flow to performers</em></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="track-box track-amber">
                <strong style="color: {AMBER};">CAPABILITY INVESTMENT TRACK</strong><br/>
                <span style="font-size: 0.9rem;">Composite score &lt; capability threshold</span>
                <hr style="margin: 8px 0; border-color: {AMBER}40;"/>
                <ul style="font-size: 0.88rem; margin: 0; padding-left: 18px;">
                    <li>No pool withhold, no savings, no tier bonus</li>
                    <li>CNHI allocates capability investment</li>
                    <li><em>Investment flows to those who need support</em></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("""
        <div class="doc-callout doc-callout-gold">
            <strong>This model doesn't punish failure — it invests in improvement.</strong>
            Financial rewards flow to those who perform. Capability investment flows to those
            who need support. Both are funded from the same national incentive budget.
        </div>
        """, unsafe_allow_html=True)

    # ─── A8 ────────────────────────────────────────────────────────────────
    with st.expander("A8. Composite Score Calculation"):
        st.markdown("""
        Each KPI is normalised to a 0–100 scale where **higher is always better**:
        - "Higher is better" KPIs (e.g., diabetes control): used directly
        - "Lower is better" KPIs (e.g., readmission): `Score = (max – value) / (max – min) × 100`

        Active KPIs within each category are averaged → category score.
        Category scores × category weights → **composite score** (0–100).
        """)

    # ─── A9 ────────────────────────────────────────────────────────────────
    with st.expander("A9. Five Pre-Built Scenarios"):
        st.markdown("""
        | Scenario | What It Tests | Watch For |
        |----------|--------------|-----------|
        | **Baseline** | Default parameters. Reference point. | Metrics match sidebar. |
        | **All Clusters Improve** | KPIs improve 10–15%. Fiscal exposure test. | CNHI total increases. Acceptable? |
        | **Gaming Detection** | One cluster slashes costs, quality drops. | Quality gate → FAIL. Savings blocked. |
        | **Population Risk Increase** | All populations 15% sicker. | RAC payments up. Performance may drop. |
        | **Budget Cap** | Programme cost capped at SAR 5M. | Warning banner. Proportional reduction. |

        **Tornado Sensitivity Diagram** tests 8+ parameters. Longest bars = most impactful parameters
        for CNHI to get right.
        """)

    # ─── A10 ───────────────────────────────────────────────────────────────
    with st.expander("A10. Year 2 Projection Logic"):
        st.markdown("""
        If incentives drive better efficiency in Year 1, utilisation drops → RAC budget reduces in Year 2.

        - **Elasticity Factor** (default 0.5): proportion of Year 1 gains carrying through.
          At 0.5, a 10% efficiency improvement reduces next year's RAC by 5%.
        - `Year 2 RAC = Year 1 RAC × (1 – avg efficiency gain × elasticity)`
        - `ROI = Year 2 RAC savings / Year 1 programme cost`
        """)

    # ─── A11 ───────────────────────────────────────────────────────────────
    with st.expander("A11. What This POC Can and Cannot Do"):
        col_can, col_cannot = st.columns(2)
        with col_can:
            st.markdown(f"**<span style='color: {TEAL};'>✓ CAN DO</span>**", unsafe_allow_html=True)
            for item in [
                "Generate 50K synthetic patients with Saudi demographics & ICD-10 codes",
                "Calculate risk-adjusted capitation responding to parameter changes in real time",
                "Run four incentive mechanisms simultaneously with dual-track assignment",
                "Detect gaming through quality gates and block ineligible savings",
                "Rank clusters in a league table for transparency",
                "Compare five scenarios with tornado sensitivity analysis",
                "Project Year 2 RAC reduction and programme ROI",
                "Assign underperformers to capability investment (no penalties)",
                "Apply budget caps with proportional reduction",
                "Run in any browser, no installation",
            ]:
                st.markdown(f"- {item}")

        with col_cannot:
            st.markdown(f"**<span style='color: {RED};'>✗ CANNOT DO</span>**", unsafe_allow_html=True)
            for item in [
                "Connect to real CNHI data or any live system",
                "Produce actuarially certified risk scores",
                "Replace detailed health economics modelling",
                "Predict actual cluster behaviour (values are user-set)",
                "Determine payouts based on ranking (payouts are independent)",
                "Model all 20+ clusters nationally",
                "Guarantee projections match actual outcomes",
                "Model specific non-financial intervention impacts",
                "Operate in Arabic",
                "Export reports as PDF/Excel (planned)",
            ]:
                st.markdown(f"- {item}")

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # PART B: HOW TO USE
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f'<p class="part-label" style="color: {GOLD};">PART B</p>', unsafe_allow_html=True)
    st.markdown("## How to Use the Application")

    # ─── B1 ────────────────────────────────────────────────────────────────
    with st.expander("B1. Opening the Application", expanded=True):
        st.markdown("""
        Open the URL in any modern browser (Chrome, Edge, Safari). The app loads with default
        parameters and displays all five modules. No login required. Synthetic population generates
        automatically (2–3 seconds).
        """)

    # ─── B2 ────────────────────────────────────────────────────────────────
    with st.expander("B2. Screen Layout"):
        st.markdown("""
        - **Left sidebar — Control panel.** Seven collapsible groups of sliders. Changes cascade
          instantly. No "refresh" button.
        - **Main area — Results.** Five numbered modules top-to-bottom. Key metrics always visible.
          Details inside expandable sections.
        """)
        st.markdown("""
        <div class="doc-callout doc-callout-teal">
            <strong>Design principle:</strong> Lead with the punchline. The most important numbers
            are always visible. Details are one click away.
        </div>
        """, unsafe_allow_html=True)

    # ─── B3 ────────────────────────────────────────────────────────────────
    with st.expander("B3. The Seven Sidebar Groups"):
        st.markdown("""
        | Group | Name | What It Controls |
        |:---:|------|-----------------|
        | **1** | RAC Capitation | Base PMPM rate (SAR 500–2,000). Scales all payments. |
        | **2** | Category Weights | Four category weight sliders. Must sum to 100%. |
        | **3** | KPI Configuration | Toggle KPIs on/off per category. Simulates wave configs. |
        | **4** | Cluster Performance | Per-cluster KPI sliders (Riyadh 1st / Eastern / Madinah). |
        | **5** | Incentive Mechanisms | Withhold %, target/floor, savings split, tier payouts, capability threshold. |
        | **6** | Quality Gates | Three thresholds: diabetes min, readmission max, composite min. |
        | **7** | Year 2 Projection | Elasticity factor (0.0–1.0). |
        """)

    # ─── B4 ────────────────────────────────────────────────────────────────
    with st.expander("B4. What's Visible vs. Expandable"):
        st.markdown("""
        | Module | Always Visible | Inside Expander |
        |--------|---------------|-----------------|
        | **1. Population** | Patient count, cluster cards with risk scores | Age histogram, disease charts, risk profile table |
        | **2. RAC Engine** | PMPM, total budget, payment summary table | Risk distributions, flat vs. RAC comparison |
        | **3. Incentives** | Combined summary, track assignment, CNHI exposure | Pool, Expectations, Savings, Tranches, League Table tabs |
        | **4. Scenarios** | Scenario selector, comparison metrics & table | Full breakdown, tornado diagram |
        | **5. Year 2** | Programme cost, RAC reduction, ROI callout | Sensitivity chart (elasticity vs. net position) |
        """)

    # ─── B5 ────────────────────────────────────────────────────────────────
    with st.expander("B5. 15-Minute Demo Walkthrough"):
        st.markdown("""
        1. **Minutes 1–2 — Population.** Show cluster cards. "Riyadh First: 20K sicker patients,
           risk ~1.35. Madinah: 12K healthier, risk ~0.72." Expand for charts.

        2. **Minutes 3–5 — RAC Payments.** Payment summary table. Move PMPM slider live.
           Expand for flat vs. RAC comparison. *"Risk adjustment makes payments fair."*

        3. **Minutes 6–8 — Combined Summary.** The punchline: combined financial summary with
           track assignment. Show programme cost breakdown.

        4. **Minutes 8–11 — Mechanism Deep-Dive.** Expand detail. RAC-Adjusted Expectations
           scatter plot (most compelling). Shared Savings waterfall. League Table.
           *"Rewards improvement, catches gaming, invests in underperformers."*

        5. **Minutes 11–13 — Scenarios.** "Gaming Detection" → quality gate FAIL. "All Improve"
           → fiscal exposure. Tornado diagram. *"Stress-test before implementation."*

        6. **Minutes 13–15 — Year 2 & Close.** ROI callout. Adjust elasticity. Break-even chart.
           *"Not just a cost — an investment with measurable return. Formulas, not just frameworks."*
        """)

    # ─── B6 ────────────────────────────────────────────────────────────────
    with st.expander("B6. Quick Reference — Common Tasks"):
        st.markdown("""
        | I Want To... | Do This |
        |-------------|---------|
        | See how much each cluster gets paid | Module 2 payment summary (always visible) |
        | Change the base payment rate | Sidebar → Group 1 → PMPM slider |
        | Test a cluster improving | Sidebar → Group 4 → cluster tab → adjust KPI sliders |
        | Simulate Wave 2 KPI mix | Sidebar → Group 3 → toggle dormant KPIs on |
        | Check if quality gates catch gaming | Group 4 → lower quality metrics → Shared Savings tab |
        | Compare baseline vs. scenario | Module 4 → scenario dropdown |
        | Find most impactful parameters | Module 4 → expand → tornado diagram |
        | See programme ROI | Module 5 → ROI callout |
        | Set maximum CNHI budget | Module 4 → Budget Cap scenario |
        | See cluster rankings | Module 3 → expand → League Table tab |
        """)

    st.markdown("---")

    # ═══════════════════════════════════════════════════════════════════════
    # PART C: WHAT'S NEW
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown(f'<p class="part-label" style="color: {AMBER};">PART C</p>', unsafe_allow_html=True)
    st.markdown("## What's New in v2.1")
    st.markdown("Features added based on CNHI stakeholder feedback and internal ADL review.")

    # ─── New features ──────────────────────────────────────────────────────
    with st.expander("New & Updated Features", expanded=True):
        features = [
            ("Cluster Model", "NEW", "tag-new",
             "Entire application migrated from 'provider' to 'cluster' terminology. Three named Saudi health clusters. All public sector.",
             "Incentive model targets clusters (ACO-style networks), not individual hospitals."),
            ("KPI Framework", "NEW", "tag-new",
             "Disease-level metrics replaced with four incentive categories containing 20 KPIs. Toggle on/off with adjustable weights.",
             "CNHI feedback: incentivisation at category level, not disease level."),
            ("Dual-Track System", "NEW", "tag-new",
             "Clusters below capability threshold receive training and support investment instead of penalties.",
             "Penalising public clusters penalises patients. NHS star rating failure is the cautionary precedent."),
            ("League Table", "NEW", "tag-new",
             "Ranked cluster view with composite and category scores. Colour-coded by track.",
             "Transparency and benchmarking without rankings determining payouts."),
            ("Year 2 Projection", "NEW", "tag-new",
             "Module 5: Year 1 efficiency → Year 2 RAC reduction. ROI and break-even analysis.",
             "Value case: better performance today = lower costs tomorrow."),
            ("Expanded Sidebar", "UPDATED", "tag-updated",
             "Seven groups (up from five). New groups for Category Weights, KPI Configuration, Year 2.",
             "More granular control without cluttering the display."),
            ("Budget Cap", "UPDATED", "tag-updated",
             "Cap now applies to total programme cost (incentives + capability investment).",
             "Fiscal exposure controlled across both tracks."),
            ("Quality Gates", "UPDATED", "tag-updated",
             "Third gate changed from patient satisfaction to composite score (≥55).",
             "More robust anti-gaming safeguard across all KPIs."),
        ]

        for name, tag_text, tag_class, what, why in features:
            st.markdown(
                f'<span class="feature-tag {tag_class}">{tag_text}</span> '
                f'**{name}**',
                unsafe_allow_html=True,
            )
            st.markdown(f"> {what}")
            st.markdown(f"*Why: {why}*")
            st.markdown("")

    # ─── Platform Evolution Roadmap ──────────────────────────────────────
    with st.expander("Platform Evolution — Lite-Weight POC → Scaled POC → Production", expanded=True):
        st.markdown(f"""
        <div class="doc-callout doc-callout-gold">
            <strong>Three-stage evolution.</strong> This application is the Lite-Weight POC — a proof of concept
            built to demonstrate feasibility. The Scaled POC extends this into a working tool using CNHI's
            actual RAC engine and real cluster data. The Production version is the fully operational
            Incentive Intelligence Platform deployed at national scale.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        | Component | **Lite-Weight POC** *(this version)* | **Scaled POC** *(design project)* | **Production Version** |
        |-----------|:---:|:---:|:---:|
        | **RAC Engine** | Simplified HCC-style model built in-house with user-adjustable weights | Integration with **CNHI's Milliman-built RAC engine** — actual risk scores and capitation calculations | Full Milliman RAC engine with actuarially certified weights, prospective and concurrent risk adjustment |
        | **Patient Data** | 50,000 synthetic records, seed-reproducible | CNHI's actual Wave 1 cluster population data (anonymised or shadow-mode) | Full national population data across all clusters via NPHIES |
        | **Clusters** | 3 named public clusters with simulated risk profiles | Wave 1 cluster set (3–5 clusters) with real demographic and utilisation profiles | All 20+ clusters nationally, public and private tracks |
        | **KPIs** | 20 KPIs across 4 categories, 10 active, user-set values | KPIs populated from real cluster performance data where available; validated against CNHI Health Outcomes Framework | Full ICHOM-aligned clinical outcome measures with automated data feeds from cluster systems |
        | **Performance Data** | User-set via sidebar sliders (simulated) | Historical cluster performance data ingested from CNHI systems; remaining gaps filled with calibrated estimates | Real-time performance data feeds from cluster EHRs, claims systems, and NPHIES |
        | **Incentive Mechanisms** | 4 mechanisms with configurable parameters, dual-track system | Same 4 mechanisms validated against Milliman RAC outputs; incentive formulas stress-tested with real financial data; governance rules codified | Formally specified, legally reviewed incentive calculations with automated payout processing |
        | **Quality Gates** | 3 configurable gates (diabetes, readmission, composite) | Gates aligned to CNHI's Health Assurance Framework; thresholds validated with clinical advisory input | Automated gate evaluation from live data with exception handling and dispute resolution workflow |
        | **Dual-Track System** | Performance Rewards vs. Capability Investment based on composite threshold | Track assignment validated with real cluster profiles; capability investment packages costed against actual training/support programmes | Operational dual-track with procurement integration for capability investment delivery |
        | **League Table** | 3-cluster ranking (reporting only) | Wave 1 cluster ranking with real scores; benchmarking against national and international comparators | National league table with quarterly publication cycle; integrated with CNHI's cluster performance reporting |
        | **Scenarios** | 5 pre-built + tornado sensitivity (8 parameters) | Scenario library expanded to 10+; Monte Carlo simulation with 1,000+ runs; scenarios calibrated against Milliman actuarial assumptions | Unlimited scenario modelling with full Monte Carlo; automated sensitivity analysis; scenario audit trail |
        | **Year 2 Projection** | Simplified two-year view with single elasticity slider | Multi-year projection (3–5 years) using Milliman's actuarial trend assumptions; RAC recalibration cycle modelled | Rolling multi-year projections with annual RAC recalibration; integrated with CNHI's budget planning cycle |
        | **Private Sector** | Not included (public cluster model only) | Accreditation-based tariff multiplier module (CBAHI / JCI / HIMSS Level 7) with performance overlay for private providers | Full private provider incentive track with accreditation, performance, and contract management |
        | **Data Integration** | No external integration (self-contained) | API connections to CNHI data sources; FHIR/HL7 compatibility; Milliman RAC engine integration via data exchange | Full NPHIES integration; real-time data feeds; automated ETL pipelines; data quality monitoring |
        | **Security & Governance** | Demo environment, no authentication | Role-based access; data anonymisation protocols; NCA cybersecurity compliance assessment | Full NCA compliance; audit logging; data sovereignty; CNHI security architecture integration |
        | **Language** | English only | English with Arabic labels for key outputs | Full bilingual Arabic/English interface |
        | **Export & Reporting** | Screen-based only | PDF scenario reports; Excel data exports; presentation-ready chart exports | Automated reporting suite; scheduled dashboards; integration with CNHI's Health Economics Unit reporting |
        | **Platform** | Streamlit demo application | Hardened Streamlit or migration to production web framework; hosted in CNHI-approved environment | Production-grade Incentive Intelligence Platform with SLA, monitoring, and operational support |
        """)

        st.markdown(f"""
        <div class="doc-callout doc-callout-teal">
            <strong>Key transition: Milliman RAC integration.</strong> Both the Scaled POC and Production
            versions connect to CNHI's Milliman-built RAC engine rather than running a separate risk
            model. This means the incentive calculations operate on the same actuarially certified risk
            scores that determine capitation payments — ensuring the incentive layer is perfectly
            calibrated to the payment foundation it sits on.
        </div>
        """, unsafe_allow_html=True)

    # ─── Footer ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'<p style="text-align: center; color: {MID_GREY}; font-size: 0.8rem;">'
        f'CNHI Incentive Intelligence Platform — Arthur D. Little — Confidential<br/>'
        f'Questions? Contact Janahan Tharmaratnam, Partner.</p>',
        unsafe_allow_html=True,
    )


# ─── Standalone execution ─────────────────────────────────────────────────────
if __name__ == "__main__":
    st.set_page_config(
        page_title="CNHI Platform — Documentation",
        page_icon="📖",
        layout="wide",
    )
    render_docs()
