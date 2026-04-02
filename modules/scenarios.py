"""Pre-built scenario definitions for Module 4."""

from config.defaults import PERFORMANCE_BASELINES


def _deep_copy_perf(base: dict) -> dict:
    return {pid: dict(v) for pid, v in base.items()}


SCENARIOS = {
    "Baseline": {
        "description": "Default parameters as specified — no modifications.",
        "perf_overrides": None,
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "All Providers Improve": {
        "description": "All performance metrics improve by 10-15%. Tests CNHI fiscal exposure when the system works well.",
        "perf_overrides": {
            "A": {"diabetes_control_rate": 80, "readmission_rate_30day": 9, "patient_satisfaction_score": 83, "cost_efficiency_ratio": 0.88},
            "B": {"diabetes_control_rate": 84, "readmission_rate_30day": 7, "patient_satisfaction_score": 88, "cost_efficiency_ratio": 0.92},
            "C": {"diabetes_control_rate": 90, "readmission_rate_30day": 5, "patient_satisfaction_score": 93, "cost_efficiency_ratio": 0.82},
        },
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "Gaming Detection": {
        "description": "Provider C cuts costs aggressively but quality declines. Tests whether quality gates catch gaming behaviour.",
        "perf_overrides": {
            "A": PERFORMANCE_BASELINES["A"],
            "B": PERFORMANCE_BASELINES["B"],
            "C": {"diabetes_control_rate": 55, "readmission_rate_30day": 12, "patient_satisfaction_score": 58, "cost_efficiency_ratio": 0.75},
        },
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "Population Risk Increase": {
        "description": "All provider panels get 15% sicker (risk scores increase). Tests how RAC payments and incentives respond to population health shifts.",
        "perf_overrides": {
            "A": {"diabetes_control_rate": 62, "readmission_rate_30day": 17, "patient_satisfaction_score": 67, "cost_efficiency_ratio": 0.98},
            "B": {"diabetes_control_rate": 66, "readmission_rate_30day": 14, "patient_satisfaction_score": 72, "cost_efficiency_ratio": 1.06},
            "C": {"diabetes_control_rate": 72, "readmission_rate_30day": 11, "patient_satisfaction_score": 78, "cost_efficiency_ratio": 0.93},
        },
        "risk_multiplier": 1.15,
        "budget_cap": None,
    },
    "Budget Cap": {
        "description": "Total incentive payout capped at SAR 5M. If incentives exceed this, all are proportionally reduced.",
        "perf_overrides": None,
        "risk_multiplier": 1.0,
        "budget_cap": 5_000_000,
    },
}


def apply_scenario(
    scenario_name: str,
    base_perf: dict,
) -> tuple[dict, float, float | None]:
    """Apply a scenario and return (perf_data, risk_multiplier, budget_cap).

    If perf_overrides is None, uses base_perf unchanged.
    """
    scenario = SCENARIOS[scenario_name]
    perf = scenario["perf_overrides"] if scenario["perf_overrides"] is not None else _deep_copy_perf(base_perf)
    return perf, scenario["risk_multiplier"], scenario["budget_cap"]
