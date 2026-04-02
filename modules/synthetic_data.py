"""Synthetic patient population generator for CNHI POC."""

import uuid
import numpy as np
import pandas as pd

from config.demographics import (
    AGE_DISTRIBUTION,
    DISEASE_PREVALENCE,
    COMORBIDITY_SECOND_CHANCE,
    COMORBIDITY_THIRD_CHANCE,
    PROVIDER_PROFILES,
    ICD10_CODES,
)
from config.defaults import RANDOM_SEED, TOTAL_PATIENTS


def _sample_ages(n: int, skew: str, rng: np.random.Generator) -> np.ndarray:
    """Sample ages respecting Saudi demographic distribution with provider skew."""
    bands = AGE_DISTRIBUTION  # (min, max, proportion)

    if skew == "older":
        weights = np.array([0.12, 0.22, 0.32, 0.34])
    elif skew == "younger":
        weights = np.array([0.48, 0.40, 0.09, 0.03])
    else:  # balanced
        weights = np.array([b[2] for b in bands])

    weights = weights / weights.sum()
    band_indices = rng.choice(len(bands), size=n, p=weights)

    ages = np.empty(n, dtype=int)
    for i, (lo, hi, _) in enumerate(bands):
        mask = band_indices == i
        count = mask.sum()
        if count > 0:
            ages[mask] = rng.integers(lo, hi + 1, size=count)
    return ages


def _get_prevalence_rate(condition: str, age: int) -> float:
    """Look up base prevalence rate for a condition given patient age."""
    for lo, hi, rate in DISEASE_PREVALENCE[condition]:
        if lo <= age <= hi:
            return rate
    return 0.0


def _assign_diseases(
    ages: np.ndarray,
    sexes: np.ndarray,
    disease_mult: float,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    """Assign chronic disease flags with comorbidity cascade logic."""
    n = len(ages)
    conditions = ["diabetes", "obesity", "cvd", "respiratory", "mental_health"]
    flags = {}

    # Phase 1: independent base rates (adjusted by provider multiplier)
    for cond in conditions:
        probs = np.array([_get_prevalence_rate(cond, a) for a in ages])
        probs = np.clip(probs * disease_mult, 0, 0.95)
        flags[cond] = rng.random(n) < probs

    # Phase 2: comorbidity cascade — if a patient has at least one condition,
    # boost probability of additional conditions
    condition_count = sum(flags[c].astype(int) for c in conditions)

    for cond in conditions:
        # For patients with 1+ other condition who DON'T already have this one
        has_others = (condition_count - flags[cond].astype(int)) >= 1
        eligible = has_others & ~flags[cond]
        if eligible.any():
            boost = rng.random(eligible.sum()) < (COMORBIDITY_SECOND_CHANCE * disease_mult * 0.3)
            flags[cond][eligible] = flags[cond][eligible] | boost

    return flags


def _assign_icd_codes(flags: dict[str, np.ndarray], rng: np.random.Generator) -> list[list[str]]:
    """Assign ICD-10 codes based on disease flags."""
    n = len(next(iter(flags.values())))
    all_codes = []
    condition_map = {
        "diabetes": "diabetes",
        "cvd": "cvd",
        "respiratory": "respiratory",
        "mental_health": "mental_health",
        "obesity": "obesity",
    }

    for i in range(n):
        codes = []
        for flag_name, icd_key in condition_map.items():
            if flags[flag_name][i]:
                pool = ICD10_CODES[icd_key]
                n_codes = min(rng.integers(1, 3), len(pool))
                selected = rng.choice(pool, size=n_codes, replace=False).tolist()
                codes.extend(selected)
        all_codes.append(codes)
    return all_codes


def generate_population(seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate the full synthetic patient population.

    Returns a DataFrame with one row per patient and all required fields.
    """
    rng = np.random.default_rng(seed)

    profiles = PROVIDER_PROFILES
    target_total = TOTAL_PATIENTS
    sizes = {pid: p["target_size"] for pid, p in profiles.items()}

    # Ensure sizes sum to target total
    total = sum(sizes.values())
    if total != target_total:
        sizes["A"] += target_total - total

    all_dfs = []

    for provider_id, profile in profiles.items():
        n = sizes[provider_id]

        ages = _sample_ages(n, profile["age_skew"], rng)
        sexes = rng.choice(["M", "F"], size=n)
        se_proxy = rng.choice(
            ["low", "medium", "high"],
            size=n,
            p=[0.30, 0.45, 0.25],
        )

        disease_flags = _assign_diseases(ages, sexes, profile["disease_multiplier"], rng)

        icd_codes = _assign_icd_codes(disease_flags, rng)

        comorbidity_count = sum(
            disease_flags[c].astype(int) for c in disease_flags
        )

        patient_ids = [str(uuid.uuid4()) for _ in range(n)]

        df = pd.DataFrame({
            "patient_id": patient_ids,
            "age": ages,
            "sex": sexes,
            "provider_id": provider_id,
            "diagnosis_codes": icd_codes,
            "has_diabetes": disease_flags["diabetes"],
            "has_cvd": disease_flags["cvd"],
            "has_respiratory": disease_flags["respiratory"],
            "has_mental_health": disease_flags["mental_health"],
            "has_obesity": disease_flags["obesity"],
            "comorbidity_count": comorbidity_count,
            "socioeconomic_proxy": se_proxy,
        })
        all_dfs.append(df)

    population = pd.concat(all_dfs, ignore_index=True)
    return population
