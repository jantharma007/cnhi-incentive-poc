"""Default parameter values for the CNHI Incentive Intelligence Platform."""

RANDOM_SEED = 42
TOTAL_PATIENTS = 50_000

# RAC Engine defaults
BASE_PMPM_RATE = 850  # SAR
PMPM_MIN = 500
PMPM_MAX = 2000

# Age-Sex risk adjustment table
# Keys: (sex, age_band) -> adjustment
AGE_SEX_ADJUSTMENTS = {
    ("M", "0-14"):  -0.30,
    ("M", "15-29"): -0.20,
    ("M", "30-44"):  0.00,
    ("M", "45-59"):  0.25,
    ("M", "60-74"):  0.55,
    ("M", "75+"):    0.90,
    ("F", "0-14"):  -0.35,
    ("F", "15-29"): -0.15,
    ("F", "30-44"):  0.05,
    ("F", "45-59"):  0.30,
    ("F", "60-74"):  0.60,
    ("F", "75+"):    1.00,
}

# Chronic disease risk weights (for RAC payment calculation — separate from KPI weights)
DISEASE_WEIGHTS = {
    "diabetes":      0.35,
    "cvd":           0.45,
    "respiratory":   0.20,
    "mental_health": 0.15,
    "obesity":       0.10,
}

# Comorbidity interaction terms
COMORBIDITY_TERMS = {
    2: 0.10,
    3: 0.25,  # 3 or more
}

# ─── KPI Framework ──────────────────────────────────────────────────────────
# Four incentive domains — incentive mechanisms operate on category-level scores

KPI_CATEGORIES = {
    "clinical_outcomes": {
        "label": "Clinical Outcomes",
        "default_weight": 35,
        "kpis": {
            "diabetes_hba1c_control": {
                "label": "Diabetes HbA1c Control Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "hypertension_control": {
                "label": "Hypertension Control Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "readmission_30day": {
                "label": "30-Day Readmission Rate (%)",
                "direction": "lower_better",
                "min": 0, "max": 30,
                "wave_1_active": True,
            },
            "preventable_hospitalisations": {
                "label": "Preventable Hospitalisations per 1,000",
                "direction": "lower_better",
                "min": 0, "max": 50,
                "wave_1_active": True,
            },
            "cancer_screening_rate": {
                "label": "Cancer Screening Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": False,
            },
            "maternal_mortality_rate": {
                "label": "Maternal Mortality Rate per 100K",
                "direction": "lower_better",
                "min": 0, "max": 50,
                "wave_1_active": False,
            },
            "childhood_immunisation": {
                "label": "Childhood Immunisation Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": False,
            },
        },
    },
    "efficiency_improvement": {
        "label": "Efficiency Improvement",
        "default_weight": 30,
        "kpis": {
            "avg_length_of_stay": {
                "label": "Avg Length of Stay vs Expected (ratio)",
                "direction": "lower_better",
                "min": 0.5, "max": 2.0,
                "wave_1_active": True,
            },
            "cost_efficiency_ratio": {
                "label": "Cost Efficiency Ratio (actual/budget)",
                "direction": "lower_better",
                "min": 0.6, "max": 1.3,
                "wave_1_active": True,
            },
            "hospital_to_primary_care_shift": {
                "label": "Hospital to Primary Care Shift (%)",
                "direction": "higher_better",
                "min": 0, "max": 50,
                "wave_1_active": True,
            },
            "generic_prescribing_rate": {
                "label": "Generic Prescribing Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "theatre_utilisation": {
                "label": "Theatre Utilisation Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": False,
            },
            "outpatient_followup_new_ratio": {
                "label": "Outpatient Follow-up to New Ratio",
                "direction": "lower_better",
                "min": 0.5, "max": 5.0,
                "wave_1_active": False,
            },
        },
    },
    "data_quality": {
        "label": "Data Quality",
        "default_weight": 20,
        "kpis": {
            "icd10_coding_accuracy": {
                "label": "ICD-10 Coding Accuracy (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "claims_submission_completeness": {
                "label": "Claims Submission Completeness (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "timely_data_submission": {
                "label": "Timely Data Submission (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "duplicate_record_rate": {
                "label": "Duplicate Record Rate (%)",
                "direction": "lower_better",
                "min": 0, "max": 20,
                "wave_1_active": False,
            },
        },
    },
    "data_reporting": {
        "label": "Data Reporting",
        "default_weight": 15,
        "kpis": {
            "mandatory_report_compliance": {
                "label": "Mandatory Report Submission Compliance (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "dashboard_adoption": {
                "label": "KPI Dashboard Adoption Rate (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": True,
            },
            "population_health_register": {
                "label": "Population Health Register Completeness (%)",
                "direction": "higher_better",
                "min": 0, "max": 100,
                "wave_1_active": False,
            },
        },
    },
}

# ─── Cluster KPI Baselines ──────────────────────────────────────────────────
# Cluster A (Riyadh 1st): large urban, older/sicker — weaker clinical/efficiency, stronger data
# Cluster B (Eastern): balanced — middle across all categories
# Cluster C (Madinah): younger/healthier — best clinical, weakest data quality/reporting

CLUSTER_KPI_BASELINES = {
    "A": {
        # Clinical Outcomes
        "diabetes_hba1c_control": 62,
        "hypertension_control": 58,
        "readmission_30day": 14,
        "preventable_hospitalisations": 28,
        "cancer_screening_rate": 35,
        "maternal_mortality_rate": 18,
        "childhood_immunisation": 82,
        # Efficiency Improvement
        "avg_length_of_stay": 1.15,
        "cost_efficiency_ratio": 0.94,
        "hospital_to_primary_care_shift": 12,
        "generic_prescribing_rate": 55,
        "theatre_utilisation": 65,
        "outpatient_followup_new_ratio": 2.8,
        # Data Quality
        "icd10_coding_accuracy": 88,
        "claims_submission_completeness": 92,
        "timely_data_submission": 90,
        "duplicate_record_rate": 6,
        # Data Reporting
        "mandatory_report_compliance": 88,
        "dashboard_adoption": 72,
        "population_health_register": 60,
    },
    "B": {
        # Clinical Outcomes
        "diabetes_hba1c_control": 70,
        "hypertension_control": 65,
        "readmission_30day": 11,
        "preventable_hospitalisations": 22,
        "cancer_screening_rate": 42,
        "maternal_mortality_rate": 12,
        "childhood_immunisation": 88,
        # Efficiency Improvement
        "avg_length_of_stay": 1.05,
        "cost_efficiency_ratio": 1.02,
        "hospital_to_primary_care_shift": 18,
        "generic_prescribing_rate": 62,
        "theatre_utilisation": 72,
        "outpatient_followup_new_ratio": 2.2,
        # Data Quality
        "icd10_coding_accuracy": 74,
        "claims_submission_completeness": 82,
        "timely_data_submission": 78,
        "duplicate_record_rate": 8,
        # Data Reporting
        "mandatory_report_compliance": 76,
        "dashboard_adoption": 58,
        "population_health_register": 52,
    },
    "C": {
        # Clinical Outcomes
        "diabetes_hba1c_control": 78,
        "hypertension_control": 72,
        "readmission_30day": 8,
        "preventable_hospitalisations": 15,
        "cancer_screening_rate": 50,
        "maternal_mortality_rate": 8,
        "childhood_immunisation": 92,
        # Efficiency Improvement
        "avg_length_of_stay": 0.95,
        "cost_efficiency_ratio": 0.88,
        "hospital_to_primary_care_shift": 25,
        "generic_prescribing_rate": 70,
        "theatre_utilisation": 80,
        "outpatient_followup_new_ratio": 1.8,
        # Data Quality
        "icd10_coding_accuracy": 68,
        "claims_submission_completeness": 72,
        "timely_data_submission": 70,
        "duplicate_record_rate": 10,
        # Data Reporting
        "mandatory_report_compliance": 72,
        "dashboard_adoption": 48,
        "population_health_register": 42,
    },
}

# Legacy alias — old code referencing PERFORMANCE_BASELINES still works
PERFORMANCE_BASELINES = CLUSTER_KPI_BASELINES

# ─── Incentive Mechanism Defaults ───────────────────────────────────────────
WITHHOLD_PERCENTAGE = 2.0
PERFORMANCE_TARGET = 70
PERFORMANCE_FLOOR = 50

# Quality gates (mapped to new KPI names)
QUALITY_GATE_DIABETES = 65       # diabetes_hba1c_control >= threshold
QUALITY_GATE_READMISSION = 15    # readmission_30day <= threshold
QUALITY_GATE_COMPOSITE = 55      # composite score >= threshold
# Legacy alias
QUALITY_GATE_SATISFACTION = QUALITY_GATE_COMPOSITE

SAVINGS_SPLIT_CNHI = 50
SAVINGS_SPLIT_PROVIDER = 50

# Capability Investment (dual-track system)
CAPABILITY_THRESHOLD = 50
CAPABILITY_INVESTMENT_PER_GAP = 50_000  # SAR per gap point

# Tier thresholds and payout percentages
TIER_THRESHOLDS = [
    (0, 49, 0.0, "No Payout"),
    (50, 64, 0.5, "Tier 1"),
    (65, 79, 1.5, "Tier 2"),
    (80, 100, 3.0, "Tier 3"),
]

# Year 2 Projection defaults
ELASTICITY_FACTOR_DEFAULT = 0.5

# ─── Colour Palette ─────────────────────────────────────────────────────────
COLORS = {
    "navy": "#0A1628",
    "teal": "#2EC4B6",
    "gold": "#C9A84C",
    "red": "#E63946",
    "amber": "#F4A261",
    "light_grey": "#F8F9FA",
    "mid_grey": "#6C757D",
    "white": "#FFFFFF",
    "provider_a": "#E63946",
    "provider_b": "#2EC4B6",
    "provider_c": "#C9A84C",
}

CLUSTER_COLORS = {"A": "#E63946", "B": "#2EC4B6", "C": "#C9A84C"}
PROVIDER_COLORS = CLUSTER_COLORS  # legacy alias
