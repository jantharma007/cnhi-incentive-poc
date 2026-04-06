"""Pre-built scenario definitions for Module 4."""

from __future__ import annotations

from config.defaults import CLUSTER_KPI_BASELINES, KPI_CATEGORIES


def _deep_copy_perf(base: dict) -> dict:
    return {cid: dict(v) for cid, v in base.items()}


def _improve_baselines(pct: float = 0.12) -> dict:
    """Shift all active KPIs toward optimal by pct (10-15%)."""
    result = {}
    for cid, kpis in CLUSTER_KPI_BASELINES.items():
        improved = dict(kpis)
        for cat_def in KPI_CATEGORIES.values():
            for kpi_id, kpi_def in cat_def["kpis"].items():
                if not kpi_def["wave_1_active"]:
                    continue
                val = kpis[kpi_id]
                if kpi_def["direction"] == "higher_better":
                    improved[kpi_id] = val + (kpi_def["max"] - val) * pct
                else:
                    improved[kpi_id] = val - (val - kpi_def["min"]) * pct
                # Round to match original type
                if isinstance(kpis[kpi_id], int):
                    improved[kpi_id] = round(improved[kpi_id])
                else:
                    improved[kpi_id] = round(improved[kpi_id], 2)
        result[cid] = improved
    return result


def _worsen_clinical(pct: float = 0.12) -> dict:
    """Worsen clinical outcomes and efficiency, keep data metrics stable."""
    clinical_kpis = set(KPI_CATEGORIES["clinical_outcomes"]["kpis"].keys())
    efficiency_kpis = set(KPI_CATEGORIES["efficiency_improvement"]["kpis"].keys())
    result = {}
    for cid, kpis in CLUSTER_KPI_BASELINES.items():
        worsened = dict(kpis)
        for kpi_id in clinical_kpis | efficiency_kpis:
            kpi_def = None
            for cat_def in KPI_CATEGORIES.values():
                if kpi_id in cat_def["kpis"]:
                    kpi_def = cat_def["kpis"][kpi_id]
                    break
            if kpi_def is None or not kpi_def["wave_1_active"]:
                continue
            val = kpis[kpi_id]
            if kpi_def["direction"] == "higher_better":
                worsened[kpi_id] = val - (val - kpi_def["min"]) * pct
            else:
                worsened[kpi_id] = val + (kpi_def["max"] - val) * pct
            if isinstance(kpis[kpi_id], int):
                worsened[kpi_id] = round(worsened[kpi_id])
            else:
                worsened[kpi_id] = round(worsened[kpi_id], 2)
        result[cid] = worsened
    return result


SCENARIOS = {
    "Baseline": {
        "description": "Default parameters — no modifications.",
        "kpi_overrides": None,
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "All Clusters Improve": {
        "description": "All KPI metrics improve by 10-15% across all clusters. Tests CNHI fiscal exposure.",
        "kpi_overrides": _improve_baselines(0.12),
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "Gaming Detection": {
        "description": "Cluster C cuts costs aggressively but clinical and data quality decline. Tests quality gates.",
        "kpi_overrides": {
            "A": dict(CLUSTER_KPI_BASELINES["A"]),
            "B": dict(CLUSTER_KPI_BASELINES["B"]),
            "C": {
                **CLUSTER_KPI_BASELINES["C"],
                "diabetes_hba1c_control": 55,
                "hypertension_control": 50,
                "readmission_30day": 12,
                "preventable_hospitalisations": 25,
                "cost_efficiency_ratio": 0.75,
                "icd10_coding_accuracy": 50,
                "claims_submission_completeness": 55,
                "timely_data_submission": 52,
            },
        },
        "risk_multiplier": 1.0,
        "budget_cap": None,
    },
    "Population Risk Increase": {
        "description": "All populations get 15% sicker. RAC payments increase, clinical performance may decline.",
        "kpi_overrides": _worsen_clinical(0.12),
        "risk_multiplier": 1.15,
        "budget_cap": None,
    },
    "Budget Cap": {
        "description": "Total programme cost (incentives + capability investment) capped at SAR 5M.",
        "kpi_overrides": None,
        "risk_multiplier": 1.0,
        "budget_cap": 5_000_000,
    },
}


def apply_scenario(
    scenario_name: str,
    base_perf: dict,
) -> tuple[dict, float, float | None]:
    """Apply a scenario and return (perf_data, risk_multiplier, budget_cap).

    If kpi_overrides is None, uses base_perf unchanged.
    """
    scenario = SCENARIOS[scenario_name]
    overrides = scenario.get("kpi_overrides") or scenario.get("perf_overrides")
    perf = overrides if overrides is not None else _deep_copy_perf(base_perf)
    return perf, scenario["risk_multiplier"], scenario["budget_cap"]
