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

# Chronic disease risk weights
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

# Performance baseline values per provider
PERFORMANCE_BASELINES = {
    "A": {
        "diabetes_control_rate": 68,
        "readmission_rate_30day": 14,
        "patient_satisfaction_score": 71,
        "cost_efficiency_ratio": 0.94,
    },
    "B": {
        "diabetes_control_rate": 72,
        "readmission_rate_30day": 11,
        "patient_satisfaction_score": 76,
        "cost_efficiency_ratio": 1.02,
    },
    "C": {
        "diabetes_control_rate": 78,
        "readmission_rate_30day": 8,
        "patient_satisfaction_score": 82,
        "cost_efficiency_ratio": 0.88,
    },
}

# Incentive mechanism defaults
WITHHOLD_PERCENTAGE = 2.0
PERFORMANCE_TARGET = 70
PERFORMANCE_FLOOR = 50
QUALITY_GATE_DIABETES = 65
QUALITY_GATE_READMISSION = 15
QUALITY_GATE_SATISFACTION = 65
SAVINGS_SPLIT_CNHI = 50
SAVINGS_SPLIT_PROVIDER = 50

# Tier thresholds and payout percentages
TIER_THRESHOLDS = [
    (0, 49, 0.0, "No Payout"),
    (50, 64, 0.5, "Tier 1"),
    (65, 79, 1.5, "Tier 2"),
    (80, 100, 3.0, "Tier 3"),
]

# Colour palette
COLORS = {
    "navy": "#0A1628",
    "teal": "#2EC4B6",
    "gold": "#C9A84C",
    "red": "#E63946",
    "light_grey": "#F8F9FA",
    "mid_grey": "#6C757D",
    "white": "#FFFFFF",
    "provider_a": "#E63946",
    "provider_b": "#2EC4B6",
    "provider_c": "#C9A84C",
}

PROVIDER_COLORS = {"A": "#E63946", "B": "#2EC4B6", "C": "#C9A84C"}
