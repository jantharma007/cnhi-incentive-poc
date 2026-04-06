"""Saudi demographic profiles and disease prevalence rates."""

# Age distribution reflecting Saudi young-skew demographics
# Format: (min_age, max_age, proportion)
AGE_DISTRIBUTION = [
    (0, 14, 0.25),     # 25% under 15
    (15, 39, 0.35),    # 35% aged 15-39
    (40, 59, 0.25),    # 25% aged 40-59
    (60, 95, 0.15),    # 15% aged 60+
]

# Disease prevalence rates by condition
# Each entry: condition -> list of (age_min, age_max, base_rate)
DISEASE_PREVALENCE = {
    "diabetes": [
        (0, 29, 0.02),
        (30, 120, 0.18),
    ],
    "obesity": [
        (0, 17, 0.15),
        (18, 120, 0.40),
    ],
    "cvd": [
        (0, 29, 0.01),
        (30, 49, 0.08),
        (50, 120, 0.25),
    ],
    "respiratory": [
        (0, 120, 0.12),
    ],
    "mental_health": [
        (0, 120, 0.15),
    ],
}

# Comorbidity cascade probabilities
COMORBIDITY_SECOND_CHANCE = 0.40  # 40% chance of a second condition given one
COMORBIDITY_THIRD_CHANCE = 0.15   # 15% chance of a third given two

# Health cluster profiles (ACO-style networks serving geographically defined populations)
CLUSTER_PROFILES = {
    "A": {
        "name": "Riyadh First Health Cluster",
        "type": "public",
        "description": "Large urban cluster serving older, higher-acuity population. Hub: King Saud Medical City.",
        "target_size": 20_000,
        "age_skew": "older",
        "disease_multiplier": 1.55,
        "target_avg_risk": 1.35,
    },
    "B": {
        "name": "Eastern Health Cluster",
        "type": "public",
        "description": "Mixed urban-suburban cluster with balanced population demographics. Hub: Dammam Medical Complex.",
        "target_size": 18_000,
        "age_skew": "balanced",
        "disease_multiplier": 0.95,
        "target_avg_risk": 1.00,
    },
    "C": {
        "name": "Madinah Health Cluster",
        "type": "public",
        "description": "Mid-sized cluster serving younger population with seasonal Hajj/Umrah demand. Hub: King Fahad Hospital Madinah.",
        "target_size": 12_000,
        "age_skew": "younger",
        "disease_multiplier": 0.50,
        "target_avg_risk": 0.72,
    },
}

# Legacy alias — removed after full migration
PROVIDER_PROFILES = CLUSTER_PROFILES

# ICD-10 code pools per condition (representative subset)
ICD10_CODES = {
    "diabetes": ["E11.9", "E11.65", "E11.22", "E11.40", "E13.9"],
    "cvd": ["I10", "I25.10", "I50.9", "I48.91", "I63.9"],
    "respiratory": ["J45.20", "J44.1", "J18.9", "J06.9"],
    "mental_health": ["F32.1", "F41.1", "F43.10", "F31.9"],
    "obesity": ["E66.01", "E66.09", "E66.9"],
}
